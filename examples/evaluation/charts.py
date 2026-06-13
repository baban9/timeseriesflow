"""Publication-grade matplotlib charts for the comparative evaluation report."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from evaluation.commercial_kpis import compute_dataset_kpis

# Colorblind-friendly palette (Wong / Paul Tol inspired)
PALETTE = {
    "vanilla_pandas": "#999999",
    "adaptiveforecast_loop": "#E69F00",
    "timeseriesflow": "#56B4E9",
    "full_stack": "#009E73",
    "blocked": "#D55E00",
    "passed": "#0072B2",
    "diversity": "#CC79A7",
    "models": "#332288",
}

MODE_LABELS = {
    "vanilla_pandas": "Vanilla pandas",
    "adaptiveforecast_loop": "AF loop",
    "timeseriesflow": "TimeSeriesFlow",
    "full_stack": "Full stack",
}

MODE_ORDER = list(MODE_LABELS.keys())


def apply_publication_style() -> None:
    mpl.rcParams.update(
        {
            "figure.dpi": 150,
            "savefig.dpi": 300,
            "font.family": "serif",
            "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
            "font.size": 10,
            "axes.labelsize": 11,
            "axes.titlesize": 11,
            "legend.fontsize": 9,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "axes.linewidth": 0.8,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.alpha": 0.25,
            "grid.linewidth": 0.6,
            "lines.linewidth": 1.5,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )


def _dataset_label(item: dict[str, Any]) -> str:
    key = str(item.get("dataset_key") or item.get("dataset") or "")
    title = str(item.get("dataset") or key)
    mapping = {
        "intel": "Intel Lab",
        "ett": "ETT Hourly",
        "uci": "UCI Household",
        "fixture": "Fixture",
        "Intel Berkeley Lab": "Intel Lab",
        "ETT Hourly (ETTh1)": "ETT Hourly",
        "UCI Household Power": "UCI Household",
        "Fixture sample": "Fixture",
    }
    return mapping.get(key, mapping.get(title, title))


def _mode_lookup(runs: list[dict[str, Any]], mode: str) -> dict[str, Any]:
    for run in runs:
        if run["mode"] == mode:
            return run
    raise KeyError(mode)


def _save_figure(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    fig.savefig(path.with_suffix(".pdf"), bbox_inches="tight", facecolor="white")
    plt.close(fig)


def plot_throughput_comparison(results: list[dict[str, Any]], output_path: Path) -> None:
    apply_publication_style()
    datasets = [_dataset_label(item) for item in results]
    x = np.arange(len(datasets))
    width = 0.18

    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    for index, mode in enumerate(MODE_ORDER):
        values = [_mode_lookup(item["runs"], mode)["entities_per_second"] for item in results]
        ax.bar(
            x + (index - 1.5) * width,
            values,
            width,
            label=MODE_LABELS[mode],
            color=PALETTE[mode],
            edgecolor="white",
            linewidth=0.5,
        )

    ax.set_ylabel("Throughput (entities s$^{-1}$)")
    ax.set_xlabel("Dataset")
    ax.set_xticks(x)
    ax.set_xticklabels(datasets)
    ax.legend(frameon=False, ncol=2, loc="upper right")
    ax.text(0.02, 0.98, "(a)", transform=ax.transAxes, fontsize=12, fontweight="bold", va="top")
    fig.tight_layout()
    _save_figure(fig, output_path)


def plot_commercial_kpis(
    results: list[dict[str, Any]],
    output_path: Path,
) -> None:
    apply_publication_style()
    kpis = [compute_dataset_kpis(item) for item in results]
    datasets = [_dataset_label(item) for item in results]
    x = np.arange(len(datasets))
    width = 0.35

    blocked = [100.0 * kpi["training_jobs_avoided_rate"] for kpi in kpis]
    diversity = [100.0 * kpi["routing_diversity_rate"] for kpi in kpis]
    unique_models = [kpi["unique_models_assigned"] for kpi in kpis]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.2, 3.6))

    ax1.bar(x - width / 2, blocked, width, label="Training jobs avoided", color=PALETTE["blocked"])
    ax1.bar(x + width / 2, diversity, width, label="Routing diversity", color=PALETTE["diversity"])
    ax1.set_ylabel("Rate (\\%)")
    ax1.set_xlabel("Dataset")
    ax1.set_xticks(x)
    ax1.set_xticklabels(datasets)
    ax1.set_ylim(0, 105)
    ax1.legend(frameon=False, loc="upper right")
    ax1.text(0.02, 0.98, "(b)", transform=ax1.transAxes, fontsize=12, fontweight="bold", va="top")

    ax2.bar(x, unique_models, width=0.55, color=PALETTE["models"], edgecolor="white")
    ax2.set_ylabel("Unique model families")
    ax2.set_xlabel("Dataset")
    ax2.set_xticks(x)
    ax2.set_xticklabels(datasets)
    ax2.text(0.02, 0.98, "(c)", transform=ax2.transAxes, fontsize=12, fontweight="bold", va="top")

    fig.tight_layout()
    _save_figure(fig, output_path)


def plot_screening_throughput(
    results: list[dict[str, Any]],
    output_path: Path,
) -> None:
    apply_publication_style()
    kpis = [compute_dataset_kpis(item) for item in results]
    datasets = [_dataset_label(item) for item in results]
    screening = [kpi["screening_throughput_eps"] for kpi in kpis]
    vanilla = [kpi["vanilla_throughput_eps"] for kpi in kpis]

    x = np.arange(len(datasets))
    width = 0.35
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    ax.bar(x - width / 2, vanilla, width, label="Vanilla pandas (stats only)", color=PALETTE["vanilla_pandas"])
    ax.bar(x + width / 2, screening, width, label="Full stack (profile + route)", color=PALETTE["full_stack"])
    ax.set_ylabel("Throughput (entities s$^{-1}$)")
    ax.set_xlabel("Dataset")
    ax.set_xticks(x)
    ax.set_xticklabels(datasets)
    ax.legend(frameon=False)
    ax.text(0.02, 0.98, "(d)", transform=ax.transAxes, fontsize=12, fontweight="bold", va="top")
    fig.tight_layout()
    _save_figure(fig, output_path)


def plot_model_distribution_stacked(
    results: list[dict[str, Any]],
    output_path: Path,
) -> None:
    apply_publication_style()
    datasets = [_dataset_label(item) for item in results]
    all_models: list[str] = []
    for item in results:
        dist = _mode_lookup(item["runs"], "full_stack").get("model_distribution") or {}
        for model in dist:
            if model not in all_models:
                all_models.append(model)

    model_colors = {
        "moving_average": "#56B4E9",
        "exponential_smoothing": "#009E73",
        "residual_lstm": "#E69F00",
        "naive": "#CC79A7",
        "insufficient_data": "#D55E00",
        "none": "#999999",
    }

    x = np.arange(len(datasets))
    bottom = np.zeros(len(datasets))
    fig, ax = plt.subplots(figsize=(7.2, 3.8))

    for model in all_models:
        values = []
        for item in results:
            dist = _mode_lookup(item["runs"], "full_stack").get("model_distribution") or {}
            values.append(dist.get(model, 0))
        ax.bar(
            x,
            values,
            bottom=bottom,
            label=model.replace("_", " "),
            color=model_colors.get(model, "#332288"),
            edgecolor="white",
            linewidth=0.4,
        )
        bottom += np.array(values)

    ax.set_ylabel("Entity count")
    ax.set_xlabel("Dataset")
    ax.set_xticks(x)
    ax.set_xticklabels(datasets)
    ax.legend(frameon=False, bbox_to_anchor=(1.02, 1), loc="upper left")
    ax.text(0.02, 0.98, "(e)", transform=ax.transAxes, fontsize=12, fontweight="bold", va="top")
    fig.tight_layout()
    _save_figure(fig, output_path)


def plot_kpi_heatmap(
    results: list[dict[str, Any]],
    output_path: Path,
) -> None:
    apply_publication_style()
    kpis = [compute_dataset_kpis(item) for item in results]
    datasets = [_dataset_label(item) for item in results]
    metrics = [
        "training_jobs_avoided_rate",
        "routing_diversity_rate",
        "unique_models_assigned",
    ]
    labels = ["Training jobs avoided", "Routing diversity", "Unique models (norm.)"]

    matrix = []
    for metric in metrics:
        row = [float(kpi[metric]) for kpi in kpis]
        if metric == "unique_models_assigned":
            max_val = max(row) if row else 1.0
            row = [value / max_val for value in row]
        matrix.append(row)
    data = np.array(matrix)

    fig, ax = plt.subplots(figsize=(7.2, 3.2))
    im = ax.imshow(data, aspect="auto", cmap="YlGnBu", vmin=0, vmax=1)
    ax.set_xticks(np.arange(len(datasets)))
    ax.set_xticklabels(datasets)
    ax.set_yticks(np.arange(len(labels)))
    ax.set_yticklabels(labels)
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            ax.text(j, i, f"{data[i, j]:.2f}", ha="center", va="center", fontsize=9)
    cbar = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    cbar.set_label("Normalized score")
    ax.text(0.02, 1.06, "(f)", transform=ax.transAxes, fontsize=12, fontweight="bold", va="top")
    fig.tight_layout()
    _save_figure(fig, output_path)


def generate_all_charts(results: list[dict[str, Any]], figures_dir: Path) -> dict[str, str]:
    figures_dir.mkdir(parents=True, exist_ok=True)
    chart_paths = {
        "throughput": figures_dir / "fig01_throughput.png",
        "commercial_kpis": figures_dir / "fig02_commercial_kpis.png",
        "screening": figures_dir / "fig03_screening_throughput.png",
        "models_stacked": figures_dir / "fig04_model_distribution.png",
        "kpi_heatmap": figures_dir / "fig05_kpi_heatmap.png",
    }
    plot_throughput_comparison(results, chart_paths["throughput"])
    plot_commercial_kpis(results, chart_paths["commercial_kpis"])
    plot_screening_throughput(results, chart_paths["screening"])
    plot_model_distribution_stacked(results, chart_paths["models_stacked"])
    plot_kpi_heatmap(results, chart_paths["kpi_heatmap"])
    return {key: path.with_suffix(".pdf").name for key, path in chart_paths.items()}


def generate_all_figures(payload: dict[str, Any], figures_dir: Path) -> dict[str, str]:
    """Generate charts from a full benchmark payload (includes precomputed KPIs)."""
    return generate_all_charts(payload["datasets"], figures_dir)
