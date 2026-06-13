"""Generate publication-grade LaTeX for the comparative evaluation PDF."""

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


def _kpi_table_rows(kpis: list[dict[str, Any]]) -> str:
    rows: list[str] = []
    for kpi in kpis:
        avoided_pct = 100.0 * float(kpi["training_jobs_avoided_rate"])
        diversity_pct = 100.0 * float(kpi["routing_diversity_rate"])
        cost_factor = float(kpi.get("profiling_cost_factor_vs_vanilla") or 0.0)
        rows.append(
            f"{_tex_escape(str(kpi['dataset']))} & "
            f"{kpi['entities']} & "
            f"{avoided_pct:.1f}\\% & "
            f"{diversity_pct:.1f}\\% & "
            f"{kpi['unique_models_assigned']} & "
            f"{kpi['screening_throughput_eps']:.1f} & "
            f"{cost_factor:.1f}$\\times$ \\\\"
        )
    return "\n".join(rows)


def _pitch_lines(highlights: list[str]) -> str:
    return "\n".join(f"  \\item {_tex_escape(line)}" for line in highlights)


def generate_latex_report(
    payload: dict[str, Any],
    *,
    figures: dict[str, str],
    output_path: Path,
) -> None:
    datasets = payload["datasets"]
    generated_on = payload.get("generated_on", date.today().isoformat())
    per_dataset_kpis: list[dict[str, Any]] = payload.get("commercial_kpis") or []
    portfolio: dict[str, Any] = payload.get("portfolio_summary") or {}
    pitch_highlights: list[str] = payload.get("pitch_highlights") or []

    portfolio_blocked_pct = 100.0 * float(portfolio.get("portfolio_training_jobs_avoided_rate") or 0.0)
    portfolio_screening = float(portfolio.get("mean_screening_throughput_eps") or 0.0)
    total_entities = int(portfolio.get("total_entities") or 0)

    dataset_sections: list[str] = []
    for item in datasets:
        summary = item["summary"]
        rows = "\n".join(_format_mode_table_row(run) for run in item["runs"])
        section = f"""
\\subsection{{{_tex_escape(item['dataset'])}}}
{_tex_escape(item.get('description', ''))}

\\begin{{tabular}}{{lrrrr}}
\\toprule
Approach & Seconds & Entities/s & Gate pass & Routing diversity \\\\
\\midrule
{rows}
\\bottomrule
\\end{{tabular}}

\\vspace{{0.3cm}}
\\noindent Entities: {summary['entities']}. Rows: {summary['rows']}. Median rows/entity: {summary['median_rows_per_entity']:.0f}. Span (days): {summary['span_days']:.1f}.
"""
        dataset_sections.append(section)

    conclusions = payload.get("conclusions", [])
    conclusion_lines = "\n".join(f"  \\item {_tex_escape(line)}" for line in conclusions)
    pitch_block = _pitch_lines(pitch_highlights) if pitch_highlights else ""

    pitch_section = ""
    if pitch_block:
        pitch_section = (
            "\\subsection{Executive highlights}\n"
            "\\begin{itemize}\n"
            f"{pitch_block}\n"
            "\\end{itemize}"
        )

    content = f"""
\\documentclass[11pt,a4paper]{{article}}
\\usepackage[margin=0.9in]{{geometry}}
\\usepackage{{graphicx}}
\\usepackage{{booktabs}}
\\usepackage{{caption}}
\\usepackage{{subcaption}}
\\usepackage{{xcolor}}
\\usepackage{{hyperref}}
\\usepackage{{microtype}}

\\hypersetup{{
  colorlinks=true,
  linkcolor=black,
  citecolor=black,
  urlcolor=blue!60!black
}}

\\title{{\\textbf{{TimeSeriesFlow and AdaptiveForecast}}\\\\[0.4em]\\large Comparative Evaluation and Commercial Impact Report}}
\\author{{TimeSeriesFlow Open Benchmark}}
\\date{{{_tex_escape(generated_on)}}}

\\begin{{document}}
\\maketitle

\\begin{{abstract}}
We benchmark four entity processing approaches on three public multi-entity time series datasets:
vanilla pandas loops, AdaptiveForecast profiling without orchestration, TimeSeriesFlow entity execution,
and the combined full stack. Beyond throughput, we quantify operational key performance indicators:
training jobs avoided by validation gates, routing diversity, unique model families assigned,
and screening throughput. Results show that vanilla pandas remains fastest for simple statistics,
while the full stack delivers profile-driven routing and blocks unfit entities before training spend accrues.
\\end{{abstract}}

\\section{{Introduction}}
Large fleets of heterogeneous time series create two recurring costs: wasted training on entities that fail quality gates,
and forecast error from a single global model family. TimeSeriesFlow addresses batch orchestration; AdaptiveForecast adds
profiling, validation gates, and per-entity model routing. This report measures when the combined stack justifies its
runtime overhead relative to manual pandas workflows.

\\section{{Methodology}}
\\subsection{{Datasets}}
\\begin{{table}}[htbp]
\\centering
\\caption{{Open datasets used in the benchmark.}}
\\begin{{tabular}}{{llrr}}
\\toprule
Dataset & Domain & Entities & Max rows/entity \\\\
\\midrule
Intel Berkeley Lab & Wireless sensors & 30 (subset) & 4\\,000 \\\\
ETT Hourly (ETTh1) & Grid load & 7 & 4\\,000 \\\\
UCI Household Power & Residential meters & 3 & 4\\,000 \\\\
\\bottomrule
\\end{{tabular}}
\\end{{table}}

\\subsection{{Approaches}}
\\begin{{itemize}}
  \\item \\textbf{{Vanilla pandas}}: groupby loop computing mean and row count only.
  \\item \\textbf{{AdaptiveForecast loop}}: per-entity profiling and routing without TimeSeriesFlow.
  \\item \\textbf{{TimeSeriesFlow}}: EntityRunner with lightweight per-entity summaries.
  \\item \\textbf{{Full stack}}: EntityRunner plus AdaptiveForecast profiling, validation gates, and routing.
\\end{{itemize}}

All timed runs use a single worker unless noted. Metrics are computed on identical entity subsets per dataset.

\\section{{Commercial key performance indicators}}
Table~\\ref{{tab:kpi}} summarizes pitch-ready metrics derived from full-stack runs.
Portfolio gate block rate is {portfolio_blocked_pct:.1f}\\% across {total_entities} entities.
Mean screening throughput is {portfolio_screening:.1f} entities/s.

\\begin{{table}}[htbp]
\\centering
\\caption{{Operational KPIs per dataset (full stack). Training jobs avoided equals gate block rate. Profiling cost is vanilla throughput divided by screening throughput.}}
\\label{{tab:kpi}}
\\small
\\begin{{tabular}}{{lrrrrrr}}
\\toprule
Dataset & Entities & Jobs avoided & Diversity & Models & Screen (ent/s) & Cost factor \\\\
\\midrule
{_kpi_table_rows(per_dataset_kpis)}
\\bottomrule
\\end{{tabular}}
\\end{{table}}

\\textbf{{Metric definitions.}}
\\begin{{itemize}}
  \\item \\textbf{{Training jobs avoided}}: share of entities blocked by validation gates before model assignment.
  \\item \\textbf{{Routing diversity}}: share of entities assigned a model different from the fleet modal choice.
  \\item \\textbf{{Screening throughput}}: entities profiled and routed per second under the full stack.
  \\item \\textbf{{Profiling cost factor}}: how many times slower full-stack screening is versus vanilla stats-only loops.
\\end{{itemize}}

{pitch_section}

\\section{{Results}}

\\begin{{figure}}[htbp]
  \\centering
  \\includegraphics[width=0.95\\linewidth]{{figures/{figures['throughput']}}}
  \\caption{{Entity throughput across datasets and processing approaches. Vanilla pandas maximizes raw speed; the full stack trades throughput for profiling and routing.}}
  \\label{{fig:throughput}}
\\end{{figure}}

\\begin{{figure}}[htbp]
  \\centering
  \\begin{{subfigure}}[b]{{0.48\\linewidth}}
    \\includegraphics[width=\\linewidth]{{figures/{figures['commercial_kpis']}}}
    \\caption{{Training jobs avoided, routing diversity, and unique model families.}}
    \\label{{fig:commercial}}
  \\end{{subfigure}}
  \\hfill
  \\begin{{subfigure}}[b]{{0.48\\linewidth}}
    \\includegraphics[width=\\linewidth]{{figures/{figures['screening']}}}
    \\caption{{Vanilla stats throughput versus full-stack screening throughput.}}
    \\label{{fig:screening}}
  \\end{{subfigure}}
  \\caption{{Commercial impact and throughput trade-off.}}
\\end{{figure}}

\\begin{{figure}}[htbp]
  \\centering
  \\begin{{subfigure}}[b]{{0.48\\linewidth}}
    \\includegraphics[width=\\linewidth]{{figures/{figures['models_stacked']}}}
    \\caption{{Per-dataset model family assignment counts.}}
    \\label{{fig:models}}
  \\end{{subfigure}}
  \\hfill
  \\begin{{subfigure}}[b]{{0.48\\linewidth}}
    \\includegraphics[width=\\linewidth]{{figures/{figures['kpi_heatmap']}}}
    \\caption{{Normalized KPI heatmap across datasets.}}
    \\label{{fig:heatmap}}
  \\end{{subfigure}}
  \\caption{{Routing outcomes and cross-dataset KPI comparison.}}
\\end{{figure}}

\\section{{Per-dataset benchmark tables}}
{''.join(dataset_sections)}

\\section{{Discussion}}
\\textbf{{When the stack delivers value.}}
The full stack is justified when entity quality varies and a uniform model family risks silent underperformance.
On Intel Berkeley and ETT Hourly, gates pass most entities while routing assigns multiple model families.
Screening at roughly 50 entities/s supports nightly fleet batches without dedicated infrastructure.

\\textbf{{When vanilla pandas suffices.}}
For small entity counts, exploratory analysis, or homogeneous series, a groupby loop remains the fastest path.
The profiling cost factor (often 50--100$\\times$ versus vanilla) is acceptable only when avoided training jobs and
routing accuracy have measurable downstream value.

\\textbf{{Commercial framing.}}
Lead with training jobs avoided and routing diversity when selling profile-driven forecasting.
Lead with orchestration throughput and checkpoint readiness when selling batch reliability.
Do not compete on raw pandas speed for simple aggregates.

\\section{{Conclusions}}
\\begin{{itemize}}
{conclusion_lines}
\\end{{itemize}}

\\vspace{{0.5cm}}
\\noindent Report generated by TimeSeriesFlow open benchmark tooling. Figures exported at 300 DPI with vector PDF companions.

\\end{{document}}
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content.strip() + "\n", encoding="utf-8")


def write_json_report(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
