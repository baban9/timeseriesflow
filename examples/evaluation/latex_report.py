"""Generate LaTeX source for the comparative evaluation PDF."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

# ruff: noqa: E501


def _tex_escape(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    escaped = text
    for key, value in replacements.items():
        escaped = escaped.replace(key, value)
    return escaped


def _format_mode_table_row(run: dict[str, Any]) -> str:
    gate = (
        f"{100 * float(run['gate_pass_rate']):.1f}\\%"
        if run["gate_pass_rate"] is not None
        else "---"
    )
    diversity = (
        f"{100 * float(run['routing_diversity_rate']):.1f}\\%"
        if run["routing_diversity_rate"] is not None
        else "---"
    )
    return (
        f"{_tex_escape(run['mode'])} & "
        f"{run['elapsed_seconds']:.2f} & "
        f"{run['entities_per_second']:.2f} & "
        f"{gate} & {diversity} \\\\"
    )


def generate_latex_report(
    payload: dict[str, Any],
    *,
    figures: dict[str, str],
    output_path: Path,
) -> None:
    datasets = payload["datasets"]
    generated_on = payload.get("generated_on", date.today().isoformat())

    dataset_sections: list[str] = []
    for item in datasets:
        summary = item["summary"]
        rows = "\n".join(_format_mode_table_row(run) for run in item["runs"])
        section = f"""
\\section{{{_tex_escape(item['dataset'])}}}
{ _tex_escape(item.get('description', '')) }

\\begin{{tabular}}{{lrrrr}}
\\toprule
Approach & Seconds & Entities/s & Gate pass & Routing diversity \\\\
\\midrule
{rows}
\\bottomrule
\\end{{tabular}}

\\vspace{{0.4cm}}
\\noindent Entities: {summary['entities']}. Rows: {summary['rows']}. Median rows/entity: {summary['median_rows_per_entity']:.0f}. Span (days): {summary['span_days']:.1f}.
"""
        dataset_sections.append(section)

    conclusions = payload.get("conclusions", [])
    conclusion_lines = "\n".join(f"  \\item {_tex_escape(line)}" for line in conclusions)

    content = f"""
\\documentclass[11pt,a4paper]{{article}}
\\usepackage[margin=1in]{{geometry}}
\\usepackage{{graphicx}}
\\usepackage{{booktabs}}
\\usepackage{{caption}}
\\usepackage{{subcaption}}
\\usepackage{{xcolor}}
\\usepackage{{hyperref}}
\\usepackage{{microtype}}

\\title{{\\textbf{{TimeSeriesFlow and AdaptiveForecast}}\\\\Comparative Evaluation Report}}
\\author{{TimeSeriesFlow Open Benchmark}}
\\date{{{_tex_escape(generated_on)}}}

\\begin{{document}}
\\maketitle

\\begin{{abstract}}
This report compares four processing approaches on three public multi-entity time series datasets:
vanilla pandas loops, AdaptiveForecast profiling without orchestration, TimeSeriesFlow entity execution,
and the combined full stack. We measure throughput, runtime, quality gate outcomes, and per-entity model routing diversity.
\\end{{abstract}}

\\section{{Objective}}
The objective is to determine when TimeSeriesFlow and AdaptiveForecast add practical value over manual pandas workflows.
We test whether per-entity orchestration, checkpoint-ready execution, and profile-driven model routing improve operational
decisions on real sensor and energy data.

\\section{{Methodology}}
\\textbf{{Datasets.}}
(1) Intel Berkeley Research Lab: 54 wireless motes, irregular sampling.
(2) ETT hourly (ETTh1): seven electricity load channels on a regular grid.
(3) UCI household power: three sub-meter channels with minute-level domestic load.

\\textbf{{Approaches.}}
\\begin{{itemize}}
  \\item \\textbf{{Vanilla pandas}}: groupby loop with mean and row count only.
  \\item \\textbf{{AdaptiveForecast loop}}: per-entity profiling and routing without TimeSeriesFlow.
  \\item \\textbf{{TimeSeriesFlow}}: EntityRunner with lightweight per-entity summaries.
  \\item \\textbf{{Full stack}}: EntityRunner plus AdaptiveForecast profiling and validation gates.
\\end{{itemize}}

\\section{{Performance overview}}
\\begin{{figure}}[h]
  \\centering
  \\includegraphics[width=0.92\\linewidth]{{figures/{figures['throughput']}}}
  \\caption{{Entity throughput across datasets and approaches.}}
\\end{{figure}}

\\begin{{figure}}[h]
  \\centering
  \\includegraphics[width=0.92\\linewidth]{{figures/{figures['elapsed']}}}
  \\caption{{Wall-clock runtime across datasets and approaches.}}
\\end{{figure}}

\\section{{Routing and screening (full stack)}}
\\begin{{figure}}[h]
  \\centering
  \\includegraphics[width=0.92\\linewidth]{{figures/{figures['routing']}}}
  \\caption{{Gate pass rate, routing diversity, and unique model count per dataset.}}
\\end{{figure}}

\\begin{{figure}}[h]
  \\centering
  \\includegraphics[width=0.92\\linewidth]{{figures/{figures['models']}}}
  \\caption{{Distribution of assigned model families per dataset.}}
\\end{{figure}}

{''.join(dataset_sections)}

\\section{{Interpretation}}
\\textbf{{When the stack is needed.}}
Use TimeSeriesFlow when you process many entities in production batches and need retries, progress, and checkpoint hooks.
Use AdaptiveForecast when entities show heterogeneous quality or patterns and a single global model family is risky.

\\textbf{{When vanilla pandas is enough.}}
A plain groupby loop remains sufficient for small entity counts, exploratory analysis, or homogeneous series where routing and gates add little.

\\section{{Conclusions}}
\\begin{{itemize}}
{conclusion_lines}
\\end{{itemize}}

\\end{{document}}
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content.strip() + "\n", encoding="utf-8")


def write_json_report(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
