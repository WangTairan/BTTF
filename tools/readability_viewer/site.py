"""Original result-site layout, backed by current archived measurements."""
from __future__ import annotations

import gzip
import csv
import hashlib
import html
import json
import math
import re
from collections import defaultdict
from functools import lru_cache

from .catalog import ORDER, LABELS
from .diagnosis import ROOT
from .source_access import OFFICIAL_SOURCES, source_restricted
from .public_catalog import source_digest, source_lines

METHODS = {
    "posnett": "Posnett", "scalabrino": "Scalabrino",
    "dorn_retrained": "Dorn", "mi_convnet_cr_reproduction": "Mi",
    "lloc_baseline": "LLOC", "dsv4-pro": "DeepSeek V4 Pro",
    "gpt61-sol": "GPT-6.1 Sol",
    "readability_model_consensus11_opencoder_jina": "BTTF",
}
REPRODUCTION_LINKS = {
    'dorn_retrained': (
        ('Reproduction code and instructions', 'https://github.com/WangTairan/BTTF/tree/main/src/methods/dorn'),
    ),
    'mi_convnet_cr_reproduction': (
        ('Reproduction code and instructions', 'https://github.com/WangTairan/BTTF/tree/main/src/methods/mi_convnet_cr'),
    ),
    'scalabrino': (
        ('Official tool download', 'https://dibt.unimol.it/report/readability/files/readability.zip'),
        ('Adapter code and instructions', 'https://github.com/WangTairan/BTTF/tree/main/src/methods/scalabrino'),
    ),
}
DATASET_DESCRIPTIONS = {
    "mbjp": "A development set constructed for this study from Java tasks in MBXP. It contains 17 functionally correct generated programs, each independently rated by two annotators. The target is their mean readability rating on a 1–5 scale.",
    "buse": "The Buse and Weimer dataset contains 100 Java snippets. Each snippet has 121 human readability ratings on a 1–5 scale; the target is their arithmetic mean.",
    "scalabrino": "The Scalabrino dataset contains 200 Java methods, each rated by nine annotators. The target is the mean readability rating on a 1–5 scale.",
    "dorn": "The Dorn dataset contains 360 snippets in Java, Python, and CUDA. Each snippet has 161–267 human ratings; the target is their mean on a 1–5 readability scale.",
    "schnappinger": "The Schnappinger dataset contains 304 Java classes with posterior probabilities over four ordered readability classes. We use the expected readability under this distribution, from 1 (least readable) to 4 (most readable).",
    "jetbrains": "The JetBrains dataset contains 119 Java snippets with 11–31 readable/unreadable votes per snippet. The target is the fraction of readable votes, rather than a majority-vote label.",
    "java_comparative_obfuscation": "A controlled corpus of 100 production-code classes, with 25 each from Apache Kafka, Google Guava, Netty, and Spring Framework. Thirteen transformations are applied independently to each original, producing 1,400 records. Evaluation uses the 896 variants whose source changes, compared with their matched original; these are not human-rated samples.",
    "python_comparative_degradation": "A controlled corpus of 100 production-code classes, with 25 each from Django, Flask, Requests, and attrs. Thirteen transformations are applied independently to each original, producing 1,400 records. Evaluation uses the 920 variants whose source changes, compared with their matched original; these are not human-rated samples.",
}
DATASET_PROCESSING = {
    "mbjp": "The loader converts escaped newlines and quotes in the stored JSON into source text. Readability targets come from the two human ratings, not the high/low generation prompts.",
    "dorn": "Source snippets are read with their original line endings preserved, so visual measurements see the released formatting.",
    "python_comparative_degradation": "The adapter maps Python's base_sample_id to the common group_id field for pairing. Variants receive no artificial scalar severity label; each is compared directly with its original.",
    "java_comparative_obfuscation": "The adapter preserves original–variant groups and transformation identity. Unchanged variants remain in the list but are excluded from response-rate calculations.",
}
escape = html.escape


def method_link(method):
    return f'<a href="/methods/{method}.html">{METHODS[method]}</a>'


def method_row_class(method):
    if method == "readability_model_consensus11_opencoder_jina":
        return ' class="bttf-method"'
    return ' class="cloud-method"' if method in ("dsv4-pro", "gpt61-sol") else ""


def num(value, digits=3):
    if value is None or not math.isfinite(value):
        return 'n/a'
    text = f'{value:.{digits}f}'
    if digits:
        text = text.rstrip('0').rstrip('.')
    return '0' if text == '-0' else text


def score_num(method, value):
    return num(value, 0 if method == 'lloc_baseline' else 2 if method in ('dsv4-pro', 'gpt61-sol') else 3)


def score_scale(method):
    if method == "lloc_baseline":
        return "Logical lines; fewer is more readable"
    if method in ("dsv4-pro", "gpt61-sol"):
        return "0–20; mean of three runs"
    return "0–1; higher is more readable"


def interference_response(items, scores, *, lower_is_better=False):
    """Use the paper evaluator's tolerance rather than strict float ordering."""
    from experiments.main.readability_model.evaluation.evaluate_constructed_variants import ratio_above_zero
    originals = {item.metadata.get("group_id"): item for item in items
                 if item.metadata.get("is_baseline_variant")}
    drops = []
    for item in items:
        original = originals.get(item.metadata.get("group_id"))
        if original is None or item.content == original.content:
            continue
        before, after = scores.get(original.task_id), scores.get(item.task_id)
        if before is not None and after is not None:
            drops.append(after - before if lower_is_better else before - after)
    return ratio_above_zero(drops), len(drops)


def display_text(value):
    """Hide machine-local paths in presentation metadata and error messages."""
    return re.sub(r'''(?<![\w:])(?:/(?:private|Users|home|tmp|var|Volumes|opt|Applications|Library|mnt)(?:/[^\s<>"']*)?|[A-Za-z]:\\[^\s<>"']+)''', '[local file]', str(value))


def measurement_table(detail):
    if not isinstance(detail, dict):
        return '<p class="muted">No additional measurements recorded.</p>'
    rows = []
    for key, value in detail.items():
        if key in {'file_name', 'filename', 'raw_output', 'stdout', 'stderr', 'model_protocol', 'implementation'} or 'path' in key.lower():
            continue
        if value is None or isinstance(value, (dict, list)):
            continue
        label = key.replace("_", " ").capitalize()
        text = num(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else display_text(value)
        rows.append(f'<tr><th>{escape(label)}</th><td>{escape(text)}</td></tr>')
    return '<table class="records measurement-table"><tbody>' + ''.join(rows) + '</tbody></table>' if rows else '<p class="muted">No additional measurements recorded.</p>'


def baseline_feature_analysis(method, detail):
    from .baseline_diagnosis import decompose_baseline
    result = decompose_baseline(method, detail)
    rows = []
    for feature in result['features']:
        contribution = feature['contribution']
        sign = '+' if contribution >= 0 else '−'
        color = 'benefit' if contribution >= 0 else 'penalty'
        rows.append(f'<tr><td title="{escape(feature["key"])}"><strong>{escape(feature["name"])}</strong><small class="baseline-description">{escape(feature["description"])}</small></td><td>{num(feature["value"])}</td><td class="{color}">{sign}{num(abs(contribution))}</td></tr>')
    return f'''<h3>Feature contributions</h3><table class="records baseline-features"><thead><tr><th>Feature</th><th>Value</th><th>Contribution<br>(log-odds)</th></tr></thead><tbody>{''.join(rows)}</tbody></table>
<p class="score-equation">Intercept {num(result['intercept'])} + feature contributions = {num(result['logit'])} (log-odds).<br>Score = sigmoid({num(result['logit'])}) = {num(result['score'])}.</p>'''


def page(title, body, script="", *, wide=False, parent=("/", "Home")):
    back = f'<a class="header-parent" href="{escape(parent[0])}" aria-label="Back to {escape(parent[1])}">← {escape(parent[1])}</a>' if parent and parent[0] != '/' else ''
    return f"""<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)} · BTTF</title>
<link id="site-icon" rel="icon" type="image/svg+xml" href="/assets/favicon-light.svg">
<meta name="application-name" content="BTTF">
<script src="/assets/theme.js"></script>
<link rel="stylesheet" href="/assets/style.css">
<link rel="stylesheet" href="/assets/diagnosis.css">
<link rel="stylesheet" href="/assets/theme.css">
<script src="/assets/app.js" defer></script>{script}</head><body>
<nav class="topbar{' wide-topbar' if wide else ''}" aria-label="Page navigation"><a class="brand" href="/" aria-label="BTTF home">BTTF</a>{back}<button id="theme-toggle" class="theme-toggle" type="button" aria-label="Switch to dark theme" aria-pressed="false">Dark</button></nav>
<main class="{'wide-comparison' if wide else ''}">{body}</main></body></html>"""


def motivating_example():
    source = '''class MonthOffsets {
    static int offset(int month) {
        int value = "-ilkDwlu2thk5".charAt(month);
        return value % 7;
    }
}
'''
    with (ROOT / "figures/data/opaque_month_offset_motivation.csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    digest = hashlib.sha256(source.encode()).hexdigest()
    if any(row["source_sha256"] != digest for row in rows):
        raise ValueError("Motivating example measurements do not match source")
    code = escape(source).replace('&quot;-ilkDwlu2thk5&quot;.charAt(month)',
                                 '<mark>&quot;-ilkDwlu2thk5&quot;.charAt(month)</mark>')
    for keyword in ("class", "static", "int", "return"):
        code = code.replace(keyword + " ", f'<span class="example-keyword">{keyword}</span> ')
    bars = []
    for row in [r for r in rows if r["kind"] == "model"] + [r for r in rows if r["kind"] == "human"]:
        value = float(row["readability_percentile"])
        label = {"deepseek_v4_pro": "DeepSeek V4 Pro", "mi_convnet_cr": "Mi", "human_developers": "Human"}.get(row["key"], row["label"])
        cls = "example-human" if row["kind"] == "human" else "example-frontier" if row["key"] in {"ours", "deepseek_v4_pro"} else ""
        if row["key"] == "ours":
            cls += " example-bttf"
        bars.append(f'<div class="example-score {cls}"><span>{escape(label)}</span><div class="example-track"><i style="width:{value:.4f}%"></i></div><span>{value:.1f}</span></div>')
    triggers = [
        ("llm__assignment_value_surprisal", "Assignment-value surprisal", '"-ilkDwlu2thk5".charAt(month)'),
        ("llm__literal_tail_surprisal", "Literal-tail surprisal", '"-ilkDwlu2thk5"'),
        ("llm__declaration_surprisal_variation", "Declaration-surprisal variation", "int value = ..."),
        ("llm__identifier_onset_surprisal", "Identifier-onset surprisal", "value"),
    ]
    contributions = {r["key"]: float(r["contribution"]) for r in rows if r["kind"] == "feature"}
    triggers.sort(key=lambda entry: abs(contributions[entry[0]]), reverse=True)
    cards = ''.join(f'<div class="example-trigger"><div><strong>{label}</strong><span>{num(contributions[key])}</span></div><code>{escape(region)}</code></div>' for key, label, region in triggers)
    return f'''<section class="panel"><h2>Motivating example</h2>
<p class="table-description">A month-offset lookup adapted from Sakamoto’s compact day-of-week algorithm. All five developers rated it 1/5, yet four traditional models place it above the 74th percentile.</p>
<div class="example-grid"><div><h3>A lookup hidden in a string</h3><pre class="example-code"><code>{code}</code></pre></div>
<div><h3>Relative readability</h3>{''.join(bars)}<p class="figure-note">Model percentiles over the human-rated benchmark pool; lower is less readable. Human 1/5 is mapped to 0. DeepSeek averages five judgements.</p></div></div>
<h3>Largest BTTF penalties and their source regions</h3><div class="example-triggers">{cards}</div></section>'''


class ResultSite:
    def __init__(self, catalog):
        self.catalog = catalog

    @lru_cache(maxsize=8)
    def scores(self, dataset):
        bundle = self.catalog.dataset(dataset)
        hashes = {item.task_id: source_digest(item)
                  for item in bundle["items"]}
        scores, details = {}, {}
        for key in METHODS:
            if key in ("dsv4-pro", "gpt61-sol"):
                runs, explanations, records = defaultdict(list), defaultdict(list), defaultdict(list)
                for path in sorted((ROOT / "results/direct_llm" / key).glob("run_*.jsonl.gz")):
                    with gzip.open(path, "rt") as stream:
                        for line in stream:
                            row = json.loads(line)
                            task = row["task_id"]
                            if row["dataset"] != dataset or row["source_sha256"] != hashes.get(task):
                                continue
                            value = row.get("llm_readability_score")
                            if value is not None:
                                runs[task].append(float(value))
                            if row.get("explanation"):
                                explanations[task].append(row["explanation"])
                                records[task].append(row)
                scores[key] = {task: sum(values) / len(values) for task, values in runs.items()
                               if len(values) == 3}
                details[key] = {task: {"explanations": values, "runs": sorted(records[task], key=lambda row: row['run'])}
                                for task, values in explanations.items()}
            else:
                paths = sorted((ROOT / "results/methods" / key / dataset).rglob("summary.json"))
                if not paths:
                    observed = {task: row['methods'][key] for task, row in bundle['published'].items()
                                if key in row['methods'] and row['source_sha256'] == hashes.get(task)}
                    scores[key] = {task: row['score'] for task, row in observed.items()}
                    details[key] = {task: row['detail'] for task, row in observed.items()}
                    continue
                summary = json.loads(paths[0].read_text())
                rows = summary.get("results", [])
                scores[key] = {row["task_id"]: row.get("score") for row in rows
                               if row["task_id"] in hashes}
                details[key] = {row["task_id"]: row.get("result", {}) for row in rows}
        # The diagnostic predictor is the published frozen 11-feature model.
        bttf = "readability_model_consensus11_opencoder_jina"
        scores[bttf] = {}
        from .diagnosis import decompose
        for item in bundle["items"]:
            values = self.catalog.cached_values(dataset, item)
            if values is not None:
                scores[bttf][item.task_id] = decompose(values)["score"]
        return scores, details

    def home(self):
        from scipy.stats import spearmanr
        datasets = self.catalog.datasets()
        header = "".join(f'<th data-dataset-column="{d["key"]}"><a href="/datasets/{d["key"]}.html">{d["name"]}</a></th>'
                         for d in datasets if d["kind"] == "human-rated")
        rows = []
        for method, label in METHODS.items():
            cells = []
            for d in datasets:
                if d["kind"] != "human-rated":
                    continue
                items = self.catalog.dataset(d["key"])["items"]
                scores = self.scores(d["key"])[0].get(method, {})
                pairs = [(scores[i.task_id], i.readability_score) for i in items
                         if scores.get(i.task_id) is not None and i.readability_score is not None]
                rho = float(spearmanr(*zip(*pairs)).statistic) if len(pairs) > 1 else None
                attrs = f' data-score="{rho}" data-dataset="{d["key"]}"' if rho is not None and math.isfinite(rho) else ""
                cells.append(f'<td data-dataset-column="{d["key"]}"><a class="result-link"{attrs} href="/datasets/{d["key"]}.html">'
                             f'<strong>{num(rho)}</strong>'
                             f'<small>{len(pairs)}/{len(items)}</small></a></td>')
            rows.append(f'<tr{method_row_class(method)} data-method-group="{method}"><th>{method_link(method)}</th>{"".join(cells)}</tr>')
        filters = "".join(f'<label class="filter-check"><input type="checkbox" '
                          f'data-method-filter="{key}" checked>{label}</label>'
                          for key, label in METHODS.items())
        dataset_filters = "".join(f'<label class="filter-check"><input type="checkbox" '
                                 f'data-dataset-filter="{d["key"]}" checked>{d["name"]}</label>' for d in datasets if d["kind"] == "human-rated")
        controlled_filters = "".join(f'<label class="filter-check"><input type="checkbox" '
                                    f'data-dataset-filter="{d["key"]}" checked>{d["name"].split()[0]}</label>' for d in datasets if d["kind"] == "controlled")
        body = f"""<section class="panel"><div class="panel-head"><div>
<h1>Code Readability Results</h1></div></div>
<p class="table-description">Spearman correlation between predicted scores and human ratings, computed separately for each dataset. Counts show evaluated samples / total samples.</p>
<div class="matrix-wrap"><table class="matrix" data-result-matrix>
<thead><tr><th>Method / Dataset</th>{header}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>
<div class="table-filters"><div class="filter-row" role="group" aria-label="Methods"><span class="filter-label">Methods</span><div class="filter-options">{filters}</div></div>
<div class="filter-row" role="group" aria-label="Datasets"><span class="filter-label">Datasets</span><div class="filter-options">{dataset_filters}</div></div></div>
</section>"""
        dataset_section = '<section class="panel"><h2>Datasets and samples</h2><table class="records"><thead><tr><th>Dataset</th><th>Samples</th><th>Evaluation</th><th>Download</th></tr></thead><tbody>'
        for d in datasets:
            download = (f'<a href="{OFFICIAL_SOURCES[d["key"]]}">Official source</a>'
                        if source_restricted(d['key']) else f'<a href="/downloads/{d["key"]}.json" download>JSON</a>')
            dataset_section += f'<tr data-dataset-row="{d["key"]}"><td><a href="/datasets/{d["key"]}.html">{d["name"]}</a></td><td>{d["count"]}</td><td>{d["kind"]}</td><td>{download}</td></tr>'
        dataset_section += "</tbody></table></section>"
        body += '<section class="panel"><h2>Independent Readability Interferences</h2><p class="table-description">Percentage of changed variants scored less readable than their matched original, reported separately for Java and Python. Counts show evaluated changed pairs.</p><div class="matrix-wrap"><table class="records" data-result-matrix><thead><tr><th>Method</th><th data-dataset-column="java_comparative_obfuscation">Java</th><th data-dataset-column="python_comparative_degradation">Python</th></tr></thead><tbody>'
        for method, label in METHODS.items():
            cells = []
            for dataset in ORDER[-2:]:
                items = self.catalog.dataset(dataset)["items"]
                scores = self.scores(dataset)[0].get(method, {})
                rate, total = interference_response(items, scores, lower_is_better=method == "lloc_baseline")
                text = f'<strong>{100 * rate:.1f}%</strong><small>{total} valid pairs</small>' if total else 'n/a'
                attrs = f' data-score="{rate}" data-dataset="{dataset}"' if total else ''
                cells.append(f'<td data-dataset-column="{dataset}"><a class="result-link"{attrs} href="/datasets/{dataset}.html">{text}</a></td>')
            body += f'<tr{method_row_class(method)} data-method-group="{method}"><th>{method_link(method)}</th>{"".join(cells)}</tr>'
        body += '</tbody></table></div><div class="table-filters"><div class="filter-row" role="group" aria-label="Methods"><span class="filter-label">Methods</span><div class="filter-options">' + filters + '</div></div><div class="filter-row" role="group" aria-label="Languages"><span class="filter-label">Languages</span><div class="filter-options">' + controlled_filters + '</div></div></div></section>'
        explanation_module = '<section class="panel"><h2><a href="/explainability.html">Explainability analysis</a></h2><p class="table-description">LLM explanations and BTTF feature contributions for 30 randomly sampled programs.</p></section>'
        return page("Results", body + motivating_example() + explanation_module + dataset_section, parent=None)

    @lru_cache(maxsize=1)
    def explanation_samples(self):
        from .explainability import sample_explanations
        return sample_explanations(self.catalog)

    @lru_cache(maxsize=6)
    def human_targets(self, dataset):
        import pandas as pd
        from src.methods.readability_model.runners.supervised_ridge import regression_target
        items = self.catalog.dataset(dataset)['items']
        return regression_target(pd.DataFrame({'dataset': [dataset] * len(items),
                                              'readability_score': [item.readability_score for item in items]}))

    @lru_cache(maxsize=8)
    def score_ranks(self, dataset):
        from scipy.stats import rankdata
        scores, _ = self.scores(dataset)
        result = {}
        for method, values in scores.items():
            observed = [(task, float(value)) for task, value in values.items()
                        if value is not None and math.isfinite(float(value))]
            direction = -1 if method == 'lloc_baseline' else 1
            ranks = rankdata([direction * value for _, value in observed], method='average')
            result[method] = {task: 100 * (rank - 1) / max(len(observed) - 1, 1)
                              for (task, _), rank in zip(observed, ranks)}
        return result

    def sample_scores_table(self, dataset, index, methods=None):
        item = self.catalog.dataset(dataset)['items'][index]
        scores, _ = self.scores(dataset)
        human_rated = dataset in ORDER[:6]
        ranks = self.score_ranks(dataset) if human_rated else {}
        human_rank = 100 * float(self.human_targets(dataset)[index]) if human_rated else None

        def rank_cell(value, human=False):
            distance = abs(value - human_rank)
            color = 'var(--human-marker, #30363c)' if human else f'hsl({120 * max(0, 1 - distance / 50):.1f}, 70%, var(--rank-lightness, 34%))'
            delta = '' if human else f'<small>Δ {distance:.1f}</small>'
            return f'<td class="rank-comparison" title="Percentile {value:.1f}; human percentile {human_rank:.1f}"><div class="rank-comparison-values"><strong style="color:{color}">{value:.1f}</strong>{delta}</div><div class="rank-comparison-track"><i class="human-rank-marker" style="left:{human_rank:.4f}%"></i><i class="model-rank-marker" style="left:{value:.4f}%;background:{color}"></i></div></td>'

        rows = []
        for method in methods or METHODS:
            value = scores.get(method, {}).get(item.task_id)
            if value is None:
                continue
            comparison = rank_cell(ranks[method][item.task_id]) if human_rated else ''
            rows.append(f'<tr{method_row_class(method)}><td>{METHODS[method]}</td><td>{score_num(method, value)}</td><td>{score_scale(method)}</td>{comparison}</tr>')
        reference = ''
        caption = ''
        if human_rated:
            scale = '0–1' if dataset == 'jetbrains' else '1–4' if dataset == 'schnappinger' else '1–5'
            reference = f'<tbody class="human-reference"><tr><td>Human</td><td>{num(item.readability_score, 2)}</td><td>{scale}; original rating</td>{rank_cell(human_rank, human=True)}</tr></tbody>'
        rank_help = 'Within this dataset, each method’s valid scores are ranked and scaled to 0–100: 100 × (average rank − 1) / (count − 1). Ties share a rank; LLOC is reversed. Human uses the paper’s within-dataset target (binary labels stay 0/100). Δ is the absolute difference between model and human ranks.'
        header = f'<th>Dataset rank<br>(0–100) <button class="help-marker" type="button" aria-label="How dataset ranks are computed" title="{escape(rank_help)}">?</button></th>' if human_rated else ''
        return f'<div class="matrix-wrap"><table class="records sample-scores"><thead><tr><th>Method</th><th>Score</th><th>Scale</th>{header}</tr></thead><tbody>{"".join(rows)}</tbody>{reference}</table></div>{caption}'

    def explainability_page(self, review_id=None):
        samples = self.explanation_samples()
        if review_id is not None:
            sample = next((row for row in samples if row['review_id'] == review_id), None)
            if sample is None:
                raise ValueError('Unknown explanation example')
            return self.explanation_example(sample, samples)
        model_runs = {'gpt61-sol': [sample['runs'] for sample in samples],
                      'dsv4-pro': [self.scores(sample['dataset'])[1]['dsv4-pro'][sample['task_id']]['runs'] for sample in samples]}
        consistency = []
        for model, records in model_runs.items():
            if any([run['run'] for run in runs] != [1, 2, 3] for runs in records):
                raise ValueError('Score consistency requires three complete runs per sample')
            same = sum(len({run['llm_readability_score'] for run in runs}) == 1 for runs in records)
            ranges = [max(run['llm_readability_score'] for run in runs) - min(run['llm_readability_score'] for run in runs) for runs in records]
            consistency.append(f'<tr><th>{METHODS[model]}</th><td>{same}/{len(samples)} ({100 * same / len(samples):.1f}%)</td><td>{sum(ranges) / len(ranges):.2f}</td><td>{max(ranges):g}</td></tr>')
        rows = []
        for position, sample in enumerate(samples):
            scores = ' / '.join(num(run['llm_readability_score'], 2) for run in sample['runs'])
            mean_score = sum(run['llm_readability_score'] for run in sample['runs']) / len(sample['runs'])
            ds_runs = model_runs['dsv4-pro'][position]
            ds_scores = ' / '.join(num(run['llm_readability_score'], 2) for run in ds_runs)
            ds_mean = sum(run['llm_readability_score'] for run in ds_runs) / len(ds_runs)
            human = self.catalog.dataset(sample['dataset'])['items'][sample['index']].readability_score
            human_target = float(self.human_targets(sample['dataset'])[sample['index']])
            scale = '0–1' if sample['dataset'] == 'jetbrains' else '1–4' if sample['dataset'] == 'schnappinger' else '1–5'
            ranks = self.score_ranks(sample['dataset'])
            gaps = ' '.join(f'data-gap-{key}="{abs(ranks[method][sample["task_id"]] - 100 * human_target)}"'
                            for key, method in [('gpt', 'gpt61-sol'), ('ds', 'dsv4-pro'), ('bttf', 'readability_model_consensus11_opencoder_jina')])
            rows.append(f'<tr {gaps} data-order="{position}" data-dataset-order="{ORDER.index(sample["dataset"])}" data-score-gpt="{mean_score}" data-score-ds="{ds_mean}" data-score-bttf="{sample["bttf"]["score"]}" data-human="{human_target}"><td><a class="sample-id-link" title="{escape(sample["task_id"])}" href="/explainability/{sample["review_id"]}.html">{sample["review_id"]} · {escape(sample["task_id"])}</a></td><td>{LABELS[sample["dataset"]]}</td><td>{scores}</td><td>{ds_scores}</td><td>{num(sample["bttf"]["score"])}</td><td title="Original human rating: {num(human, 2)} ({scale})">{num(human_target)}</td></tr>')
        body = f'''<section class="panel"><h1>Explainability analysis</h1>
<p class="table-description">30 programs randomly sampled from the 1,100 human-rated samples; seed 42.</p></section>
<section class="panel"><h2>Score consistency across runs</h2><p class="table-description">Three runs per sample · 0–20 scale</p><div class="matrix-wrap"><table class="records"><thead><tr><th>Model</th><th>Identical scores</th><th title="Mean maximum minus minimum across three runs">Mean score range</th><th title="Largest maximum minus minimum across three runs">Maximum score range</th></tr></thead><tbody>{''.join(consistency)}</tbody></table></div></section>
<section class="panel"><h2>Sampled examples</h2><div class="matrix-wrap"><table class="records explanation-sample-table" data-sortable-samples><thead><tr>
<th><button class="sort-header" data-sort-key="order" data-sort-dir="desc">Example <span>↕</span></button></th>
<th><button class="sort-header" data-sort-key="dataset-order" data-sort-dir="desc">Dataset <span>↕</span></button></th>
<th><button class="sort-header" data-sort-key="score-gpt" data-gap-key="gap-gpt" data-sort-dir="desc" title="Sort by the mean of three scores; Δ sorts by human percentile gap">GPT-6.1 Sol <span>↕</span></button><br>Runs 1 / 2 / 3</th>
<th><button class="sort-header" data-sort-key="score-ds" data-gap-key="gap-ds" data-sort-dir="desc" title="Sort by the mean of three scores; Δ sorts by human percentile gap">DeepSeek V4 Pro <span>↕</span></button><br>Runs 1 / 2 / 3</th>
<th><button class="sort-header" data-sort-key="score-bttf" data-gap-key="gap-bttf" data-sort-dir="desc" title="Δ sorts by human percentile gap">BTTF (0–1) <span>↕</span></button></th>
<th><button class="sort-header" data-sort-key="human" data-sort-dir="desc" title="Within-dataset percentile rank, as used in the paper">Human (0–1) <span>↕</span></button></th>
</tr></thead><tbody>{''.join(rows)}</tbody></table></div></section>'''
        return page('Explainability analysis', body)

    def explanation_example(self, sample, samples):
        dataset, index = sample['dataset'], sample['index']
        _, details = self.scores(dataset)
        explanation_panels = []
        for model, runs in [('gpt61-sol', sample['runs']), ('dsv4-pro', details.get('dsv4-pro', {}).get(sample['task_id'], {}).get('runs', []))]:
            cards = []
            for run in runs:
                text = escape(run['explanation'])
                for heading in ('Code Structure:', 'Nesting:', 'Clarity of intent:', 'Code length:', 'Action granularity:', 'Reading flow:'):
                    text = text.replace(heading, f'</p><p><strong>{heading}</strong>')
                opened = ' open' if run['run'] == 1 else ''
                cards.append(f'<details class="explanation-run"{opened}><summary>Run {run["run"]} · {num(run["llm_readability_score"], 2)}/20</summary><p>{text}</p></details>')
            hidden = ' hidden' if model != 'gpt61-sol' else ''
            explanation_panels.append(f'<div data-explanation-model="{model}"{hidden}><h2>{METHODS[model]} explanations</h2><div class="comparison-scroll">{"".join(cards)}</div></div>')
        result = sample['bttf']
        body = f'''<section class="panel"><h1>{sample['review_id']} · {escape(sample['task_id'])}</h1><p><a href="/samples/{dataset}/{index}.html">Full sample results</a></p></section>
<section class="panel"><h2>Scores</h2>{self.sample_scores_table(dataset, index, ['gpt61-sol', 'dsv4-pro', 'readability_model_consensus11_opencoder_jina'])}</section>
<section class="panel"><div id="mode-bttf" data-dataset="{dataset}" data-index="{index}"><div class="explanation-model-picker" role="radiogroup" aria-label="Explanation model"><label><input type="radio" name="explanation-model" value="gpt61-sol" checked> GPT-6.1 Sol</label><label><input type="radio" name="explanation-model" value="dsv4-pro"> DeepSeek V4 Pro</label></div><p id="status">Loading feature diagnosis…</p>
<div class="explanation-comparison">
<article class="comparison-column"><h2>Source code</h2><div id="code" class="diagnostic-code"></div><div id="plain-code" hidden></div></article>
<article class="comparison-column">{''.join(explanation_panels)}</article>
<article class="comparison-column"><h2>BTTF feature contributions</h2><p class="comparison-score">Score {num(result['score'])} / 1</p><div class="feature-list-scroll"><div id="features"></div></div>
<div class="selected-feature-detail" aria-live="polite"><strong id="selected-name"></strong><p id="description"></p><p id="equation"></p></div>
</article>
</div></div></section>'''
        return page(sample['task_id'], body, '<script src="/assets/diagnosis.js" defer></script>', wide=True, parent=('/explainability.html', 'Explainability analysis'))

    def method_page(self, method):
        if method not in METHODS:
            raise ValueError("Unknown method")
        descriptions = {
            "posnett": "The published three-feature model of Posnett et al. uses source lines, Halstead volume, and byte entropy. We apply its original coefficients without retraining and use the predicted probability of readable code as the score.",
            "scalabrino": "The comprehensive model of Scalabrino et al. combines structural, textual, and visual features. We call the authors' released Java archive and pretrained classifier through a local adapter, wrapping method snippets in a minimal class where required. The published features and scoring logic are unchanged. Unsupported or failed samples are omitted.",
            "dorn_retrained": "We reconstruct the Dorn model from the public feature data and released visual-metric implementations. Metrics available for fewer than 80% of training samples are excluded; forward selection retains seven features, and logistic regression is fitted on all 360 Dorn samples. A thin adapter selects the appropriate language analyzer without changing metric formulas or wrapping Java snippets. The score is the readable-class probability.",
            "mi_convnet_cr_reproduction": "Our reproduction of Mi et al.'s character-level ConvNetCR branch, not the complete DeepCRM model. It is trained on the highest and lowest readability quartiles of Buse, the Java subset of Dorn, and Scalabrino. The score is the readable-class probability.",
            "readability_model_consensus11_opencoder_jina": "BTTF combines four traditional code measurements, two embedding-based measurements of semantic organization, and five causal-LM predictability measurements in a Ridge predictor. The 11 features are selected through stability analysis and consensus across 15 pretrained-model combinations. This viewer uses OpenCoder-1.5B-Base and Jina Embeddings v2 Base Code.",
            "lloc_baseline": "Logical lines of code count statement and declaration nodes in the source AST, excluding comments and blank lines. Java and Python use their respective grammars; C, C++, and CUDA use the C++ grammar. Lower counts are treated as higher readability in controlled comparisons.",
            "dsv4-pro": "DeepSeek-V4-Pro-0813 directly evaluates each source sample using the developer-guided zero-shot prompt adopted from Ouédraogo et al. The prompt covers structure, nesting, intent, length, action granularity, and reading flow. Scores average three independent runs, without tools or an agentic workflow; recorded explanations appear on sample pages.",
            "gpt61-sol": "GPT-6.1 Sol uses the same developer-guided zero-shot prompt adopted from Ouédraogo et al., covering structure, nesting, intent, length, action granularity, and reading flow. It uses low reasoning effort and no tools or agentic workflow. Scores average three independent runs; recorded explanations appear on sample pages.",
        }
        from scipy.stats import spearmanr
        rows = []
        for dataset in self.catalog.datasets():
            items = self.catalog.dataset(dataset["key"])["items"]
            scores = self.scores(dataset["key"])[0].get(method, {})
            valid = [item for item in items if scores.get(item.task_id) is not None]
            metric = "—"
            if dataset["kind"] == "human-rated":
                pairs = [(scores[item.task_id], item.readability_score) for item in valid if item.readability_score is not None]
                rho = float(spearmanr(*zip(*pairs)).statistic) if len(pairs) > 1 else None
                metric = num(rho)
            rows.append(f'<tr><td><a href="/datasets/{dataset["key"]}.html">{dataset["name"]}</a></td><td>{len(valid)}/{len(items)}</td><td>{metric}</td></tr>')
        body = f'<section class="panel"><p class="eyebrow">Method</p><h1>{METHODS[method]}</h1><p>{descriptions[method]}</p><p class="muted">Score scale: {score_scale(method)}.</p></section>'
        if method in REPRODUCTION_LINKS:
            links = ' · '.join(f'<a href="{url}">{label}</a>' for label, url in REPRODUCTION_LINKS[method])
            body = body.removesuffix('</section>') + f'<p>{links}</p></section>'
        if method == "readability_model_consensus11_opencoder_jina":
            body += '<section class="panel"><h2>Evaluation in this viewer</h2><p>Training uses within-dataset percentile targets and equal total weight for each dataset. Inference applies the fitted imputation, training-range clipping, standardization, and Ridge coefficients. This viewer uses the fixed diagnostic model, not CV/LODO predictions. Cloud scores average three runs.</p></section>'
            from .diagnosis import decompose
            manifest = self.catalog.manifest
            features = decompose(dict(zip(manifest["features"]["ordered_names"], manifest["pipeline"]["imputer_statistics"])), manifest)["features"]
            body += '<section class="panel"><h2>Selected features</h2><table class="records"><thead><tr><th>Feature</th><th>Measurement</th></tr></thead><tbody>'
            body += ''.join(f'<tr><th>{escape(f["name"])}</th><td>{escape(f["description"])}</td></tr>' for f in features)
            body += '</tbody></table></section>'
        body += '<section class="panel"><h2>Dataset results</h2><table class="records"><thead><tr><th>Dataset</th><th>Coverage</th><th>Spearman ρ</th></tr></thead><tbody>' + ''.join(rows) + '</tbody></table></section>'
        return page(METHODS[method], body)

    def dataset_page(self, dataset):
        bundle = self.catalog.dataset(dataset)
        scores, _ = self.scores(dataset)
        methods = [key for key in METHODS if any(v is not None for v in scores.get(key, {}).values())]
        controlled = dataset in ORDER[-2:]
        ranks = self.score_ranks(dataset) if not controlled else {}
        human_targets = self.human_targets(dataset) if not controlled else []
        processing = f'<p class="muted wide">{escape(DATASET_PROCESSING[dataset])}</p>' if dataset in DATASET_PROCESSING else ''
        def header(label, key):
            gap = f' data-gap-key="gap-{key[6:]}" title="Δ sorts by human percentile gap"' if key.startswith('score-') and not controlled else ''
            return f'<th><button class="sort-header" data-sort-key="{key}"{gap} data-sort-dir="desc">{label} <span>↕</span></button></th>'
        headings = header("ID", "order") + ("<th>Transformation</th>" if controlled else header("Human", "human"))
        headings += "".join(header(METHODS[m], f"score-{m}") for m in methods) + header("Lines", "code-lines")
        rows = []
        for index, item in enumerate(bundle["items"]):
            attrs = f'data-order="{index}" data-human="{item.readability_score if not controlled else ""}" data-code-lines="{source_lines(item)}"'
            attrs += "".join(f' data-score-{m}="{scores[m].get(item.task_id, "")}"' for m in methods)
            if not controlled:
                for method in methods:
                    rank = ranks[method].get(item.task_id)
                    gap = abs(rank - 100 * float(human_targets[index])) if rank is not None else ''
                    attrs += f' data-gap-{method}="{gap}"'
            id_cell = f'<td class="sample-id-cell"><a class="sample-id-link" title="{escape(item.task_id)}" href="/samples/{dataset}/{index}.html">{escape(item.task_id)}</a></td>'
            if not controlled:
                cells = id_cell + f'<td>{num(item.readability_score, 2)}</td>'
            else:
                cells = id_cell + f'<td>{escape(item.metadata.get("description", item.metadata.get("display_label", "")))}</td>'
            cells += "".join(f'<td>{score_num(m, scores[m].get(item.task_id))}</td>' for m in methods)
            cells += f'<td>{source_lines(item)}</td>'
            rows.append(f'<tr {attrs}>{cells}</tr>')
        download = (f'<a href="{OFFICIAL_SOURCES[dataset]}">Official dataset source</a>'
                    if source_restricted(dataset) else f'<a href="/downloads/{dataset}.json" download>Download dataset (JSON)</a>')
        sample_hint = ('Click a sample ID to inspect its scores. Source code is linked to the official dataset; the fixed 30-case analysis retains source views.'
                       if source_restricted(dataset) else 'Click a sample ID to inspect its code, method scores, and BTTF feature diagnosis.')
        body = f"""<section class="panel"><p class="eyebrow">Dataset</p>
<h1>{LABELS[dataset]}</h1><p>{escape(DATASET_DESCRIPTIONS[dataset])}</p>{processing}<p>{download}</p><div class="stats"><div class="stat"><span>Samples</span>
<strong>{len(bundle["items"])}</strong></div></div></section>
<section class="panel"><div class="panel-head compact"><div><h2>Samples</h2>
<p class="muted">{sample_hint}</p>
</div><input id="sample-search" placeholder="Search sample ID"></div>
<div class="matrix-wrap"><table class="records sample-table {'controlled-samples' if controlled else 'human-samples'}" data-sortable-samples>
<thead><tr>{headings}</tr></thead><tbody>{"".join(rows)}</tbody></table></div></section>"""
        return page(LABELS[dataset], body, '<script src="/assets/list.js" defer></script>')

    def source_visible(self, dataset, index):
        if not source_restricted(dataset):
            return True
        return any(row['dataset'] == dataset and row['index'] == index
                   for row in self.explanation_samples())

    def sample_page(self, dataset, index):
        items = self.catalog.dataset(dataset)["items"]
        if not 0 <= index < len(items):
            raise ValueError("Unknown sample")
        item = items[index]
        visible = self.source_visible(dataset, index)
        source_view = (f'<div id="plain-code" class="diagnostic-code">{escape(item.content)}</div>' if visible
                       else f'<div id="plain-code" class="source-reference"><a href="{OFFICIAL_SOURCES[dataset]}">Official dataset source</a> · {escape(item.task_id)}</div>')
        scores, details = self.scores(dataset)
        controlled = dataset in ORDER[-2:]
        tabs, panels = [], []
        for key, label in METHODS.items():
            if scores.get(key, {}).get(item.task_id) is None:
                continue
            if key == "readability_model_consensus11_opencoder_jina":
                continue
            detail = details.get(key, {}).get(item.task_id, {})
            tabs.append(f'<button class="mode-tab" data-mode-target="mode-{key}">{label}</button>')
            if "explanations" in detail:
                text = "".join(f'<details{" open" if n == 1 else ""}><summary>Run {n}</summary><p>{escape(t)}</p></details>'
                               for n, t in enumerate(detail["explanations"], 1))
            elif key in {'posnett', 'dorn_retrained'}:
                text = baseline_feature_analysis(key, detail)
            else:
                text = measurement_table(detail)
            panels.append(f'<div class="mode-panel" id="mode-{key}">{text}</div>')
        human = "" if controlled else f'<div class="stat"><span>Human</span><strong>{num(item.readability_score, 2)}</strong></div>'
        context = ""
        if controlled:
            context = f'<p>{escape(item.metadata.get("description", ""))}</p>'
            group = item.metadata.get("group_id")
            original = next((i for i, candidate in enumerate(items) if candidate.metadata.get("group_id") == group and candidate.metadata.get("is_baseline_variant")), None)
            if original is not None and original != index:
                context += f'<p><a href="/samples/{dataset}/{original}.html">Matched original source</a></p>'
        else:
            context = '<p class="muted">Human rating uses the original dataset scale.</p>'
        body = f"""<section class="panel"><p class="eyebrow">Sample</p><h1>{escape(item.task_id)}</h1>
{context}
<div class="stats"><div class="stat"><span>Dataset</span><strong><a href="/datasets/{dataset}.html">{LABELS[dataset]}</a></strong></div>{human}
<div class="stat"><span>Lines</span><strong>{source_lines(item)}</strong></div></div></section>
<section class="panel"><h2>Scores</h2>{self.sample_scores_table(dataset, index)}</section>
<section class="panel"><h2>Views</h2><div class="mode-tabs">
<button class="mode-tab active" data-mode-target="mode-bttf">BTTF diagnosis</button>{"".join(tabs)}</div>
<div class="method-views bttf-view"><article class="persistent-source"><h3>Source code</h3>{source_view}</article>
<div class="mode-panel active" id="mode-bttf" data-dataset="{dataset}" data-index="{index}">
<p id="status">Loading feature diagnosis…</p><div class="grid two diagnosis-grid">
<article><h3>Source regions</h3><div id="code" class="diagnostic-code"></div></article>
<article><h3>Feature contributions</h3><div class="feature-list-scroll"><div id="features"></div></div><div class="selected-feature-detail" aria-live="polite"><strong id="selected-name"></strong><p id="description"></p><p id="equation"></p></div></article></div>
</div>{"".join(panels)}</div></section>"""
        return page(item.task_id, body, '<script src="/assets/diagnosis.js" defer></script>', parent=(f'/datasets/{dataset}.html', LABELS[dataset]))
