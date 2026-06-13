"""Build a PDF report from generated figures when LaTeX is unavailable."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages


def build_pdf_from_figures(
    payload: dict[str, Any],
    figures_dir: Path,
    output_path: Path,
) -> Path:
    """Assemble a multi-page PDF from vector figure assets and KPI text."""
    figures: dict[str, str] = payload.get("figures") or {}
    portfolio: dict[str, Any] = payload.get("portfolio_summary") or {}
    highlights: list[str] = payload.get("pitch_highlights") or []

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with PdfPages(output_path) as pdf:
        _title_page(pdf, payload.get("generated_on", ""), portfolio, highlights)

        order = [
            ("throughput", "Figure 1. Entity throughput by approach and dataset."),
            (
                "commercial_kpis",
                "Figure 2. Training jobs avoided, routing diversity, unique models.",
            ),
            ("screening", "Figure 3. Vanilla stats throughput vs full-stack screening."),
            ("models_stacked", "Figure 4. Model family assignment distribution."),
            ("kpi_heatmap", "Figure 5. Normalized KPI heatmap across datasets."),
        ]
        for key, caption in order:
            name = figures.get(key)
            if not name:
                continue
            path = figures_dir / name
            png_path = path.with_suffix(".png")
            if png_path.exists():
                _figure_page(pdf, png_path, caption)
            elif path.exists():
                _figure_page(pdf, path, caption)

        _kpi_table_page(pdf, payload.get("commercial_kpis") or [])

    return output_path


def _title_page(
    pdf: PdfPages,
    generated_on: str,
    portfolio: dict[str, Any],
    highlights: list[str],
) -> None:
    fig, ax = plt.subplots(figsize=(8.27, 11.69))
    ax.axis("off")
    avoided_pct = 100 * float(portfolio.get("portfolio_training_jobs_avoided_rate", 0))
    diversity_pct = 100 * float(portfolio.get("mean_routing_diversity_rate", 0))
    screening_eps = portfolio.get("mean_screening_throughput_eps", 0)
    lines = [
        "TimeSeriesFlow and AdaptiveForecast",
        "Comparative Evaluation and Commercial Impact Report",
        "",
        f"Generated: {generated_on}",
        "",
        "Portfolio summary",
        f"  Datasets: {portfolio.get('datasets_evaluated', 0)}",
        f"  Total entities: {portfolio.get('total_entities', 0)}",
        f"  Training jobs avoided: {avoided_pct:.1f}%",
        f"  Mean routing diversity: {diversity_pct:.1f}%",
        f"  Mean screening throughput: {screening_eps:.1f} ent/s",
        "",
        "Highlights",
    ]
    lines.extend(f"  - {line}" for line in highlights[:6])
    ax.text(0.08, 0.92, "\n".join(lines), va="top", ha="left", fontsize=11, family="serif")
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def _figure_page(pdf: PdfPages, image_path: Path, caption: str) -> None:
    png_path = image_path.with_suffix(".png")
    source = png_path if png_path.exists() else image_path
    img = plt.imread(str(source))
    fig, ax = plt.subplots(figsize=(8.27, 11.69))
    ax.imshow(img)
    ax.axis("off")
    ax.set_title(caption, fontsize=10, family="serif", loc="left", pad=12)
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def _kpi_table_page(pdf: PdfPages, kpis: list[dict[str, Any]]) -> None:
    fig, ax = plt.subplots(figsize=(8.27, 11.69))
    ax.axis("off")
    header = (
        f"{'Dataset':<8} {'Ent':>4} {'Avoid%':>7} {'Div%':>7} "
        f"{'Models':>7} {'Ent/s':>7} {'Cost':>6}"
    )
    rows = [header, "-" * len(header)]
    for kpi in kpis:
        rows.append(
            f"{kpi['dataset']!s:<8} {kpi['entities']:>4} "
            f"{100 * kpi['training_jobs_avoided_rate']:>6.1f}% "
            f"{100 * kpi['routing_diversity_rate']:>6.1f}% "
            f"{kpi['unique_models_assigned']:>7} "
            f"{kpi['screening_throughput_eps']:>7.1f} "
            f"{kpi.get('profiling_cost_factor_vs_vanilla', 0):>5.1f}x"
        )
    table_text = "Commercial KPI table\n\n" + "\n".join(rows)
    ax.text(
        0.06,
        0.94,
        table_text,
        va="top",
        ha="left",
        fontsize=9,
        family="monospace",
    )
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)
