from __future__ import annotations

import html
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.datasets import load_code_dataset
from src.experiments.paths import safe_path_part
from src.experiments.statistics import matthews_correlation_coefficient, spearman
from src.methods.llm_prompt import LLM_READABILITY_PROMPT_TEMPLATE
from src.methods.posnett.method import JAVA_KEYWORDS, JAVA_OPERATORS, TOKEN_PATTERN, strip_comments
from src.methods.rmc.prompts import (
    CODE_MASK_JSON_PROMPT_TEMPLATE,
    GENERALIST_NEGATIVE_3SHOT_VARIANT,
    GENERALIST_POSITIVE_3SHOT_VARIANT,
    build_recovery_prompt,
)
from src.methods.rmc.scoring import (
    AGGREGATION_LABEL as RMC_AGGREGATION_LABEL,
    DEFAULT_CONTROL_CAPACITY as RMC_DEFAULT_CONTROL_CAPACITY,
    DEFAULT_ERROR_PENALTY as RMC_DEFAULT_ERROR_PENALTY,
    EXCEPTION_CONTROL_CAPACITY as RMC_EXCEPTION_CONTROL_CAPACITY,
    EXCEPTION_ERROR_PENALTY as RMC_EXCEPTION_ERROR_PENALTY,
    METHOD_BODY_CAPACITY as RMC_METHOD_BODY_CAPACITY,
    METHOD_BODY_ERROR_PENALTY as RMC_METHOD_BODY_ERROR_PENALTY,
    MASK_PROPORTION_WEIGHT as RMC_MASK_PROPORTION_WEIGHT,
    MIN_CONTROL_DENSITY as RMC_MIN_CONTROL_DENSITY,
    MIN_CONTROL_DENSITY_LOC as RMC_MIN_CONTROL_DENSITY_LOC,
    SPARSE_CONTROL_PENALTY as RMC_SPARSE_CONTROL_PENALTY,
    count_source_tokens as rmc_source_token_count,
    score_task_result,
)
from src.site.labels import (
    DATASET_ORDER,
    METHOD_ORDER,
    dataset_label,
    dataset_rank,
    method_label,
    method_rank,
    short_model_label,
)


ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = ROOT / "results" / "methods"
DOCS_DIR = ROOT / "docs"
RMC_METHODS = {"rmc", "rmc_generalist_negative", "rmc_generalist_positive"}
SHOW_RMC_HISTORY_RUNS = False
RMC_HISTORY_RUNS: dict[str, Path] = {}

_TASK_RESULT_CACHE: dict[tuple[Path, str], dict[str, Any] | None] = {}
_RUN_SCORE_CACHE: dict[str, dict[str, float | None]] = {}
_DATASET_TOTAL_CACHE: dict[str, int | None] = {}
COGNASCORE_ML_METHODS = {
    "cognascore_ml_consensus24",
}
HIDDEN_METHODS: set[str] = set()
HIDDEN_DATASETS: set[str] = set()


@dataclass(frozen=True)
class Run:
    method: str
    dataset: str
    model: str | None
    summary_path: Path
    data: dict[str, Any]

    @property
    def label(self) -> str:
        if is_rmc_method(self.method):
            return f"{run_group_label(self.method, self.model)} on {dataset_label(self.dataset)}"
        if self.method in COGNASCORE_ML_METHODS or self.method == "cognascore_compact":
            return f"{method_label(self.method)} on {dataset_label(self.dataset)}"
        model = f" · {short_model_label(self.model)}" if self.model else ""
        return f"{method_label(self.method)} on {dataset_label(self.dataset)}{model}"

    @property
    def slug(self) -> str:
        parts = [self.method, self.dataset]
        if self.model:
            parts.append(self.model)
        return "__".join(slugify(part) for part in parts)

    @property
    def metric_name(self) -> str:
        if self.data.get("mcc") is not None:
            return "MCC"
        if self.data.get("spearman") is not None:
            return "Spearman"
        inferred = self.inferred_metric()
        if inferred[0] is not None:
            return inferred[0]
        return str(self.data.get("evaluation_metric") or "Score")

    @property
    def metric_value(self) -> float | None:
        value = self.data.get("mcc")
        if value is None:
            value = self.data.get("spearman")
        if value is None:
            value = self.inferred_metric()[1]
        return as_float(value)

    @property
    def count(self) -> int | None:
        return self.data.get("valid_count") or len(self.valid_rows()) or self.data.get("count")

    def valid_rows(self) -> list[dict[str, Any]]:
        rows = []
        for row in self.data.get("results", []):
            task_id = row.get("task_id")
            score = display_score_for_row(self, row)
            human = row.get("readability_score")
            if task_id is not None and as_float(score) is not None and as_float(human) is not None:
                updated = dict(row)
                updated["score"] = score
                rows.append(updated)
        return rows

    def inferred_metric(self) -> tuple[str | None, float | None]:
        rows = self.valid_rows()
        if len(rows) < 2:
            return None, None
        scores = [float(row.get("score", row.get("rmc_score"))) for row in rows]
        human = [float(row["readability_score"]) for row in rows]
        if all(value in {0.0, 1.0} for value in human):
            return "MCC", best_mcc(scores, [int(value) for value in human])
        return "Spearman", spearman(scores, human)


def main() -> None:
    runs = discover_runs()
    reset_docs()
    write_assets()
    write_index(runs)
    write_dataset_pages(runs)
    write_method_pages(runs)
    write_run_pages(runs)
    print(f"Wrote {DOCS_DIR.relative_to(ROOT)} with {len(runs)} runs")


def discover_runs() -> list[Run]:
    runs = []
    for path in sorted(RESULTS_DIR.glob("**/summary.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            continue
        if data.get("mock_recover") is True:
            continue
        rel = path.relative_to(RESULTS_DIR)
        parts = rel.parts
        if len(parts) < 3:
            continue
        if parts[0] == "history":
            continue
        method = parts[0]
        if method in HIDDEN_METHODS:
            continue
        if is_rmc_method(method):
            continue
        if method not in METHOD_ORDER:
            continue
        dataset = parts[1]
        if dataset in HIDDEN_DATASETS:
            continue
        model = infer_model(method, parts, data)
        if method == "cognascore_compact" and model != "Qwen/Qwen3-Embedding-0.6B":
            continue
        runs.append(Run(method=method, dataset=dataset, model=model, summary_path=path, data=data))
    if SHOW_RMC_HISTORY_RUNS:
        for method, history_root in RMC_HISTORY_RUNS.items():
            for path in sorted(history_root.glob("*/gpt41-nano/summary.json")):
                data = json.loads(path.read_text(encoding="utf-8"))
                dataset = path.parent.parent.name
                runs.append(
                    Run(
                        method=method,
                        dataset=dataset,
                        model=str(data.get("model") or "gpt41-nano"),
                        summary_path=path,
                        data=data,
                    )
                )
    return sorted(runs, key=lambda run: (method_rank(run.method), dataset_rank(run.dataset), run.model or ""))


def infer_model(method: str, parts: tuple[str, ...], data: dict[str, Any]) -> str | None:
    if method in {"posnett", "scalabrino"}:
        return None
    value = data.get("model")
    if value:
        model = str(value)
        if method in COGNASCORE_ML_METHODS and model == "nomic-ai-nomic-embed-text-v1.5":
            return "nomic-ai/nomic-embed-text-v1.5"
        return model
    if len(parts) >= 4:
        return parts[2]
    return None


def is_rmc_method(method: str) -> bool:
    return method in RMC_METHODS


def reset_docs() -> None:
    if DOCS_DIR.exists():
        shutil.rmtree(DOCS_DIR)
    (DOCS_DIR / "assets").mkdir(parents=True)
    (DOCS_DIR / "datasets").mkdir()
    (DOCS_DIR / "methods").mkdir()
    (DOCS_DIR / "runs").mkdir()
    (DOCS_DIR / "samples").mkdir()


def write_assets() -> None:
    (DOCS_DIR / "assets" / "style.css").write_text(STYLE_CSS, encoding="utf-8")
    (DOCS_DIR / "assets" / "app.js").write_text(APP_JS, encoding="utf-8")


def write_index(runs: list[Run]) -> None:
    datasets = sorted({run.dataset for run in runs}, key=dataset_rank)
    run_groups = sorted({run_group_key(run) for run in runs}, key=run_group_rank)
    best_runs = best_runs_by_dataset(runs)
    by_cell: dict[tuple[tuple[str, str | None], str], list[Run]] = {}
    for run in runs:
        by_cell.setdefault((run_group_key(run), run.dataset), []).append(run)

    header = "".join(
        f'<th><a href="datasets/{slugify(dataset)}.html">{escape(dataset_label(dataset))}</a></th>'
        for dataset in datasets
    )
    controls = []
    rows = []
    for group in run_groups:
        method, model = group
        group_id = slugify("__".join(part for part in (method, model) if part))
        label = run_group_label(method, model)
        controls.append(
            f'<button class="method-filter active" type="button" draggable="true" data-method-group="{escape(group_id)}" '
            f'aria-pressed="true">{escape(label)}</button>'
        )
        cells = []
        for dataset in datasets:
            cell_runs = by_cell.get((group, dataset), [])
            cells.append(f"<td>{render_run_cell(cell_runs, best_runs)}</td>")
        rows.append(
            f'<tr data-method-group="{escape(group_id)}">'
            f'<th><a href="methods/{slugify(method)}.html">{escape(label)}</a></th>'
            + "".join(cells)
            + "</tr>"
        )
    body = f"""
    <section class="panel">
      <div class="panel-head">
        <div>
          <p class="eyebrow">Result matrix</p>
          <h1>Code Readability Results</h1>
        </div>
      </div>
      <div class="method-filters" data-method-filters>
        {''.join(controls)}
      </div>
      <div class="matrix-wrap">
        <table class="matrix" data-result-matrix>
          <thead><tr><th>Method / Dataset</th>{header}</tr></thead>
          <tbody>{''.join(rows)}</tbody>
        </table>
      </div>
    </section>
    """
    write_page(DOCS_DIR / "index.html", "Code Readability Results", body, current="Results")


def best_runs_by_dataset(runs: list[Run]) -> set[str]:
    best: dict[str, tuple[float, str]] = {}
    for run in runs:
        value = run.metric_value
        if value is None:
            continue
        current = best.get(run.dataset)
        candidate = (float(value), run.slug)
        if current is None or candidate[0] > current[0]:
            best[run.dataset] = candidate
    return {slug for _, slug in best.values()}


def render_run_cell(runs: list[Run], best_runs: set[str]) -> str:
    if not runs:
        return '<span class="missing">Not run</span>'
    links = []
    for run in runs:
        value = format_metric(run.metric_value)
        coverage = format_coverage(run)
        class_name = "result-link best" if run.slug in best_runs else "result-link"
        score = run.metric_value
        score_attr = "" if score is None else f' data-score="{float(score)}"'
        links.append(
            f'<a class="{class_name}" href="runs/{run.slug}.html" data-dataset="{escape(run.dataset)}"{score_attr}>'
            f"<strong>{escape(value)}</strong>"
            f"<span>{escape(run.metric_name)}</span>"
            f'<small>{escape(coverage)}</small>'
            "</a>"
        )
    return "".join(links)


def format_coverage(run: Run) -> str:
    valid = run.count
    total = dataset_total(run)
    if valid is None and total is None:
        return "valid n/a"
    if total is None:
        return f"{valid}/?"
    if valid is None:
        return f"?/{total}"
    return f"{valid}/{total}"


def dataset_total(run: Run) -> int | None:
    if run.dataset in _DATASET_TOTAL_CACHE:
        return _DATASET_TOTAL_CACHE[run.dataset]
    items = load_dataset_items([run])
    total = len(items) if items else as_int(run.data.get("count"))
    _DATASET_TOTAL_CACHE[run.dataset] = total
    return total


def write_dataset_pages(runs: list[Run]) -> None:
    for dataset in sorted({run.dataset for run in runs}, key=dataset_rank):
        dataset_runs = [run for run in runs if run.dataset == dataset]
        run_rows = "".join(run_row(run, prefix="../") for run in dataset_runs)
        items = load_dataset_items(dataset_runs)
        write_sample_pages(dataset, items, dataset_runs)
        sample_rows = "".join(
            dataset_sample_row(dataset, index, item, dataset_runs)
            for index, item in enumerate(items, start=1)
        )
        score_headers = "".join(
            sortable_header(short_run_label(run), run_sort_key(run))
            for run in dataset_runs
        )
        human_label = dataset_human_label(dataset_runs)
        body = f"""
        <section class="panel">
          <p class="eyebrow">Dataset</p>
          <h1>{escape(dataset_label(dataset))}</h1>
          {dataset_description(dataset, items)}
        </section>
        <section class="panel">
          <h2>Runs</h2>
          <table class="records">
            <thead><tr><th>Method</th><th>Model</th><th>Metric</th><th>Count</th></tr></thead>
            <tbody>{run_rows}</tbody>
          </table>
        </section>
        <section class="panel">
          <div class="panel-head compact">
            <div>
              <h2>Samples</h2>
              <p class="muted">Click a sample ID to inspect code on its own page. Method columns are only shown when that method has results for this dataset.</p>
            </div>
          </div>
          <table class="records sample-table" data-sortable-samples>
            <thead><tr>{sortable_header("ID", "order", "asc")}{sortable_header(human_label, "human", "desc")}{score_headers}{sortable_header("LOC", "code-lines", "desc")}</tr></thead>
            <tbody>{sample_rows}</tbody>
          </table>
        </section>
        """
        write_page(DOCS_DIR / "datasets" / f"{slugify(dataset)}.html", dataset_label(dataset), body, prefix="../")


def write_method_pages(runs: list[Run]) -> None:
    for method in sorted({run.method for run in runs}, key=method_rank):
        method_runs = [run for run in runs if run.method == method]
        rows = "".join(method_run_row(run, prefix="../") for run in method_runs)
        description = method_description(method)
        body = f"""
        <section class="panel">
          <p class="eyebrow">Method</p>
          <h1>{escape(method_label(method))}</h1>
          {description}
        </section>
        <section class="panel">
          <h2>Runs</h2>
          <table class="records">
            <thead><tr><th>Dataset</th><th>Model</th><th>Metric</th><th>Count</th></tr></thead>
            <tbody>{rows}</tbody>
          </table>
        </section>
        """
        write_page(DOCS_DIR / "methods" / f"{slugify(method)}.html", method_label(method), body, prefix="../")


def method_description(method: str) -> str:
    if is_rmc_method(method):
        developer_message, user_prompt = rmc_prompt_for_method(method)
        return f"""
          <p class="muted">RMC asks the LLM to return a keyed JSON object such as <code>{{"mask_1": "..."}}</code>, then compares each recovered mask directly with the hidden code.</p>
          <p class="muted">Key parameters: model is shown in the run table, granularity = control, aggregation = <strong>{escape(RMC_AGGREGATION_LABEL)}</strong>, similarity = sequence similarity over exact mask contents.</p>
          <p class="formula">RMC = 1 - sum(error penalty * (1 - similarity)) / sum(capacity)</p>
          <p class="formula">method body: capacity = {RMC_METHOD_BODY_CAPACITY}, penalty = {RMC_METHOD_BODY_ERROR_PENALTY}; try/catch/finally: capacity = {RMC_EXCEPTION_CONTROL_CAPACITY}, penalty = {RMC_EXCEPTION_ERROR_PENALTY}; other controls: capacity = {RMC_DEFAULT_CONTROL_CAPACITY}, penalty = {RMC_DEFAULT_ERROR_PENALTY}</p>
          <p class="formula">for mask proportion r = mask tokens / source tokens, capacity and penalty are both multiplied by {RMC_MASK_PROPORTION_WEIGHT}</p>
          <p class="formula">if LOC &gt;= {RMC_MIN_CONTROL_DENSITY_LOC} and control_count / LOC &lt; {RMC_MIN_CONTROL_DENSITY}: score = max(0, score - {RMC_SPARSE_CONTROL_PENALTY})</p>
          <h2>Developer / System Message</h2>
          <pre class="code-block"><code>{escape(developer_message or "None")}</code></pre>
          <h2>User Prompt</h2>
          <pre class="code-block"><code>{escape(user_prompt)}</code></pre>
        """
    if method in COGNASCORE_ML_METHODS:
        training_note = (
            "This Consensus-24 ML route first ranks features independently under five "
            "embedding models, then retains a compact consensus set whose feature names "
            "are stable across embedding spaces. After the feature set is fixed, the final "
            "readability score is fitted with Ridge regression using the Nomic feature "
            "instantiation. The selected 24 features are evaluated on MBJP, Buse, Dorn, "
            "Scalabrino, Schnappinger, and JetBrains."
        )
        return f"""
          <p class="muted wide">CognaScore ML is motivated by a cognitive view of code readability: a reader does not process code as a flat token stream, but maintains short-lived semantic chunks in working memory while tracking visual density, local irregularity, and relationships among related program elements. We therefore build an initial feature library from code layout, cognitive chunks, chunk types, embedding-space geometry, and automatic clustering over embedded chunks. The supervised model is used to test whether this feature space contains predictive readability signal.</p>
          <figure class="feature-diagram">
            <figcaption>
              <span>Feature engineering view before selection</span>
              <small>Left: conventional readability controls. Right: CognaScore features derived from cognitive chunks and embedding-space structure.</small>
            </figcaption>
            <div class="feature-diagram-flow">
              <section class="feature-column traditional-column">
                <div class="column-title">Traditional controls</div>
                <div class="feature-box">
                  <h3>Code size and lexical statistics</h3>
                  <p>Code-scale and token-distribution controls.</p>
                  <div class="feature-tags">
                    <code>loc</code><code>vocabulary_size</code><code>token_count</code><code>halstead_volume</code><code>byte_entropy</code>
                  </div>
                </div>
                <div class="feature-box">
                  <h3>Visual layout and surface density</h3>
                  <p>What the reader sees on screen.</p>
                  <div class="feature-tags">
                    <code>max_line_length</code><code>max_indent</code><code>blank_line_ratio</code><code>visual_operator_density</code><code>visual_identifier_area_ratio</code>
                  </div>
                </div>
              </section>
              <section class="source-column" aria-label="source-code-to-cognitive-chunks">
                <div class="source-card">
                  <span>Source code</span>
                  <pre><code>for item in data:
    score += weight(item)
if score &gt; limit:
    return score</code></pre>
                </div>
                <div class="flow-arrow">→</div>
                <div class="chunk-card">
                  <span>Cognitive chunks</span>
                  <div><code>control</code><code>call</code><code>identifier</code><code>literal</code></div>
                </div>
              </section>
              <section class="feature-column cognascore-column">
                <div class="column-title">CognaScore feature library</div>
                <div class="cognascore-grid">
                  <div class="feature-box embedding-box">
                    <h3>Cognitive chunk inventory</h3>
                    <p>Chunk count, coverage, and local unevenness.</p>
                    <div class="feature-tags embedding-tags">
                      <code>semantic_chunk_count</code><code>std_chunks_per_source_line</code><code>chunk_chars_cv</code><code>chunk_line_span_ratio</code>
                    </div>
                  </div>
                  <div class="feature-box embedding-box">
                    <h3>Type-aware chunk families</h3>
                    <p>Chunk statistics split by cognitive role.</p>
                    <div class="feature-tags embedding-tags">
                      <code>type_identifier_count</code><code>type_call_count</code><code>type_control_flow_count</code><code>type_logical_count</code>
                    </div>
                  </div>
                  <div class="feature-box embedding-box">
                    <h3>Embedding-space geometry</h3>
                    <p>Semantic concentration versus dispersion.</p>
                    <div class="feature-tags embedding-tags">
                      <code>embedding_mean_cosine_to_centroid</code><code>embedding_pairwise_cosine_std</code><code>embedding_effective_rank</code><code>embedding_first_pc_explained_variance</code>
                    </div>
                  </div>
                  <div class="feature-box cluster-box">
                    <h3>Automatic clustering</h3>
                    <p>Adaptive grouping over embedded chunks.</p>
                    <div class="feature-tags cluster-tags">
                      <code>hdbscan_noise_ratio</code><code>optics_reachability_mean</code><code>auto_kmeans_selected_k</code><code>auto_agglo_cluster_count</code>
                    </div>
                  </div>
                  <div class="feature-box embedding-box wide-box">
                    <h3>Chunk-view variants</h3>
                    <p>Recomputed over selected views to isolate cognitive channels.</p>
                    <div class="feature-tags embedding-tags">
                      <code>all</code><code>only_identifier</code><code>semantic_core</code><code>structural_core</code>
                    </div>
                  </div>
                </div>
              </section>
            </div>
          </figure>
          <p class="muted wide">The initial ML feature table contains code-scale, visual-layout, chunk-inventory, identifier-quality, type-aware chunk, compression, embedding-geometry, semantic-context, and adaptive-clustering features. The stable schema contains 111 base features plus 108 embedding-derived features for each model. Feature selection is performed as a cross-embedding consensus: L1 logistic stability screening is run separately under Nomic, Jina Code, Qwen3, Snowflake Arctic, and Voyage Nano; canonical feature names are aggregated and redundant candidates are filtered. The final score is a Ridge model over the fixed consensus feature set. {escape(training_note)}</p>
          <section class="method-note">
            <h2>Final Consensus-24 feature set</h2>
            <p class="muted wide">The final ML model uses 24 selected features: 19 base/CognaScore features, 4 embedding-derived features, and 1 compression feature. Each feature below is instantiated with the Nomic feature table for the final Ridge model.</p>
            <table class="records compact-feature-table">
              <thead><tr><th>Feature</th><th>One-sentence interpretation</th></tr></thead>
              <tbody>
                <tr><td><code>base__visual_operator_density</code></td><td>Measures how densely operator symbols occupy the visible code area, capturing local symbolic load.</td></tr>
                <tr><td><code>base__byte_entropy</code></td><td>Measures character-level textual entropy, used as a broad proxy for lexical irregularity.</td></tr>
                <tr><td><code>base__blank_line_ratio</code></td><td>Measures the fraction of empty lines, capturing visual separation and spacing in the snippet.</td></tr>
                <tr><td><code>base__chunk_y_std</code></td><td>Measures vertical dispersion of extracted cognitive chunks across the code layout.</td></tr>
                <tr><td><code>base__visual_identifier_area_ratio</code></td><td>Measures how much visible code area is occupied by identifiers rather than other token classes.</td></tr>
                <tr><td><code>base__type_literal_ratio</code></td><td>Measures the fraction of chunks classified as literal constants.</td></tr>
                <tr><td><code>base__visual_period_y_mean</code></td><td>Measures the average vertical position of period/dot tokens, which often mark member access or qualified names.</td></tr>
                <tr><td><code>embedding__structural_core__auto_kmeans_selected_k</code></td><td>Measures the automatically selected number of semantic clusters among structural-core chunks.</td></tr>
                <tr><td><code>base__max_line_length</code></td><td>Measures the longest source line, capturing the worst-case horizontal reading span.</td></tr>
                <tr><td><code>embedding__only_identifier__embedding_first_pc_explained_variance</code></td><td>Measures whether identifier embeddings collapse along one dominant semantic direction.</td></tr>
                <tr><td><code>base__chunk_chars_cv</code></td><td>Measures coefficient of variation in chunk character lengths, capturing uneven chunk size.</td></tr>
                <tr><td><code>base__type_unused_import_count</code></td><td>Counts imports detected as unused, acting as a sparse signal of dead or distracting dependencies.</td></tr>
                <tr><td><code>base__type_regex_ratio</code></td><td>Measures the fraction of chunks associated with regular-expression content.</td></tr>
                <tr><td><code>base__visual_keyword_area_ratio</code></td><td>Measures how much visible area is occupied by language keywords.</td></tr>
                <tr><td><code>base__std_indent</code></td><td>Measures dispersion of indentation depth across lines.</td></tr>
                <tr><td><code>base__type_bitwise_ratio</code></td><td>Measures the fraction of chunks involving bitwise operations or masks.</td></tr>
                <tr><td><code>embedding__structural_core__optics_cluster_type_entropy_mean</code></td><td>Measures average chunk-type entropy inside OPTICS clusters over structural-core embeddings.</td></tr>
                <tr><td><code>base__indent_transition_mean</code></td><td>Measures average line-to-line indentation change, capturing control-structure movement in the visual layout.</td></tr>
                <tr><td><code>base__identifier_single_letter_ratio</code></td><td>Measures the fraction of identifiers that are single-letter names.</td></tr>
                <tr><td><code>base__log_max_chunk_chars</code></td><td>Log-transforms the largest chunk length, capturing the largest local cognitive unit while reducing scale dominance.</td></tr>
                <tr><td><code>embedding__structural_core__optics_noise_ratio</code></td><td>Measures the fraction of structural-core chunks treated as noise by adaptive OPTICS clustering.</td></tr>
                <tr><td><code>base__identifier_length_cv</code></td><td>Measures variability in identifier length, capturing inconsistency in naming scale.</td></tr>
                <tr><td><code>compression__zlib_line_ratio_std</code></td><td>Measures the line-to-line variability of zlib compression ratio, capturing uneven repetition or regularity across source lines.</td></tr>
                <tr><td><code>base__long_line_ratio_100</code></td><td>Measures the fraction of source lines longer than 100 characters, capturing extreme horizontal reading burden.</td></tr>
              </tbody>
            </table>
            <h3>Collinearity and sparsity</h3>
            <p class="muted wide">The final 24 features are not strongly redundant: no pair has Pearson or Spearman correlation above 0.9, and only two pairs exceed 0.8. The main overlap is expected: short-identifier ratio and single-letter identifier ratio both measure short-name behavior. Overall sparsity is moderate, although a few rare-pattern features such as regex, bitwise operations, and unused imports are active only in a small subset of samples.</p>
          </section>
        """
    if method == "cognascore_compact":
        return """
          <p class="muted">CognaScore Compact is the interpretable route. It keeps the model linear after simple monotonic transformations and uses four features that represent visible density, code scale, local chunk irregularity, and semantic dispersion among identifier chunks.</p>
          <p class="formula">score = 1.43341466 - 0.30461071 * log1p(visual_operator_density) - 0.227365225 * sqrt(log_LOC) - 0.0463927146 * log1p(std_chunks_per_source_line) - 0.196472171 * log1p(qwen_only_identifier_auto_kmeans_cluster_diameter_max)</p>
          <p class="formula">training: Ridge(alpha = 30), target = per-dataset rank-percentile readability, training datasets = Scalabrino + Schnappinger + Dorn + Buse.</p>
          <table class="records compact-feature-table">
            <thead><tr><th>Feature</th><th>Interpretation</th></tr></thead>
            <tbody>
              <tr><td><code>visual_operator_density</code></td><td>Operator characters per visible code area. Higher density means the reader sees more symbolic operations in a small visual region.</td></tr>
              <tr><td><code>log_LOC</code></td><td>Log-transformed non-empty lines of code. It controls for code scale while reducing the dominance of very long snippets.</td></tr>
              <tr><td><code>std_chunks_per_source_line</code></td><td>Line-level unevenness of CognaScore chunks. Larger values indicate that cognitive chunks are concentrated irregularly across lines.</td></tr>
              <tr><td><code>qwen_only_identifier_auto_kmeans_cluster_diameter_max</code></td><td>Maximum semantic diameter among automatically selected K-means clusters over identifier chunks. Larger values indicate more dispersed naming concepts within the same identifier view.</td></tr>
            </tbody>
          </table>
          <p class="muted">The formula follows a single principle: readable code should be visually sparse, moderate in scale, locally even, and semantically concentrated. All four learned coefficients are negative, so increases in these burden signals lower the predicted readability score. This entry prioritizes a small, defensible formula; it is strongest on Buse, Schnappinger, Dorn, and JetBrains, while Scalabrino is better handled by the high-feature ML route.</p>
        """
    if method == "loc_baseline":
        return """
          <p class="muted">A length-only control. It predicts that shorter snippets are more readable and uses no syntax, token, chunk, embedding, or supervised feature information.</p>
          <p class="formula">score = LOC</p>
          <p class="formula">LOC is the number of non-empty source lines. Lower score means predicted more readable, so continuous Spearman correlations are expected to be negative.</p>
        """
    if method == "posnett":
        return """
          <p class="muted">Our implementation of the Posnett logistic readability model using Java tokens, Halstead volume, LOC, and byte entropy.</p>
          <p class="formula">readability = 1 / (1 + exp(-z)), z = 8.87 - 0.033 * V + 0.40 * LOC - 1.5 * H</p>
        """
    if method == "scalabrino":
        return """
          <p class="muted">The original Scalabrino model, run through the released Java tool and classifier.</p>
          <p class="muted">It is a traditional feature-based model over structural, visual, and textual code metrics; no tuned hyperparameters are set in our runner.</p>
        """
    if method in {"llm", "llm_prompt"}:
        prompt = LLM_READABILITY_PROMPT_TEMPLATE.format(code="{code}")
        return f"""
          <p class="muted">Our direct LLM scoring baseline: the model reads the source text and returns a readability score on a 0-20 scale.</p>
          <p class="muted">Key parameter: model is shown in the run table.</p>
          <h2>Prompt</h2>
          <pre class="code-block"><code>{escape(prompt)}</code></pre>
        """
    return '<p class="muted">Method implementation details are not available for this method yet.</p>'


def rmc_prompt_for_method(method: str) -> tuple[str | None, str]:
    masked_code = "{masked_code}"
    variants = {
        "rmc_generalist_negative": GENERALIST_NEGATIVE_3SHOT_VARIANT,
        "rmc_generalist_positive": GENERALIST_POSITIVE_3SHOT_VARIANT,
    }
    variant = variants.get(method)
    if variant is None:
        return None, CODE_MASK_JSON_PROMPT_TEMPLATE.format(masked_text=masked_code)
    return None, build_recovery_prompt(masked_code, variant=variant)


def dataset_description(dataset: str, items) -> str:
    if not items:
        return '<p class="muted">Dataset statistics are unavailable because the dataset adapter could not load the source files.</p>'
    stats = dataset_stats(items)
    language = stats["language"]
    lines = stats["lines"]
    chars = stats["chars"]
    labels = stats["labels"]
    cards = [
        stat("Samples", str(stats["count"])),
        stat("Languages", language_summary(language)),
        stat("Avg LOC", format_stat_number(lines["mean"])),
        stat("Median LOC", format_stat_number(lines["median"])),
        stat("Avg Chars", format_stat_number(chars["mean"])),
        stat("Label Range", label_range(labels)),
    ]
    language_rows = "".join(
        f"<tr><td>{escape(str(name))}</td><td>{count}</td><td>{count / stats['count']:.1%}</td></tr>"
        for name, count in sorted(language.items(), key=lambda item: (-item[1], str(item[0])))
    )
    note = dataset_note(dataset)
    return f"""
      <p class="muted">{escape(note)}</p>
      <div class="stats dataset-stats">{''.join(cards)}</div>
      <table class="records compact-records">
        <thead><tr><th>Language</th><th>Samples</th><th>Share</th></tr></thead>
        <tbody>{language_rows}</tbody>
      </table>
    """


def dataset_stats(items) -> dict[str, Any]:
    line_counts = [len(item.content.splitlines()) for item in items]
    char_counts = [len(item.content) for item in items]
    labels = [item.readability_score for item in items if item.readability_score is not None]
    language_counts: dict[str, int] = {}
    for item in items:
        language = item.metadata.get("language") or infer_item_language(item)
        language_counts[str(language)] = language_counts.get(str(language), 0) + 1
    return {
        "count": len(items),
        "language": language_counts,
        "lines": numeric_summary(line_counts),
        "chars": numeric_summary(char_counts),
        "labels": labels,
    }


def numeric_summary(values: list[int | float]) -> dict[str, float]:
    if not values:
        return {"mean": 0.0, "median": 0.0}
    ordered = sorted(float(value) for value in values)
    mid = len(ordered) // 2
    median = ordered[mid] if len(ordered) % 2 else (ordered[mid - 1] + ordered[mid]) / 2
    return {"mean": sum(ordered) / len(ordered), "median": median}


def infer_item_language(item) -> str:
    task_id = str(item.task_id).lower()
    if "/python/" in task_id:
        return "python"
    if "/cuda/" in task_id:
        return "cuda"
    if "/java/" in task_id:
        return "java"
    return "java"


def language_summary(language_counts: dict[str, int]) -> str:
    if not language_counts:
        return "n/a"
    ordered = sorted(language_counts.items(), key=lambda item: (-item[1], item[0]))
    if len(ordered) == 1:
        name, count = ordered[0]
        return f"{name} ({count})"
    return ", ".join(f"{name} {count}" for name, count in ordered[:3])


def label_range(labels: list[float]) -> str:
    if not labels:
        return "n/a"
    return f"{min(labels):.2f}-{max(labels):.2f}"


def format_stat_number(value: float) -> str:
    return f"{value:.1f}" if abs(value) < 100 else f"{value:.0f}"


def dataset_note(dataset: str) -> str:
    notes = {
        "mbjp": "MBJP is a small Java programming readability dataset with continuous human scores.",
        "buse": "Buse contains 100 short Java snippets with averaged human Likert readability ratings from the Buse and Weimer study.",
        "scalabrino": "Scalabrino contains Java snippets with continuous readability scores from the original dataset.",
        "jetbrains": "JetBrains contains Java snippets with binary human readability labels.",
        "dorn": "Dorn is the original mixed-language readability dataset with CUDA, Java, and Python snippets.",
        "schnappinger": "Schnappinger contains Java class-level examples with continuous readability labels derived from the study probabilities.",
    }
    return notes.get(dataset, "Dataset statistics are computed from the local adapter output.")


def write_run_pages(runs: list[Run]) -> None:
    for run in runs:
        data = run.data
        items = load_dataset_items([run])
        rows = "".join(run_sample_row(run, index, item) for index, item in enumerate(items, start=1))
        human_label = dataset_human_label([run])
        score_key = run_sort_key(run)
        body = f"""
        <section class="panel">
          <p class="eyebrow">Run</p>
          <h1>{escape(run.label)}</h1>
          <div class="stats">
            {stat("Metric", f"{run.metric_name} {format_metric(run.metric_value)}")}
            {stat("Valid", str(data.get("valid_count") or data.get("count") or "n/a"))}
            {stat("Errors", str(data.get("error_count") or 0))}
            {stat("Masks", str(data.get("total_mask_count") or "n/a"))}
          </div>
        </section>
        <section class="panel">
          <h2>Configuration</h2>
          {definition_list(run_config_items(run))}
        </section>
        <section class="panel">
          <h2>Samples</h2>
          <table class="records sample-table" data-sortable-samples>
            <thead><tr>{sortable_header("ID", "order", "asc")}{sortable_header(human_label, "human", "desc")}{sortable_header(short_run_label(run), score_key)}{sortable_header("Diff", "diff", "desc")}{sortable_header("LOC", "code-lines", "desc")}</tr></thead>
            <tbody>{rows}</tbody>
          </table>
        </section>
        """
        write_page(DOCS_DIR / "runs" / f"{run.slug}.html", run.label, body, prefix="../")


def run_config_items(run: Run) -> list[tuple[str, str]]:
    data = run.data
    items = [
        ("Method", method_label(run.method)),
        ("Dataset", dataset_label(run.dataset)),
        ("Model", short_model_label(run.model) or "deterministic"),
        ("Summary", str(run.summary_path.relative_to(ROOT))),
    ]
    items.extend(readable_run_config_items(run))
    return items


def readable_run_config_items(run: Run) -> list[tuple[str, str]]:
    data = run.data
    items: list[tuple[str, str]] = []
    if is_rmc_method(run.method):
        if data.get("mask_strategy") is not None:
            items.append(("Masking", readable_masking(data)))
        if data.get("ast_granularity") is not None:
            items.append(("Code Region", readable_granularity(data.get("ast_granularity"))))
        items.append(("Aggregation", RMC_AGGREGATION_LABEL))
        if data.get("max_combination_size") is not None:
            items.append(("Mask Combination", f"Up to {data['max_combination_size']} regions at once"))
        if data.get("sampling_mode") is not None:
            items.append(("Combination Coverage", readable_sampling(data)))
        if data.get("similarity") is not None:
            items.append(("Recovery Match", readable_similarity(data.get("similarity"))))
        return items
    if run.method in COGNASCORE_ML_METHODS:
        model = data.get("embedding_model") or run.model
        if model:
            items.append(("Embeddings", short_model_label(str(model)) or str(model)))
        score_model = data.get("score_model") or {}
        if isinstance(score_model, dict):
            if score_model.get("selected_feature_count") is not None:
                items.append(("Score Model", f"{score_model['selected_feature_count']} selected features + Ridge"))
            if score_model.get("training_sample_count") is not None:
                datasets = score_model.get("training_datasets")
                if isinstance(datasets, list) and datasets:
                    dataset_text = " + ".join(str(dataset) for dataset in datasets)
                    items.append(("Training", f"{score_model['training_sample_count']} samples from {dataset_text}"))
                else:
                    items.append(("Training", f"{score_model['training_sample_count']} samples"))
            if score_model.get("training_policy") is not None:
                items.append(("Evaluation Policy", str(score_model["training_policy"])))
        return items
    metric = data.get("evaluation_metric")
    if metric:
        items.append(("Evaluation", readable_metric(metric)))
    threshold = data.get("classification_threshold")
    if threshold is not None:
        items.append(("Decision Threshold", str(threshold)))
    return items


def readable_masking(data: dict[str, Any]) -> str:
    strategy = str(data.get("mask_strategy", ""))
    dataset = str(data.get("dataset_key") or data.get("source") or "")
    if strategy.startswith("java_ast"):
        return "Java control-flow regions from the AST"
    if strategy.startswith("java_fragment"):
        if dataset == "dorn":
            return "Control-flow regions in CUDA, Java, and Python fragments"
        return "Control-flow regions from token matching"
    return "Masked source regions"


def readable_granularity(value: Any) -> str:
    labels = {
        "control": "Control statements",
        "statement": "Statements",
    }
    return labels.get(str(value), str(value).replace("_", " ").title())


def readable_sampling(data: dict[str, Any]) -> str:
    if data.get("sampling_mode") == "all":
        return "All generated combinations"
    limit = data.get("max_samples_per_stratum")
    if limit is not None:
        return f"Sampled, at most {limit} per group"
    return "Sampled combinations"


def readable_similarity(value: Any) -> str:
    labels = {
        "sequence": "Sequence similarity",
        "edit": "Edit similarity",
        "token_jaccard": "Token Jaccard",
        "bleu": "BLEU",
        "rouge_l": "ROUGE-L",
        "cosine": "Embedding cosine",
    }
    return labels.get(str(value), str(value).replace("_", " ").title())


def readable_metric(value: Any) -> str:
    labels = {
        "spearman": "Spearman correlation",
        "mcc": "Matthews correlation coefficient",
        "binary_threshold_required": "Binary classification threshold",
    }
    return labels.get(str(value), str(value).replace("_", " ").title())


def run_row(run: Run, prefix: str) -> str:
    return (
        "<tr>"
        f'<td><a href="{prefix}runs/{run.slug}.html">{escape(short_run_label(run))}</a></td>'
        f"<td>{escape(short_model_label(run.model) or 'deterministic')}</td>"
        f"<td>{escape(run.metric_name)} {escape(format_metric(run.metric_value))}</td>"
        f"<td>{escape(str(run.count or 'n/a'))}</td>"
        "</tr>"
    )


def method_run_row(run: Run, prefix: str) -> str:
    return (
        "<tr>"
        f'<td><a href="{prefix}runs/{run.slug}.html">{escape(dataset_label(run.dataset))}</a></td>'
        f"<td>{escape(short_model_label(run.model) or 'deterministic')}</td>"
        f"<td>{escape(run.metric_name)} {escape(format_metric(run.metric_value))}</td>"
        f"<td>{escape(str(run.count or 'n/a'))}</td>"
        "</tr>"
    )


def load_dataset_items(runs: list[Run]):
    if not runs:
        return []
    dataset_path = Path(str(runs[0].data.get("dataset", "")))
    if not dataset_path.is_absolute():
        dataset_path = ROOT / dataset_path
    try:
        return load_code_dataset(dataset_path)
    except Exception:
        return []


def write_sample_pages(dataset: str, items, runs: list[Run]) -> None:
    sample_dir = DOCS_DIR / "samples" / slugify(dataset)
    sample_dir.mkdir(parents=True, exist_ok=True)
    for index, item in enumerate(items, start=1):
        score_rows = "".join(sample_score_row(item.task_id, run) for run in runs)
        mode_tabs = sample_mode_tabs(item.task_id, runs)
        mode_panels = sample_mode_panels(item, runs)
        body = f"""
        <section class="panel">
          <p class="eyebrow">Sample</p>
          <h1>{escape(item.task_id)}</h1>
          <div class="stats">
            {stat("Dataset", dataset_label(dataset))}
            {stat(dataset_human_label(runs), format_metric(as_float(item.readability_score)))}
            {stat("Order", str(index))}
            {stat("Lines", str(len(item.content.splitlines())))}
          </div>
        </section>
        <section class="panel">
          <h2>Scores</h2>
          <table class="records">
            <thead><tr><th>Method</th><th>Score</th></tr></thead>
            <tbody>{score_rows}</tbody>
          </table>
        </section>
        <section class="panel">
          <h2>Views</h2>
          <div class="mode-tabs">{mode_tabs}</div>
          {mode_panels}
        </section>
        """
        write_page(sample_dir / f"{slugify(item.task_id)}.html", item.task_id, body, prefix="../../")


def sample_score_row(task_id: str, run: Run) -> str:
    score = run_score_by_task(run).get(task_id)
    return (
        "<tr>"
        f"<td>{escape(short_run_label(run))}</td>"
        f"<td>{escape(format_metric(as_float(score)))}</td>"
        "</tr>"
    )


def sample_mode_tabs(task_id: str, runs: list[Run]) -> str:
    tabs = ['<button class="mode-tab active" type="button" data-mode-target="mode-code">Code</button>']
    for run in runs:
        if task_id in run_score_by_task(run):
            target = f"mode-{run.slug}"
            tabs.append(
                f'<button class="mode-tab" type="button" data-mode-target="{escape(target)}">'
                f"{escape(short_run_label(run))}</button>"
            )
    return "".join(tabs)


def sample_mode_panels(item, runs: list[Run]) -> str:
    panels = [
        (
            '<div class="mode-panel active" id="mode-code">'
            f'<pre class="code-block"><code>{escape(item.content)}</code></pre>'
            '</div>'
        )
    ]
    for run in runs:
        if item.task_id not in run_score_by_task(run):
            continue
        panel_id = f"mode-{run.slug}"
        if run.method == "posnett":
            panels.append(posnett_panel(panel_id, item, run))
        elif is_rmc_method(run.method):
            panels.append(rmc_panel(panel_id, item, run))
        elif run.method in COGNASCORE_ML_METHODS:
            panels.append(cognascore_ml_panel(panel_id, item, run))
        elif run.method in {"llm", "llm_prompt"}:
            panels.append(llm_panel(panel_id, item, run))
        else:
            score = run_score_by_task(run).get(item.task_id)
            panels.append(
                f'<div class="mode-panel" id="{escape(panel_id)}">'
                f"<p class=\"muted\">{escape(short_run_label(run))} visualization placeholder. "
                "This view will show method-specific evidence after the renderer is implemented.</p>"
                f"<div class=\"stats\">{stat('Score', format_metric(as_float(score)))}</div>"
                "</div>"
            )
    return "".join(panels)


def posnett_panel(panel_id: str, item, run: Run) -> str:
    row = run_row_by_task(run).get(item.task_id, {})
    result = row.get("result", {})
    formula = "p = sigmoid(8.87 - 0.033 * Halstead volume + 0.40 * LOC - 1.5 * byte entropy)"
    metrics = [
        ("Score", format_metric(as_float(row.get("score")))),
        ("Probability", format_metric(as_float(result.get("probability")))),
        ("z", format_metric(as_float(result.get("z_value")))),
        ("LOC", str(result.get("lines", "n/a"))),
        ("Halstead V", format_metric(as_float(result.get("halstead_volume")))),
        ("Byte entropy", format_metric(as_float(result.get("byte_entropy")))),
        ("Tokens", str(result.get("token_count", "n/a"))),
        ("Vocabulary", str(result.get("vocabulary_size", "n/a"))),
    ]
    return f"""
    <div class="mode-panel" id="{escape(panel_id)}">
      <div class="grid two">
        <article>
          <h3>Operators</h3>
          <p class="muted">Highlighted spans are Java operators and keywords used in the Halstead component after comments are stripped.</p>
          <pre class="code-block"><code>{highlight_posnett_operations(item.content)}</code></pre>
        </article>
        <article>
          <h3>Formula</h3>
          <p class="formula">{escape(formula)}</p>
          {definition_list(metrics)}
        </article>
      </div>
    </div>
    """


def rmc_panel(panel_id: str, item, run: Run) -> str:
    task_data = task_result_data(run, item.task_id)
    score = run_score_by_task(run).get(item.task_id)
    if not task_data:
        return (
            f'<div class="mode-panel" id="{escape(panel_id)}">'
            f"<p class=\"muted\">No RMC task result found for {escape(item.task_id)}.</p>"
            "</div>"
        )
    control_rows = contributing_control_recoveries(
        task_data,
        selected_order=(1,) if is_rmc_method(run.method) else (3, 2, 1),
    )
    hard = sorted(control_rows, key=lambda row: (as_float(row.get("score")) or 0.0, mask_size(row), span_start(row)))
    control_table_rows = "".join(
        control_recovery_row(rank, row) for rank, row in enumerate(control_rows, start=1)
    )
    if not control_table_rows:
        control_table_rows = '<tr><td colspan="6" class="missing">No contributing control recovery available.</td></tr>'
    patches = mask_patch_cards(hard, task_data, run.method)
    aggregation_label = RMC_AGGREGATION_LABEL
    stats = [
        ("Displayed Score", format_metric(as_float(score))),
        ("Aggregation", aggregation_label),
        ("Masks", str(len(task_data.get("masks", [])))),
        ("Displayed Controls", str(len(control_rows))),
    ]
    return f"""
    <div class="mode-panel" id="{escape(panel_id)}">
      <div class="grid two">
        <article class="rmc-source-panel">
          <h3>Source Code</h3>
          <pre class="code-block rmc-source"><code>{render_source_lines(task_data)}</code></pre>
          {definition_list(stats)}
        </article>
        <article>
          <h3>Control Recoveries</h3>
          <table class="records control-records">
            <thead><tr><th>#</th><th>Control</th><th>Recovery</th><th>Size</th><th>Lines</th></tr></thead>
            <tbody>{control_table_rows}</tbody>
          </table>
          <div class="patch-head">
            <h3>Model Patches</h3>
            <button class="patch-sort" type="button" data-sort-dir="desc">Worst first <span>↓</span></button>
          </div>
          {patches}
        </article>
      </div>
    </div>
    """


def cognascore_ml_panel(panel_id: str, item, run: Run) -> str:
    row = run_row_by_task(run).get(item.task_id, {})
    result = row.get("result", {}) if isinstance(row.get("result"), dict) else {}
    score_model = run.data.get("score_model", {})
    if not isinstance(score_model, dict):
        score_model = {}
    metrics = [
        ("Predicted readability", format_metric(as_float(row.get("score")))),
        ("Score model", str(result.get("score_model", score_model.get("name", "n/a")))),
        ("Selected features", str(score_model.get("selected_feature_count", "n/a"))),
        ("Ridge alpha", str(score_model.get("ridge_alpha", "n/a"))),
    ]
    return f"""
    <div class="mode-panel" id="{escape(panel_id)}">
      <div class="grid two">
        <article>
          <h3>CognaScore ML prediction</h3>
          {definition_list(metrics)}
          <p class="muted evidence-note">This is the output of the frozen selected-feature Ridge model. Feature-selection experiments are kept separately from the materialized score.</p>
        </article>
        <article>
          <h3>Code</h3>
          <pre class="code-block"><code>{escape(item.content)}</code></pre>
        </article>
      </div>
    </div>
    """


def llm_panel(panel_id: str, item, run: Run) -> str:
    row = run_row_by_task(run).get(item.task_id, {})
    result = row.get("result", {}) if isinstance(row.get("result"), dict) else {}
    score = as_float(row.get("score"))
    reasoning = str(result.get("reasoning") or row.get("reasoning") or "No reasoning stored.")
    metrics = [
        ("Score", format_metric(score)),
        ("Scale", "0-20"),
        ("Model", short_model_label(run.model) or str(run.model or "n/a")),
    ]
    prompt = LLM_READABILITY_PROMPT_TEMPLATE.format(code="{code}")
    return f"""
    <div class="mode-panel" id="{escape(panel_id)}">
      <div class="grid two">
        <article>
          <h3>LLM Score</h3>
          {definition_list(metrics)}
        </article>
        <article>
          <h3>Reasoning</h3>
          <p class="muted llm-reasoning">{escape(reasoning)}</p>
        </article>
      </div>
      <h3>Prompt</h3>
      <pre class="code-block"><code>{escape(prompt)}</code></pre>
    </div>
    """


def run_row_by_task(run: Run) -> dict[str, dict[str, Any]]:
    result = {}
    for row in run.data.get("results", []):
        task_id = row.get("task_id")
        if task_id is not None:
            result[str(task_id)] = row
    return result


def task_result_data(run: Run, task_id: str) -> dict[str, Any] | None:
    key = (run.summary_path.parent, task_id)
    if key in _TASK_RESULT_CACHE:
        return _TASK_RESULT_CACHE[key]
    path = run.summary_path.parent / safe_path_part(task_id) / "result.json"
    if not path.is_file():
        _TASK_RESULT_CACHE[key] = None
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        data = None
    _TASK_RESULT_CACHE[key] = data
    return data


def display_score_for_row(run: Run, row: dict[str, Any]) -> float | None:
    task_id = row.get("task_id")
    if is_rmc_method(run.method) and task_id is not None:
        return score_task_result(task_result_data(run, str(task_id)))
    return as_float(row.get("score", row.get("rmc_score")))


def hardest_contributing_mask_recoveries(
    task_data: dict[str, Any],
    selected_order: tuple[int, ...] = (3, 2, 1),
) -> list[dict[str, Any]]:
    contributing = contributing_control_recoveries(task_data, selected_order)
    count = len(contributing)
    for row in contributing:
        score = as_float(row.get("score"))
        row["impact"] = None if score is None or count == 0 else (1 - score) / count
    return sorted(contributing, key=lambda row: (as_float(row.get("score")) or 0.0, mask_size(row), span_start(row)))


def contributing_control_recoveries(
    task_data: dict[str, Any],
    selected_order: tuple[int, ...] = (3, 2, 1),
) -> list[dict[str, Any]]:
    rows = []
    masks = {mask.get("index"): mask for mask in task_data.get("masks", [])}
    source_tokens = source_token_count(task_data)
    for recovery in task_data.get("recoveries", []):
        mask = masks.get(recovery.get("index"), {})
        score = as_float(recovery.get("score", recovery.get("similarity")))
        k = mask.get("selected_segments") or recovery.get("selected_segments")
        if score is None:
            continue
        row = dict(mask)
        row.update(recovery)
        row["score"] = score
        row["k"] = k
        row["source_token_count"] = source_tokens
        rows.append(row)
    active = contributing_mask_size(rows, selected_order)
    if active is None:
        return []
    return sorted(
        [row for row in rows if row.get("k") == active],
        key=lambda row: (span_start(row), mask_label(row)),
    )


def contributing_mask_size(
    rows: list[dict[str, Any]],
    selected_order: tuple[int, ...] = (3, 2, 1),
) -> int | None:
    for selected in selected_order:
        if any(row.get("k") == selected for row in rows):
            return selected
    return None


def hard_mask_row(rank: int, row: dict[str, Any]) -> str:
    score = as_float(row.get("score", row.get("similarity")))
    gap = None if score is None else 1 - score
    return (
        "<tr>"
        f"<td>{rank}</td>"
        f"<td>{escape(mask_label(row))}</td>"
        f"<td>{escape(format_metric(score))}</td>"
        f"<td>{escape(format_metric(gap))}</td>"
        f"<td>{escape(span_label(row))}</td>"
        "</tr>"
    )


def control_recovery_row(rank: int, row: dict[str, Any]) -> str:
    score = as_float(row.get("score", row.get("similarity")))
    status = recovery_status(score)
    size = mask_size_label(row)
    return (
        f'<tr class="control-row {status}">'
        f"<td>{rank}</td>"
        f"<td>{escape(mask_label(row))}</td>"
        f'<td><span class="recovery-badge {status}">{escape(format_metric(score))}</span></td>'
        f"<td>{escape(size)}</td>"
        f"<td>{escape(span_label(row))}</td>"
        "</tr>"
    )


def recovery_status(score: float | None) -> str:
    if score is None:
        return "recovery-missing"
    if score >= 0.7:
        return "recovery-good"
    if score >= 0.4:
        return "recovery-mid"
    return "recovery-bad"


def mask_size_label(row: dict[str, Any]) -> str:
    token_count = as_int(row.get("token_count"))
    source_tokens = as_int(row.get("source_token_count"))
    if token_count is None:
        return "n/a"
    if source_tokens is None or source_tokens <= 0:
        return f"{token_count} tok"
    return f"{token_count} tok · {token_count / source_tokens:.1%}"


def source_token_count(task_data: dict[str, Any]) -> int:
    return rmc_source_token_count(task_data)


def mask_patch_cards(rows: list[dict[str, Any]], task_data: dict[str, Any], method: str) -> str:
    if not rows:
        return '<p class="missing">No model patch available.</p>'
    blocks = []
    for rank, row in enumerate(rows, start=1):
        score = as_float(row.get("score", row.get("similarity")))
        gap = None if score is None else 1 - score
        status = recovery_status(score)
        recovered, recovered_label = recovered_patch_for_row(row, method)
        expected = expected_patch_for_row(row, task_data, method)
        line_indices = ",".join(str(index) for index in row_line_indices(row))
        blocks.append(
            f'<section class="patch-card {status}" data-score="{number_attr(score)}">'
            f'<details class="mask-detail" data-lines="{escape(line_indices)}" data-status="{escape(status)}">'
            "<summary>"
            f'<span class="patch-title">#{rank} {escape(mask_label(row))}</span>'
            f'<span class="recovery-badge {status}">{escape(format_metric(score))}</span>'
            f'<span class="patch-meta">gap {escape(format_metric(gap))} · lines {escape(span_label(row))}</span>'
            "</summary>"
            f'<p class="muted">{escape(recovered_label)}</p>'
            f'<pre class="code-block patch"><code>{escape(clean_display_code(recovered))}</code></pre>'
            '<p class="muted patch-subtitle">Original hidden code</p>'
            f'<pre class="code-block patch"><code>{escape(clean_display_code(expected))}</code></pre>'
            "</details>"
            '</section>'
        )
    return "".join(blocks)


def clean_display_code(code: str) -> str:
    return "\n".join(line.rstrip() for line in code.splitlines())


def row_line_indices(row: dict[str, Any]) -> list[int]:
    indices: list[int] = []
    for span in row.get("spans", []):
        try:
            start = int(span.get("start", 0))
            end = int(span.get("end", start + 1))
        except (TypeError, ValueError):
            continue
        indices.extend(range(max(start, 0), max(end, start + 1)))
    return sorted(set(indices))


def recovered_patch_for_row(row: dict[str, Any], method: str) -> tuple[str, str]:
    recovered = str(row.get("recovered_text") or row.get("recovered_code") or "")
    if not recovered.strip():
        recovered = str(row.get("llm_answer") or "No recovered patch stored.")
    return recovered, "Model prediction as a readability repair patch"


def expected_patch_for_row(row: dict[str, Any], task_data: dict[str, Any], method: str) -> str:
    return str(row.get("expected_text") or row.get("expected_source") or "")


def source_from_char_spans(row: dict[str, Any], source: str) -> str:
    spans = row.get("char_spans") or []
    if not source or not isinstance(spans, list):
        return ""
    parts = []
    for span in spans:
        try:
            start = int(span.get("start", 0))
            end = int(span.get("end", start))
        except (TypeError, ValueError):
            continue
        if 0 <= start < end <= len(source):
            parts.append(source[start:end])
    return "\n...\n".join(parts)


def source_from_line_spans(row: dict[str, Any], task_data: dict[str, Any]) -> str:
    lines = task_data.get("source_lines") or []
    spans = row.get("spans") or []
    if not isinstance(lines, list) or not isinstance(spans, list):
        return ""
    parts = []
    for span in spans:
        try:
            start = int(span.get("start", 0))
            end = int(span.get("end", start + 1))
        except (TypeError, ValueError):
            continue
        chunk = lines[max(start, 0) : min(end, len(lines))]
        if chunk:
            parts.append("\n".join(str(line) for line in chunk))
    return "\n...\n".join(parts)


def extract_single_mask_replacement(masked_text: str, recovered: str) -> str | None:
    if masked_text.count("<mask>") != 1 or not recovered:
        return None
    prefix, suffix = masked_text.split("<mask>", 1)
    if recovered.startswith(prefix) and recovered.endswith(suffix):
        return recovered[len(prefix) : len(recovered) - len(suffix)]
    return None


def highlight_hard_masks(task_data: dict[str, Any], hard_rows: list[dict[str, Any]]) -> str:
    lines = task_data.get("source_lines") or []
    if not isinstance(lines, list):
        lines = []
    rank_by_line: dict[int, int] = {}
    for rank, row in enumerate(hard_rows, start=1):
        for span in row.get("spans", []):
            start = int(span.get("start", 0))
            end = int(span.get("end", start + 1))
            for line_index in range(start, end):
                rank_by_line.setdefault(line_index, rank)
    rendered = []
    for index, line in enumerate(lines):
        rank = rank_by_line.get(index)
        label = f"{index + 1:>4} "
        escaped = escape(str(line))
        if rank == 1:
            rendered.append(f'<span class="hard hard-1">{escape(label)}{escaped}</span>')
        elif rank == 2:
            rendered.append(f'<span class="hard hard-2">{escape(label)}{escaped}</span>')
        else:
            rendered.append(f"{escape(label)}{escaped}")
    return "\n".join(rendered)


def highlight_control_recoveries(task_data: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    lines = task_data.get("source_lines") or []
    if not isinstance(lines, list):
        lines = []
    status_by_line: dict[int, str] = {}
    rank_by_line: dict[int, int] = {}
    priority = {
        "recovery-bad": 3,
        "recovery-mid": 2,
        "recovery-good": 1,
        "recovery-missing": 0,
    }
    for rank, row in enumerate(rows, start=1):
        status = recovery_status(as_float(row.get("score", row.get("similarity"))))
        for span in row.get("spans", []):
            start = int(span.get("start", 0))
            end = int(span.get("end", start + 1))
            for line_index in range(start, end):
                current = status_by_line.get(line_index)
                if current is None or priority[status] > priority[current]:
                    status_by_line[line_index] = status
                    rank_by_line[line_index] = rank
    rendered = []
    for index, line in enumerate(lines):
        label = f"{index + 1:>4} "
        escaped = escape(str(line))
        status = status_by_line.get(index)
        if status:
            rank = rank_by_line.get(index, 0)
            rendered.append(
                f'<span class="control-highlight {status}" title="control recovery #{rank}">'
                f"{escape(label)}{escaped}</span>"
            )
        else:
            rendered.append(f"{escape(label)}{escaped}")
    return "\n".join(rendered)


def render_source_lines(task_data: dict[str, Any]) -> str:
    lines = task_data.get("source_lines") or []
    if not isinstance(lines, list):
        lines = []
    rendered = []
    for index, line in enumerate(lines):
        label = f"{index + 1:>4} "
        rendered.append(
            f'<span class="source-line" data-line="{index}">{escape(label)}{escape(str(line))}</span>'
        )
    return "".join(rendered)


def control_label(row: dict[str, Any]) -> str:
    node_type = row.get("node_type")
    role = row.get("ast_role")
    if node_type and role:
        return f"{node_type} · {role}"
    if node_type:
        return str(node_type)
    nodes = row.get("node_types")
    if isinstance(nodes, list) and nodes:
        return ", ".join(str(node) for node in nodes)
    return "control"


def mask_label(row: dict[str, Any]) -> str:
    selected = row.get("selected_segments")
    if selected is None:
        selected = mask_size(row)
    if selected == 1:
        return control_label(row)
    nodes = row.get("node_types")
    if isinstance(nodes, list) and nodes:
        preview = ", ".join(str(node) for node in nodes[:3])
        suffix = "" if len(nodes) <= 3 else f" +{len(nodes) - 3}"
        return f"{selected}-mask · {preview}{suffix}"
    return f"{selected}-mask"


def mask_size(row: dict[str, Any]) -> int:
    selected = row.get("selected_segments")
    if isinstance(selected, int):
        return selected
    spans = row.get("spans")
    if isinstance(spans, list):
        return len(spans)
    return 0


def span_label(row: dict[str, Any]) -> str:
    spans = row.get("spans") or []
    labels = []
    for span in spans:
        start = int(span.get("start", 0)) + 1
        end = int(span.get("end", start)) 
        labels.append(str(start) if end <= start else f"{start}-{end}")
    return ", ".join(labels) if labels else "n/a"


def span_start(row: dict[str, Any]) -> int:
    spans = row.get("spans") or []
    if not spans:
        return 0
    return int(spans[0].get("start", 0))


def highlight_posnett_operations(code: str) -> str:
    stripped = "\n".join(line.rstrip() for line in strip_comments(code).splitlines())
    parts = []
    cursor = 0
    for match in TOKEN_PATTERN.finditer(stripped):
        token = match.group(0)
        parts.append(escape(stripped[cursor:match.start()]))
        if token in JAVA_OPERATORS or token in JAVA_KEYWORDS:
            parts.append(f'<mark>{escape(token)}</mark>')
        else:
            parts.append(escape(token))
        cursor = match.end()
    parts.append(escape(stripped[cursor:]))
    return "".join(parts)


def dataset_sample_row(dataset: str, index: int, item, runs: list[Run]) -> str:
    score_cells = []
    loc = len(item.content.splitlines())
    sort_attrs = [
        f'data-order="{index}"',
        f'data-human="{number_attr(item.readability_score)}"',
        f'data-code-lines="{loc}"',
    ]
    for run in runs:
        score = run_score_by_task(run).get(item.task_id)
        key = run_sort_key(run)
        sort_attrs.append(f'data-{key}="{number_attr(score)}"')
        score_cells.append(f"<td>{escape(format_metric(as_float(score)))}</td>")
    sample_href = f"../samples/{slugify(dataset)}/{slugify(item.task_id)}.html"
    return (
        f"<tr {' '.join(sort_attrs)}>"
        f'<td><a href="{sample_href}">{escape(item.task_id)}</a></td>'
        f"<td>{escape(format_metric(as_float(item.readability_score)))}</td>"
        + "".join(score_cells)
        + f"<td>{escape(str(loc))}</td>"
        "</tr>"
    )


def run_sample_row(run: Run, index: int, item) -> str:
    score = run_score_by_task(run).get(item.task_id)
    if score is None:
        return ""
    diff = run_difference_by_task(run).get(item.task_id)
    loc = len(item.content.splitlines())
    score_key = run_sort_key(run)
    sample_href = f"../samples/{slugify(run.dataset)}/{slugify(item.task_id)}.html"
    sort_attrs = [
        f'data-order="{index}"',
        f'data-human="{number_attr(item.readability_score)}"',
        f'data-{score_key}="{number_attr(score)}"',
        f'data-diff="{number_attr(diff)}"',
        f'data-code-lines="{loc}"',
    ]
    return (
        f"<tr {' '.join(sort_attrs)}>"
        f'<td><a href="{sample_href}">{escape(item.task_id)}</a></td>'
        f"<td>{escape(format_metric(as_float(item.readability_score)))}</td>"
        f"<td>{escape(format_metric(as_float(score)))}</td>"
        f"<td>{escape(format_metric(as_float(diff)))}</td>"
        f"<td>{escape(str(loc))}</td>"
        "</tr>"
    )


def sortable_header(label: str, key: str, initial_dir: str = "desc") -> str:
    return (
        '<th>'
        f'<button class="sort-header" type="button" data-sort-key="{escape(key)}" '
        f'data-sort-dir="{escape(initial_dir)}">{escape(label)} <span aria-hidden="true">↕</span></button>'
        '</th>'
    )


def run_score_by_task(run: Run) -> dict[str, float | None]:
    if run.slug in _RUN_SCORE_CACHE:
        return _RUN_SCORE_CACHE[run.slug]
    result = {}
    for row in run.data.get("results", []):
        task_id = row.get("task_id")
        if task_id is None:
            continue
        result[str(task_id)] = display_score_for_row(run, row)
    _RUN_SCORE_CACHE[run.slug] = result
    return result


def run_difference_by_task(run: Run) -> dict[str, float | None]:
    rows = run.valid_rows()
    if not rows:
        return {}
    scores = [float(row["score"]) for row in rows]
    human = [float(row["readability_score"]) for row in rows]
    if all(value in {0.0, 1.0} for value in human):
        threshold = as_float(run.data.get("classification_threshold"))
        if threshold is None:
            threshold = best_binary_threshold_value(scores, [int(value) for value in human])
        if threshold is None:
            return {str(row["task_id"]): None for row in rows}
        return {
            str(row["task_id"]): abs(float(float(row["score"]) >= threshold) - float(row["readability_score"]))
            for row in rows
        }

    score_ranks = percentile_ranks(scores)
    human_ranks = percentile_ranks(human)
    if continuous_direction(run, scores, human) < 0:
        score_ranks = [1.0 - value for value in score_ranks]
    return {
        str(row["task_id"]): abs(score_rank - human_rank)
        for row, score_rank, human_rank in zip(rows, score_ranks, human_ranks)
    }


def percentile_ranks(values: list[float]) -> list[float]:
    if len(values) <= 1:
        return [0.0 for _ in values]
    ordered = sorted((value, index) for index, value in enumerate(values))
    ranks = [0.0 for _ in values]
    start = 0
    while start < len(ordered):
        end = start + 1
        while end < len(ordered) and ordered[end][0] == ordered[start][0]:
            end += 1
        average_rank = (start + end - 1) / 2
        percentile = average_rank / (len(values) - 1)
        for _, index in ordered[start:end]:
            ranks[index] = percentile
        start = end
    return ranks


def continuous_direction(run: Run, scores: list[float], human: list[float]) -> int:
    value = run.metric_value
    if value is None and len(scores) >= 2:
        value = spearman(scores, human)
    return -1 if value is not None and value < 0 else 1


def run_sort_key(run: Run) -> str:
    return "score-" + slugify(run.slug).lower().replace(".", "_")


def run_group_key(run: Run) -> tuple[str, str | None]:
    if run.method in COGNASCORE_ML_METHODS or run.method == "cognascore_compact":
        return run.method, None
    if run.model:
        return run.method, run.model
    return run.method, None


def run_group_label(method: str, model: str | None) -> str:
    if method in COGNASCORE_ML_METHODS or method == "cognascore_compact":
        return method_label(method)
    if model is None:
        return method_label(method)
    short = short_model_label(model) or model
    if is_rmc_method(method):
        return f"{method_label(method)} {short}"
    return f"{method_label(method)} ({short})"


def run_group_rank(group: tuple[str, str | None]) -> tuple[int, str, str]:
    method, model = group
    return method_rank(method) + (short_model_label(model) or model or "",)


def short_run_label(run: Run) -> str:
    model = short_model_label(run.model)
    if run.method in COGNASCORE_ML_METHODS or run.method == "cognascore_compact":
        return method_label(run.method)
    if is_rmc_method(run.method) and model:
        return f"{method_label(run.method)} {model}"
    if model:
        return f"{method_label(run.method)} ({model})"
    return method_label(run.method)


def dataset_human_label(runs: list[Run]) -> str:
    values = []
    for run in runs:
        for row in run.data.get("results", []):
            value = as_float(row.get("readability_score"))
            if value is not None:
                values.append(value)
    if values and all(value in {0.0, 1.0} for value in values):
        return "Label"
    return "Human"


def number_attr(value: Any) -> str:
    number = as_float(value)
    return "" if number is None else f"{number:.12g}"


def task_row(row: dict[str, Any], run: Run | None = None) -> str:
    task_id = row.get("task_id", "unknown")
    score = display_score_for_row(run, row) if run is not None else row.get("rmc_score", row.get("score"))
    return (
        "<tr>"
        f"<td>{escape(str(task_id))}</td>"
        f"<td>{escape(format_metric(as_float(row.get('readability_score'))))}</td>"
        f"<td>{escape(format_metric(as_float(score)))}</td>"
        f"<td>{escape(str(row.get('mask_count', '')))}</td>"
        "</tr>"
    )


def best_mcc(scores: list[float], actual: list[int]) -> float | None:
    unique = sorted(set(scores))
    if not unique:
        return None
    candidates = [unique[0] - 1e-12]
    candidates.extend((left + right) / 2 for left, right in zip(unique, unique[1:]))
    candidates.append(unique[-1] + 1e-12)
    best = None
    for threshold in candidates:
        predicted = [int(score >= threshold) for score in scores]
        value = matthews_correlation_coefficient(predicted, actual)
        if best is None or value > best:
            best = value
    return best


def best_binary_threshold_value(scores: list[float], actual: list[int]) -> float | None:
    unique = sorted(set(scores))
    if not unique:
        return None
    candidates = [unique[0] - 1e-12]
    candidates.extend((left + right) / 2 for left, right in zip(unique, unique[1:]))
    candidates.append(unique[-1] + 1e-12)
    best_threshold = None
    best_value = None
    for threshold in candidates:
        predicted = [int(score >= threshold) for score in scores]
        value = matthews_correlation_coefficient(predicted, actual)
        if best_value is None or value > best_value:
            best_value = value
            best_threshold = threshold
    return best_threshold


def write_page(path: Path, title: str, body: str, prefix: str = "", current: str = "") -> None:
    nav = f"""
    <nav class="topbar">
      <a class="brand" href="{prefix}index.html">Readability</a>
      <div>
        <a href="{prefix}index.html">{escape(current or "Results")}</a>
      </div>
    </nav>
    """
    page = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)} · Readability</title>
  <link rel="stylesheet" href="{prefix}assets/style.css">
  <script src="{prefix}assets/app.js" defer></script>
</head>
<body>
  {nav}
  <main>{body}</main>
</body>
</html>
"""
    path.write_text(page, encoding="utf-8")


def stat(label: str, value: str) -> str:
    return f'<div class="stat"><span>{escape(label)}</span><strong>{escape(value)}</strong></div>'


def definition_list(items: list[tuple[str, str]]) -> str:
    return "<dl>" + "".join(f"<dt>{escape(k)}</dt><dd>{escape(v)}</dd>" for k, v in items) + "</dl>"


def link_item(href: str, label: str) -> str:
    return f'<a href="{href}">{escape(label)}</a>'


def as_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def as_int(value: Any) -> int | None:
    number = as_float(value)
    return None if number is None else int(number)


def format_metric(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.4f}"


def slugify(value: str) -> str:
    result = []
    for char in value:
        if char.isalnum() or char in {".", "_", "-"}:
            result.append(char)
        else:
            result.append("-")
    return "".join(result).strip("-._") or "default"


def escape(value: str) -> str:
    return html.escape(value, quote=True)


STYLE_CSS = """
:root {
  color-scheme: light;
  --bg: #f5f7f8;
  --panel: #ffffff;
  --text: #1d252c;
  --muted: #68717a;
  --line: #dce2e7;
  --accent: #176b87;
  --accent-soft: #e6f3f6;
  --good: #1b7f4c;
}

* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font: 15px/1.5 ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
main { width: min(1180px, calc(100vw - 32px)); margin: 24px auto 56px; }
.topbar {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background: rgba(255,255,255,.92);
  border-bottom: 1px solid var(--line);
  position: sticky;
  top: 0;
  z-index: 2;
}
.brand { font-weight: 750; color: var(--text); }
.panel {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 22px;
  margin-bottom: 18px;
}
.panel.small { margin-bottom: 0; }
.panel-head {
  display: flex;
  gap: 24px;
  justify-content: space-between;
  align-items: end;
  margin-bottom: 18px;
}
.panel-head.compact { align-items: start; margin-bottom: 10px; }
h1, h2 { margin: 0; line-height: 1.15; letter-spacing: 0; }
h1 { font-size: 30px; }
h2 { font-size: 18px; margin-bottom: 14px; }
h3 { margin: 0 0 10px; font-size: 15px; }
.eyebrow {
  margin: 0 0 6px;
  color: var(--accent);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: .08em;
  text-transform: uppercase;
}
.muted { color: var(--muted); max-width: 620px; margin: 0; }
.muted.wide { max-width: 960px; }
.llm-reasoning { max-width: 760px; line-height: 1.55; }
.feature-diagram {
  margin: 22px 0;
  padding: 0;
}
.feature-diagram figcaption {
  display: flex;
  flex-direction: column;
  gap: 3px;
  margin-bottom: 12px;
  color: var(--text);
  font-weight: 750;
}
.feature-diagram figcaption small {
  color: var(--muted);
  font-weight: 500;
}
.feature-diagram-flow {
  display: grid;
  grid-template-columns: minmax(210px, .9fr) minmax(190px, .75fr) minmax(420px, 1.8fr);
  gap: 14px;
  align-items: stretch;
}
.feature-column {
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 12px;
  background: #fbfcfd;
}
.traditional-column {
  background: #fbfaf7;
  border-color: #e2d8c4;
}
.cognascore-column {
  background: #f8fbfd;
  border-color: #cfe0ea;
}
.column-title {
  margin-bottom: 10px;
  color: var(--text);
  font-size: 13px;
  font-weight: 750;
  letter-spacing: .04em;
  text-transform: uppercase;
}
.cognascore-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}
.feature-box {
  border: 1px solid var(--line);
  border-radius: 9px;
  padding: 10px;
  background: rgba(255,255,255,.74);
}
.embedding-box {
  border-color: #d8ccef;
  background: #fbf8ff;
}
.cluster-box {
  border-color: #bfdced;
  background: #f4fbff;
}
.wide-box { grid-column: 1 / -1; }
.feature-box h3 {
  margin: 0 0 4px;
  font-size: 15px;
}
.feature-box p {
  margin: 0 0 10px;
  color: var(--muted);
  font-size: 13px;
}
.source-column {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 10px;
  min-width: 0;
}
.source-card,
.chunk-card {
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 10px;
  background: #ffffff;
}
.source-card span,
.chunk-card span {
  display: block;
  margin-bottom: 7px;
  color: var(--accent);
  font-size: 12px;
  font-weight: 750;
  letter-spacing: .04em;
  text-transform: uppercase;
}
.source-card pre {
  margin: 0;
  padding: 8px;
  max-width: none;
  max-height: none;
  font-size: 11px;
}
.chunk-card div {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.chunk-card code {
  padding: 3px 7px;
  border: 1px solid #cbbff0;
  border-radius: 999px;
  background: #f4f0ff;
  color: #4b357f;
  font: 12px/1.35 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}
.flow-arrow {
  align-self: center;
  color: var(--accent);
  font-size: 24px;
  font-weight: 750;
}
.figure-note {
  margin: 10px 0 0;
  color: var(--muted);
  font-size: 12px;
}
.feature-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
}
.feature-tags code {
  display: inline-flex;
  align-items: center;
  min-height: 26px;
  padding: 3px 7px;
  border: 1px solid #cfd7de;
  border-radius: 999px;
  background: #f7f9fa;
  color: #2d3942;
  font: 12px/1.35 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}
.feature-tags.embedding-tags code {
  border-color: #cbbff0;
  background: #f4f0ff;
  color: #4b357f;
}
.feature-tags.cluster-tags code {
  border-color: #b6d9f0;
  background: #eef8ff;
  color: #195d82;
}
.matrix-wrap { overflow-x: auto; }
.method-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: -4px 0 16px;
}
.method-filter {
  appearance: none;
  border: 1px solid var(--line);
  border-radius: 999px;
  background: #f7f9fa;
  color: var(--text);
  padding: 6px 10px;
  font: inherit;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
}
.method-filter[draggable="true"] { cursor: grab; }
.method-filter.dragging {
  opacity: .55;
  cursor: grabbing;
}
.method-filter.active {
  border-color: #9fc7d5;
  background: var(--accent-soft);
  color: var(--accent);
}
.method-filter:not(.active) {
  color: var(--muted);
  text-decoration: line-through;
}
table { border-collapse: collapse; width: 100%; }
th, td { border-bottom: 1px solid var(--line); padding: 12px 10px; text-align: left; vertical-align: top; }
th { font-weight: 700; color: #2b333a; background: #fafbfc; }
.matrix th:first-child { min-width: 190px; }
.matrix td { min-width: 150px; }
.result-link {
  display: inline-flex;
  flex-direction: column;
  min-width: 112px;
  padding: 8px 10px;
  border: 1px solid transparent;
  border-radius: 8px;
  background: transparent;
}
.result-link:hover { background: #f7f9fa; border-color: var(--line); }
.result-link.best {
  background: #e7f6ec;
  border-color: #7fc894;
}
.result-link.best:hover { background: #dbf0e2; border-color: #5eb577; }
.result-link strong { color: var(--text); font-size: 17px; }
.result-link span { color: var(--muted); font-size: 12px; }
.result-link small { color: var(--muted); font-size: 11px; margin-top: 2px; }
.missing { color: #9aa3ab; }
.grid { display: grid; gap: 18px; margin-bottom: 18px; }
.grid.two { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.link-list { display: flex; flex-wrap: wrap; gap: 10px; }
.link-list a {
  display: inline-flex;
  align-items: center;
  min-height: 34px;
  padding: 6px 10px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: #fbfcfd;
}
.stats { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin-top: 18px; }
.stat { border: 1px solid var(--line); border-radius: 8px; padding: 12px; background: #fbfcfd; }
.stat span { display: block; color: var(--muted); font-size: 12px; }
.stat strong { display: block; margin-top: 4px; font-size: 18px; overflow-wrap: anywhere; }
dl { display: grid; grid-template-columns: 170px 1fr; gap: 8px 14px; margin: 0; }
dt { color: var(--muted); }
dd { margin: 0; overflow-wrap: anywhere; }
.records th, .records td { font-size: 14px; }
.sort-header {
  appearance: none;
  border: 0;
  background: transparent;
  color: inherit;
  padding: 0;
  font: inherit;
  font-weight: 700;
  cursor: pointer;
}
.sort-header:hover { color: var(--accent); }
.sort-header span { color: var(--muted); margin-left: 4px; }
.sort-header.active span { color: #c74343; }
.mode-tabs {
  display: flex;
  gap: 6px;
  border-bottom: 1px solid var(--line);
  margin-bottom: 16px;
  overflow-x: auto;
}
.mode-tab {
  appearance: none;
  border: 0;
  border-bottom: 2px solid transparent;
  background: transparent;
  color: var(--muted);
  padding: 8px 10px;
  font: inherit;
  font-weight: 700;
  cursor: pointer;
  white-space: nowrap;
}
.mode-tab.active {
  color: var(--accent);
  border-bottom-color: var(--accent);
}
.mode-panel { display: none; }
.mode-panel.active { display: block; }
.formula {
  margin: 0 0 14px;
  padding: 10px 12px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: #fbfcfd;
  font: 13px/1.45 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}
.method-hero {
  max-width: 920px;
  margin-bottom: 18px;
  padding: 18px 20px;
  border: 1px solid #d7e4ea;
  border-radius: 14px;
  background:
    radial-gradient(circle at 12% 0%, rgba(23,107,135,.12), transparent 34%),
    linear-gradient(135deg, #fbfdfe, #f5fafc);
}
.method-hero p:last-child {
  margin: 0;
  color: #34424d;
  font-size: 16px;
  line-height: 1.65;
}
.feature-figure {
  margin: 18px 0 20px;
  max-width: 1040px;
}
.feature-figure figcaption {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: end;
  margin-bottom: 12px;
  color: #26333d;
}
.feature-figure figcaption span {
  font-size: 17px;
  font-weight: 760;
}
.feature-figure figcaption small {
  color: var(--muted);
  font-size: 12px;
}
.feature-map {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}
.feature-group {
  position: relative;
  min-height: 170px;
  padding: 16px;
  border: 1px solid var(--line);
  border-radius: 14px;
  background: #fff;
  overflow: hidden;
}
.feature-group::before {
  content: "";
  position: absolute;
  inset: 0 0 auto;
  height: 5px;
  background: #9aa3ab;
}
.feature-group-head {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  margin-bottom: 12px;
}
.feature-icon {
  display: inline-grid;
  place-items: center;
  flex: 0 0 auto;
  width: 34px;
  height: 34px;
  border-radius: 10px;
  background: #eef2f5;
  color: #34424d;
  font-weight: 800;
}
.feature-group h3 {
  margin: 0 0 4px;
  font-size: 15px;
}
.feature-group p {
  margin: 0;
  color: var(--muted);
  font-size: 12px;
  line-height: 1.45;
}
.feature-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  list-style: none;
  padding: 0;
  margin: 0;
}
.feature-list li {
  min-height: 50px;
  padding: 9px 10px;
  border: 1px solid rgba(0,0,0,.06);
  border-radius: 10px;
  background: rgba(248,250,252,.88);
}
.feature-list code {
  display: block;
  color: #18242d;
  font: 11px/1.35 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  overflow-wrap: anywhere;
}
.feature-list span {
  display: block;
  margin-top: 4px;
  color: var(--muted);
  font-size: 11px;
  line-height: 1.25;
}
.code-group::before,
.visual-group::before { background: #8c98a4; }
.code-group .feature-icon,
.visual-group .feature-icon { background: #eef2f5; color: #34424d; }
.embedding-group {
  border-color: #d8c9f2;
  background: linear-gradient(180deg, #fff, #fbf8ff);
}
.embedding-group::before { background: #8f63d8; }
.embedding-group .feature-icon { background: #efe8fb; color: #6d42b8; }
.cluster-group {
  border-color: #b9d9ee;
  background: linear-gradient(180deg, #fff, #f6fbff);
}
.cluster-group::before { background: #2178a8; }
.cluster-group .feature-icon { background: #e5f3fb; color: #176b87; }
.feature-legend {
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
  margin-top: 12px;
  color: var(--muted);
  font-size: 12px;
}
.feature-legend span {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.feature-legend i {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  display: inline-block;
}
.legend-code { background: #8c98a4; }
.legend-embedding { background: #8f63d8; }
.legend-cluster { background: #2178a8; }
pre {
  max-width: min(880px, calc(100vw - 80px));
  max-height: 420px;
  overflow: auto;
  margin: 12px 0 0;
  padding: 12px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: #f7f9fa;
  color: #1d252c;
  font: 12px/1.45 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}
.code-block { max-width: none; }
.code-block mark {
  background: #fff2a8;
  color: inherit;
  padding: 0 1px;
  border-radius: 3px;
}
.hard {
  display: block;
  margin: 0 -4px;
  padding: 0 4px;
  border-left: 3px solid transparent;
}
.hard-1 { background: #fff0f0; border-left-color: #c74343; }
.hard-2 { background: #fff7df; border-left-color: #c28a1d; }
.rmc-source-panel {
  position: sticky;
  top: 72px;
  align-self: start;
}
.rmc-source {
  max-height: calc(100vh - 150px);
}
.source-line {
  display: block;
  margin: 0 -4px;
  padding: 0 4px;
  border-left: 3px solid transparent;
  line-height: inherit;
  min-height: 1.45em;
}
.source-line.active.recovery-good {
  background: #eaf7ef;
  border-left-color: #2f9b5f;
}
.source-line.active.recovery-mid {
  background: #fff8df;
  border-left-color: #c99a22;
}
.source-line.active.recovery-bad {
  background: #fff0f0;
  border-left-color: #c74343;
}
.control-records td,
.control-records th {
  font-size: 13px;
}
.control-row.recovery-good td:first-child {
  border-left: 4px solid #2f9b5f;
}
.control-row.recovery-mid td:first-child {
  border-left: 4px solid #c99a22;
}
.control-row.recovery-bad td:first-child {
  border-left: 4px solid #c74343;
}
.recovery-badge {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding: 2px 8px;
  border-radius: 999px;
  font-weight: 700;
}
.recovery-badge.recovery-good {
  color: #155d37;
  background: #dff2e7;
}
.recovery-badge.recovery-mid {
  color: #76530d;
  background: #fff1bf;
}
.recovery-badge.recovery-bad {
  color: #8d2525;
  background: #ffe0e0;
}
.recovery-badge.recovery-missing {
  color: var(--muted);
  background: #edf1f4;
}
.evidence-note { margin-top: 12px; }
.patch-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 18px;
}
.patch-head h3 {
  margin: 0;
}
.patch-sort {
  appearance: none;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: var(--text);
  padding: 5px 9px;
  font: inherit;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
}
.patch-sort span {
  color: #c74343;
  margin-left: 4px;
}
.patch-card {
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 12px;
  background: #fbfcfd;
}
.patch-card.recovery-good { border-left: 4px solid #2f9b5f; }
.patch-card.recovery-mid { border-left: 4px solid #c99a22; }
.patch-card.recovery-bad { border-left: 4px solid #c74343; }
.patch-card h4 {
  margin: 0 0 6px;
  font-size: 14px;
}
.patch-card details {
  margin: 0;
}
.patch-card summary {
  color: var(--text);
  cursor: pointer;
  font-weight: 700;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 6px 10px;
  align-items: center;
}
.patch-title { overflow-wrap: anywhere; }
.patch-meta {
  grid-column: 1 / -1;
  color: var(--muted);
  font-size: 12px;
  font-weight: 500;
}
.patch-subtitle {
  margin-top: 10px;
  font-size: 13px;
  font-weight: 700;
}
.code-block.patch {
  max-height: 220px;
}
.sample-table td:first-child { min-width: 260px; }
@media (max-width: 760px) {
  main { width: min(100vw - 20px, 1180px); margin-top: 12px; }
  .topbar { padding: 0 14px; }
  .panel { padding: 16px; }
  .panel-head, .grid.two { display: block; }
  .grid.two .panel { margin-bottom: 14px; }
  .feature-diagram-flow { grid-template-columns: 1fr; }
  .cognascore-grid { grid-template-columns: 1fr; }
  .feature-diagram figcaption { display: block; }
  .feature-diagram figcaption small { display: block; margin-top: 4px; }
  .stats { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  dl { grid-template-columns: 1fr; }
}
"""


APP_JS = """
function numericValue(row, key) {
  const raw = row.getAttribute(`data-${key}`) || "";
  if (raw === "") return null;
  const value = Number(raw);
  return Number.isFinite(value) ? value : null;
}

function sortSampleTable(control) {
  const table = control.closest("table");
  if (!table) return;
  const tbody = table.querySelector("tbody");
  const key = control.dataset.sortKey;
  const current = control.dataset.sortDir || "desc";
  const dir = current === "desc" ? -1 : 1;
  const rows = Array.from(tbody.querySelectorAll("tr"));
  rows.sort((left, right) => {
    const a = numericValue(left, key);
    const b = numericValue(right, key);
    if (a === null && b === null) {
      return numericValue(left, "order") - numericValue(right, "order");
    }
    if (a === null) return 1;
    if (b === null) return -1;
    if (a === b) return numericValue(left, "order") - numericValue(right, "order");
    return (a - b) * dir;
  });
  rows.forEach((row) => tbody.appendChild(row));
  table.querySelectorAll(".sort-header").forEach((item) => {
    item.classList.remove("active");
    const marker = item.querySelector("span");
    if (marker) marker.textContent = "↕";
  });
  const indicator = control.querySelector("span");
  if (indicator) indicator.textContent = current === "desc" ? "↓" : "↑";
  control.classList.add("active");
  control.dataset.sortDir = current === "desc" ? "asc" : "desc";
}

function clearSourceHighlights(panel) {
  panel.querySelectorAll(".source-line.active").forEach((line) => {
    line.classList.remove("active", "recovery-good", "recovery-mid", "recovery-bad", "recovery-missing");
  });
}

function highlightMaskLines(detail) {
  const panel = detail.closest(".mode-panel");
  if (!panel) return;
  clearSourceHighlights(panel);
  if (!detail.open) return;
  const status = detail.dataset.status || "recovery-missing";
  const lines = (detail.dataset.lines || "").split(",").filter(Boolean);
  let first = null;
  lines.forEach((lineIndex) => {
    const line = panel.querySelector(`.source-line[data-line="${lineIndex}"]`);
    if (!line) return;
    line.classList.add("active", status);
    if (!first) first = line;
  });
  if (first) {
    first.scrollIntoView({ block: "nearest" });
  }
}

function sortPatchCards(button) {
  const panel = button.closest(".mode-panel");
  if (!panel) return;
  const cards = Array.from(panel.querySelectorAll(".patch-card[data-score]"));
  if (!cards.length) return;
  const target = button.dataset.sortDir || "desc";
  const dir = target === "asc" ? 1 : -1;
  cards.sort((left, right) => {
    const a = Number(left.dataset.score);
    const b = Number(right.dataset.score);
    if (!Number.isFinite(a) && !Number.isFinite(b)) return 0;
    if (!Number.isFinite(a)) return 1;
    if (!Number.isFinite(b)) return -1;
    return (a - b) * dir;
  });
  cards.forEach((card) => card.parentElement.appendChild(card));
  const next = target === "asc" ? "desc" : "asc";
  button.dataset.sortDir = next;
  button.firstChild.textContent = target === "asc" ? "Worst first " : "Best first ";
  const marker = button.querySelector("span");
  if (marker) marker.textContent = target === "asc" ? "↓" : "↑";
}

function updateResultMatrixBest(matrix) {
  const links = Array.from(matrix.querySelectorAll(".result-link[data-score][data-dataset]"));
  links.forEach((link) => link.classList.remove("best"));
  const bestByDataset = new Map();
  links.forEach((link) => {
    const row = link.closest("tr");
    if (row && row.hidden) return;
    const score = Number(link.dataset.score);
    if (!Number.isFinite(score)) return;
    const dataset = link.dataset.dataset;
    const current = bestByDataset.get(dataset);
    if (!current || score > current.score) {
      bestByDataset.set(dataset, { score, link });
    }
  });
  bestByDataset.forEach((item) => item.link.classList.add("best"));
}

function toggleMethodFilter(button) {
  const group = button.dataset.methodGroup;
  const panel = button.closest(".panel");
  if (!group || !panel) return;
  const matrix = panel.querySelector("[data-result-matrix]");
  if (!matrix) return;
  const nextActive = button.getAttribute("aria-pressed") !== "true";
  button.setAttribute("aria-pressed", nextActive ? "true" : "false");
  button.classList.toggle("active", nextActive);
  matrix.querySelectorAll(`tr[data-method-group="${CSS.escape(group)}"]`).forEach((row) => {
    row.hidden = !nextActive;
  });
  updateResultMatrixBest(matrix);
}

function initializeResultMatrices() {
  document.querySelectorAll("[data-result-matrix]").forEach((matrix) => updateResultMatrixBest(matrix));
}

function dragInsertBefore(container, dragging, target, clientX) {
  if (!container || !dragging || !target || dragging === target) return;
  const box = target.getBoundingClientRect();
  const after = clientX > box.left + box.width / 2;
  container.insertBefore(dragging, after ? target.nextSibling : target);
}

function syncMatrixOrderFromFilters(filters) {
  const panel = filters.closest(".panel");
  const matrix = panel ? panel.querySelector("[data-result-matrix]") : null;
  const tbody = matrix ? matrix.querySelector("tbody") : null;
  if (!tbody) return;
  filters.querySelectorAll(".method-filter[data-method-group]").forEach((button) => {
    const group = button.dataset.methodGroup;
    const row = tbody.querySelector(`tr[data-method-group="${CSS.escape(group)}"]`);
    if (row) tbody.appendChild(row);
  });
  updateResultMatrixBest(matrix);
}

document.addEventListener("click", (event) => {
  const methodFilter = event.target.closest(".method-filter[data-method-group]");
  if (methodFilter) {
    if (methodFilter.dataset.dragJustEnded === "true") {
      delete methodFilter.dataset.dragJustEnded;
      return;
    }
    toggleMethodFilter(methodFilter);
    return;
  }
  const patchSort = event.target.closest(".patch-sort");
  if (patchSort) {
    sortPatchCards(patchSort);
    return;
  }
  const button = event.target.closest(".sort-header[data-sort-key]");
  if (button) {
    sortSampleTable(button);
    return;
  }
  const tab = event.target.closest(".mode-tab[data-mode-target]");
  if (!tab) return;
  const panel = tab.closest(".panel");
  panel.querySelectorAll(".mode-tab").forEach((item) => item.classList.remove("active"));
  panel.querySelectorAll(".mode-panel").forEach((item) => item.classList.remove("active"));
  tab.classList.add("active");
  const target = document.getElementById(tab.dataset.modeTarget);
  if (target) target.classList.add("active");
});

document.addEventListener("dragstart", (event) => {
  const button = event.target.closest ? event.target.closest('.method-filter[draggable="true"][data-method-group]') : null;
  if (!button) return;
  button.classList.add("dragging");
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = "move";
    event.dataTransfer.setData("text/plain", button.dataset.methodGroup || "");
  }
});

document.addEventListener("dragover", (event) => {
  const target = event.target.closest ? event.target.closest('.method-filter[draggable="true"][data-method-group]') : null;
  if (!target) return;
  const filters = target.parentElement;
  const dragging = filters ? filters.querySelector(".method-filter.dragging") : null;
  if (!dragging) return;
  event.preventDefault();
  dragInsertBefore(filters, dragging, target, event.clientX);
  syncMatrixOrderFromFilters(filters);
});

document.addEventListener("dragend", (event) => {
  const button = event.target.closest ? event.target.closest(".method-filter.dragging") : null;
  if (!button) return;
  const filters = button.closest("[data-method-filters]");
  button.classList.remove("dragging");
  button.dataset.dragJustEnded = "true";
  window.setTimeout(() => {
    delete button.dataset.dragJustEnded;
  }, 0);
  if (filters) syncMatrixOrderFromFilters(filters);
});

document.addEventListener("toggle", (event) => {
  const detail = event.target.closest ? event.target.closest(".mask-detail") : null;
  if (!detail) return;
  highlightMaskLines(detail);
}, true);

document.addEventListener("DOMContentLoaded", initializeResultMatrices);
"""


if __name__ == "__main__":
    main()
