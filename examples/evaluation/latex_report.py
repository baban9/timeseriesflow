"""Generate publication-grade LaTeX for the comparative evaluation PDF."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from evaluation.verdict import status_label

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


def _decision_table_rows(rows: list[dict[str, Any]]) -> str:
    mode_keys = [
        "vanilla_pandas",
        "timeseriesflow",
        "adaptiveforecast_loop",
        "full_stack",
    ]
    lines: list[str] = []
    for row in rows:
        cells = " & ".join(
            _tex_escape(status_label(row.get(key, "na"))) for key in mode_keys
        )
        lines.append(f"{_tex_escape(row['criterion'])} & {cells} \\\\")
    return "\n".join(lines)


def _product_verdict_block(key: str, verdict: dict[str, Any]) -> str:
    title = {
        "timeseriesflow": "TimeSeriesFlow",
        "adaptiveforecast": "AdaptiveForecast",
        "full_stack": "Full stack",
    }[key]
    effective = "\n".join(
        f"  \\item {_tex_escape(line)}" for line in verdict.get("effective_for", [])
    )
    ineffective = "\n".join(
        f"  \\item {_tex_escape(line)}" for line in verdict.get("not_effective_for", [])
    )
    return f"""
\\subsection{{{title}}}
\\noindent\\textbf{{Verdict ({_tex_escape(status_label(verdict.get('status', 'partial')))}):}}
{_tex_escape(verdict.get('headline', ''))}

\\textbf{{Use when:}}
\\begin{{itemize}}
{effective}
\\end{{itemize}}

\\textbf{{Do not use when:}}
\\begin{{itemize}}
{ineffective}
\\end{{itemize}}
"""


def _verdict_section(verdict: dict[str, Any]) -> str:
    if not verdict:
        return ""
    use_lines = "\n".join(f"  \\item {_tex_escape(line)}" for line in verdict.get("use_when", []))
    avoid_lines = "\n".join(
        f"  \\item {_tex_escape(line)}" for line in verdict.get("avoid_when", [])
    )
    products = verdict.get("product_verdicts") or {}
    product_blocks = "".join(
        _product_verdict_block(key, products[key])
        for key in ("timeseriesflow", "adaptiveforecast", "full_stack")
        if key in products
    )
    decision_notes = "\n".join(
        f"  \\item \\textbf{{{_tex_escape(row['criterion'])}}}: {_tex_escape(row.get('note', ''))}"
        for row in verdict.get("decision_table", [])
    )
    return f"""
\\section{{Executive verdict}}
\\noindent\\textbf{{Bottom line.}} {_tex_escape(verdict.get('executive_summary', ''))}

\\subsection{{When to use the stack}}
\\begin{{itemize}}
{use_lines}
\\end{{itemize}}

\\subsection{{When not to use the stack}}
\\begin{{itemize}}
{avoid_lines}
\\end{{itemize}}

\\subsection{{Effectiveness decision table}}
\\begin{{table}}[htbp]
\\centering
\\caption{{Pass or fail against benchmark criteria (Phase 1: no forecast accuracy test).}}
\\label{{tab:decision}}
\\small
\\begin{{tabular}}{{p{{4.8cm}}cccc}}
\\toprule
Criterion & Pandas & TSFlow & AF loop & Full stack \\\\
\\midrule
{_decision_table_rows(verdict.get('decision_table', []))}
\\bottomrule
\\end{{tabular}}
\\end{{table}}

\\noindent\\textbf{{Notes.}}
\\begin{{itemize}}
{decision_notes}
\\end{{itemize}}

{product_blocks}
"""


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
    verdict: dict[str, Any] = payload.get("verdict") or {}

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

    verdict_section = _verdict_section(verdict)

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
We benchmark four entity processing approaches on three public multi-entity time series datasets.
This Phase 1 report answers a single question: should you adopt TimeSeriesFlow, AdaptiveForecast,
or the combined stack for your workload? We measure screening throughput, gate outcomes, routing
diversity, and orchestration overhead. We do \\textbf{{not}} yet measure forecast accuracy (Phase 2).
Vanilla pandas wins on raw speed for simple statistics. AdaptiveForecast blocks unfit entities and
assigns model families. TimeSeriesFlow adds batch structure with modest overhead on lightweight work.
\\end{{abstract}}

{verdict_section}

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
The executive verdict above is the primary takeaway. The sections below provide supporting metrics.

\\textbf{{How to read throughput charts.}}
Do not treat vanilla pandas throughput as a forecast baseline. It computes mean and row count only.
Full-stack throughput reflects profiling plus routing plus orchestration. Compare TimeSeriesFlow to
pandas for orchestration tax; compare full stack to AdaptiveForecast-only for runner overhead.

\\textbf{{Commercial framing.}}
Lead with screening and routing when entity quality varies. Lead with orchestration when batch
reliability matters. Do not sell on pandas speed. Phase 2 must add forecast error metrics before
claiming model-selection effectiveness.

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
