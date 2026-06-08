import html
import json
from pathlib import Path
from typing import Any, Dict, List, Sequence

from .types import ComplexityResult, MaskConstraints


def result_to_dict(
    result: ComplexityResult,
    source_path: str,
    model_name: str,
    constraints: MaskConstraints,
    source_lines: Sequence[str],
    line_numbering: str = "cleaned_non_blank_1_based",
) -> Dict[str, Any]:
    return {
        "source_path": source_path,
        "model": model_name,
        "source_lines": list(source_lines),
        "line_numbering": line_numbering,
        "constraints": {
            "nmin": constraints.nmin,
            "nmax": constraints.nmax,
            "lmin": constraints.lmin,
            "lmax": constraints.lmax,
        },
        "summary": {
            "score": result.score,
            "mask_count": len(result.masks),
            "profile_count": len(result.profile),
        },
        "masks": [
            {
                "index": mask.index if mask.index is not None else index,
                "granularity": mask.granularity,
                "masked_segments": mask.masked_segments,
                "selected_segments": mask.selected_segments,
                "strategy": mask.strategy,
                "node_type": mask.node_type,
                "char_start": mask.char_start,
                "char_end": mask.char_end,
                "token_count": mask.token_count,
                "ast_role": mask.ast_role,
                "ast_granularity": mask.ast_granularity,
                "node_types": list(mask.node_types),
                "ast_roles": list(mask.ast_roles),
                "char_spans": [
                    {"start": start, "end": end}
                    for start, end in mask.char_spans
                ],
                "stratum_total": mask.stratum_total,
                "stratum_sampled": mask.stratum_sampled,
                "sampling_seed": mask.sampling_seed,
                "spans": [
                    {"start": span.start, "end": span.end, "length": span.length}
                    for span in mask.spans
                ],
                "masked_text": mask.text,
                "masked_code": mask.text,
            }
            for index, mask in enumerate(result.masks)
        ],
        "recoveries": [
            {
                "index": (
                    item.masked.index if item.masked.index is not None else index
                ),
                "similarity": item.similarity,
                "score": item.similarity,
                "spans": [
                    {"start": span.start, "end": span.end, "length": span.length}
                    for span in item.masked.spans
                ],
                "strategy": item.masked.strategy,
                "node_type": item.masked.node_type,
                "char_start": item.masked.char_start,
                "char_end": item.masked.char_end,
                "token_count": item.masked.token_count,
                "ast_role": item.masked.ast_role,
                "ast_granularity": item.masked.ast_granularity,
                "node_types": list(item.masked.node_types),
                "ast_roles": list(item.masked.ast_roles),
                "char_spans": [
                    {"start": start, "end": end}
                    for start, end in item.masked.char_spans
                ],
                "stratum_total": item.masked.stratum_total,
                "stratum_sampled": item.masked.stratum_sampled,
                "sampling_seed": item.masked.sampling_seed,
                "masked_text": item.masked.text,
                "masked_code": item.masked.text,
                "expected_text": item.expected,
                "expected_source": item.expected,
                "recovered_text": item.completion,
                "recovered_code": item.completion,
                "llm_answer": item.recovered,
                "alignment_failed": item.alignment_failed,
                "extraction_failed": item.extraction_failed,
                "expected_mask_count": item.expected_mask_count,
                "recovered_mask_count": item.recovered_mask_count,
                "mask_count_mismatch": item.mask_count_mismatch,
            }
            for index, item in enumerate(result.profile)
        ],
    }


def write_json_report(data: Dict[str, Any], path: Path) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def write_html_report(data: Dict[str, Any], path: Path) -> None:
    path.write_text(render_html_report(data), encoding="utf-8")


def render_html_report(data: Dict[str, Any]) -> str:
    recoveries = data["recoveries"]
    summary = data["summary"]
    source_lines = data["source_lines"]
    recovery_blocks = _render_recovery_blocks(recoveries, source_lines)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Recursive Masking Complexity Report</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f7f7f4;
      --panel: #ffffff;
      --ink: #1e2329;
      --muted: #667085;
      --line: #d8d8d0;
      --accent: #0f766e;
      --accent-soft: #d7f2ee;
      --code: #111827;
    }}
    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: var(--bg);
      color: var(--ink);
    }}
    header {{
      padding: 28px 36px 18px;
      border-bottom: 1px solid var(--line);
      background: var(--panel);
    }}
    h1 {{
      margin: 0 0 10px;
      font-size: 26px;
      letter-spacing: 0;
    }}
    h2 {{
      margin: 30px 0 14px;
      font-size: 19px;
      letter-spacing: 0;
    }}
    main {{
      max-width: 1180px;
      margin: 0 auto;
      padding: 24px 28px 48px;
    }}
    .meta {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      color: var(--muted);
      font-size: 14px;
    }}
    .stats {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
      gap: 12px;
      margin-top: 18px;
    }}
    .stat {{
      border: 1px solid var(--line);
      background: var(--panel);
      padding: 14px;
      border-radius: 8px;
    }}
    .stat strong {{
      display: block;
      font-size: 24px;
      margin-top: 4px;
    }}
    .block {{
      border: 1px solid var(--line);
      background: var(--panel);
      border-radius: 8px;
      margin-bottom: 14px;
      overflow: hidden;
    }}
    .block-title {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      padding: 11px 14px;
      background: #fbfbf8;
      border-bottom: 1px solid var(--line);
      color: var(--muted);
      font-size: 14px;
    }}
    pre {{
      margin: 0;
      padding: 14px;
      overflow: auto;
      color: var(--code);
      font: 13px/1.45 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      white-space: pre-wrap;
    }}
    .code-view {{
      max-height: 520px;
      overflow: auto;
      padding: 10px 0;
      background: #fcfcfa;
      color: var(--code);
      font: 13px/1.45 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    }}
    .code-line {{
      display: grid;
      grid-template-columns: 48px minmax(0, 1fr);
      min-height: 20px;
      padding: 0 14px 0 0;
    }}
    .code-line.masked-line {{
      background: #fff3bf;
      box-shadow: inset 4px 0 0 #f59e0b;
    }}
    .code-line.completion-line {{
      background: #dcfce7;
      box-shadow: inset 4px 0 0 #16a34a;
    }}
    .alignment-warning {{
      color: #b45309;
      font-weight: 600;
    }}
    .line-no {{
      padding-right: 12px;
      color: #98a2b3;
      text-align: right;
      user-select: none;
      font-variant-numeric: tabular-nums;
    }}
    .masked-line .line-no {{
      color: #92400e;
      font-weight: 600;
    }}
    .completion-line .line-no {{
      color: #166534;
      font-weight: 600;
    }}
    .line-code {{
      min-width: 0;
      overflow-wrap: anywhere;
      white-space: pre-wrap;
    }}
    .comparison {{
      display: grid;
      grid-template-columns: minmax(0, 1.25fr) minmax(320px, 0.75fr);
      min-height: 0;
    }}
    .pane {{
      min-width: 0;
    }}
    .pane + .pane {{
      border-left: 1px solid var(--line);
    }}
    .pane-title {{
      padding: 9px 14px;
      border-bottom: 1px solid var(--line);
      background: #fcfcfa;
      color: var(--muted);
      font-size: 13px;
      font-weight: 600;
    }}
    .score {{
      display: inline-block;
      min-width: 58px;
      padding: 3px 8px;
      border-radius: 999px;
      background: var(--accent-soft);
      color: var(--accent);
      text-align: center;
      font-variant-numeric: tabular-nums;
    }}
    .answer {{
      max-height: 520px;
      overflow: auto;
      background: #fcfcfa;
    }}
    @media (max-width: 860px) {{
      .comparison {{
        grid-template-columns: 1fr;
      }}
      .pane + .pane {{
        border-left: 0;
        border-top: 1px solid var(--line);
      }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>Recursive Masking Complexity Report</h1>
    <div class="meta">
      <span>Source: {html.escape(data["source_path"])}</span>
      <span>Model: {html.escape(data["model"])}</span>
      <span>Line numbers: cleaned non-blank source</span>
    </div>
  </header>
  <main>
    <section class="stats">
      <div class="stat">Score<strong>{_format_score(summary["score"])}</strong></div>
      <div class="stat">Masks<strong>{summary["mask_count"]}</strong></div>
      <div class="stat">Recoveries<strong>{summary["profile_count"]}</strong></div>
    </section>

    <section>
      <h2>Masks And Completions</h2>
      {recovery_blocks}
    </section>
  </main>
</body>
</html>
"""


def _render_recovery_blocks(
    recoveries: Sequence[Dict[str, Any]],
    source_lines: Sequence[str],
) -> str:
    blocks: List[str] = []
    for item in recoveries:
        blocks.append(
            f"""<article class="block">
  <div class="block-title">
    <span>Mask #{item["index"]}</span>
    <span>{html.escape(_mask_label(item))}, full similarity=<span class="score">{item["similarity"]:.4f}</span></span>
  </div>
  <div class="comparison">
    <div class="pane">
      <div class="pane-title">Original Source</div>
      {_render_highlighted_code(source_lines, item["spans"])}
    </div>
    <div class="pane">
      <div class="pane-title">Recovered Output</div>
      {_render_recovered_code(item["llm_answer"], item.get("completion_line_indexes", ()))}
    </div>
  </div>
</article>"""
        )
    return "\n".join(blocks)


def _render_highlighted_code(
    source_lines: Sequence[str],
    spans: Sequence[Dict[str, int]],
) -> str:
    masked_lines = set()
    for span in spans:
        masked_lines.update(range(span["start"], span["end"]))

    rendered_lines = []
    for index, line in enumerate(source_lines):
        class_name = "code-line masked-line" if index in masked_lines else "code-line"
        rendered_lines.append(
            f"""<div class="{class_name}">
  <span class="line-no">{index + 1}</span>
  <span class="line-code">{html.escape(line) if line else " "}</span>
</div>"""
        )

    return f'<div class="code-view">{"".join(rendered_lines)}</div>'


def _render_recovered_code(text: str, highlighted_indexes: Sequence[int]) -> str:
    highlighted = set(highlighted_indexes)
    lines = text.splitlines() or [""]
    rendered_lines = []
    for index, line in enumerate(lines):
        class_name = "code-line completion-line" if index in highlighted else "code-line"
        rendered_lines.append(
            f"""<div class="{class_name}">
  <span class="line-no">{index + 1}</span>
  <span class="line-code">{html.escape(line) if line else " "}</span>
</div>"""
        )

    return f'<div class="code-view">{"".join(rendered_lines)}</div>'


def _format_spans(spans: Sequence[Dict[str, int]]) -> str:
    labels = []
    for span in spans:
        first_line = span["start"] + 1
        last_line = span["end"]
        if first_line == last_line:
            labels.append(str(first_line))
        else:
            labels.append(f"{first_line}-{last_line}")
    return ", ".join(labels)


def _mask_label(item: Dict[str, Any]) -> str:
    lines = _format_spans(item["spans"])
    if str(item.get("strategy", "")).startswith("java_ast") and item.get("node_type"):
        return (
            f"node={item['node_type']}, role={item.get('ast_role')}, "
            f"tokens={item.get('token_count')}, source lines={lines}"
        )
    if str(item.get("strategy", "")).startswith("java_ast") and item.get("node_types"):
        nodes = "+".join(item["node_types"])
        return (
            f"level={item.get('ast_granularity')}, nodes={nodes}, "
            f"tokens={item.get('token_count')}, source lines={lines}"
        )
    return f"lines={lines}"


def _format_score(score: Any) -> str:
    if score is None:
        return "n/a"
    return f"{score:.4f}"
