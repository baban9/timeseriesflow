"""Matplotlib charts for the comparative evaluation PDF."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np

MODE_LABELS = {
    "vanilla_pandas": "Vanilla pandas",
    "adaptiveforecast_loop": "AdaptiveForecast loop",
    "timeseriesflow": "TimeSeriesFlow",
    "full_stack": "Full stack",
}

MODE_COLORS = {
    "vanilla_pandas": "#6c757d",
    "adaptiveforecast_loop": "#fd7e14",
    "timeseriesflow": "#0d6efd",
    "full_stack": "#198754",
}


def _mode_lookup(runs: list[dict[str, Any]], mode: str) -> dict[str, Any]:
    for run in runs:
        if run["mode"] == mode:
            return run
    raise KeyError(mode)


def plot_throughput_comparison(
    results: list[dict[str, Any]],
    output_path: Path,
) -> None:
    datasets = [item["dataset"] for item in results]
    modes = list(MODE_LABELS.keys())
    x = np.arange(len(datasets))
    width = 0.18

    fig, ax = plt.subplots(figsize=(10, 5))
    for index, mode in enumerate(modes):
        values = [_mode_lookup(item["runs"], mode)["entities_per_second"] for item in results]
        ax.bar(
            x + (index - 1.5) * width,
            values,
            width,
            label=MODE_LABELS[mode],
            color=MODE_COLORS[mode],
        )

    ax.set_title("Entity throughput by approach and dataset")
    ax.set_ylabel("Entities per second")
    ax.set_xticks(x)
    ax.set_xticklabels(datasets, rotation=15, ha="right")
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def plot_elapsed_time_comparison(
    results: list[dict[str, Any]],
    output_path: Path,
) -> None:
    datasets = [item["dataset"] for item in results]
    modes = list(MODE_LABELS.keys())
    x = np.arange(len(datasets))
    width = 0.18

    fig, ax = plt.subplots(figsize=(10, 5))
    for index, mode in enumerate(modes):
        values = [_mode_lookup(item["runs"], mode)["elapsed_seconds"] for item in results]
        ax.bar(
            x + (index - 1.5) * width,
            values,
            width,
            label=MODE_LABELS[mode],
            color=MODE_COLORS[mode],
        )

    ax.set_title("Wall-clock runtime by approach and dataset")
    ax.set_ylabel("Seconds")
    ax.set_xticks(x)
    ax.set_xticklabels(datasets, rotation=15, ha="right")
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def plot_routing_metrics(
    results: list[dict[str, Any]],
    output_path: Path,
) -> None:
    datasets = [item["dataset"] for item in results]
    gate_rates: list[float] = []
    diversity_rates: list[float] = []
    unique_models: list[int] = []

    for item in results:
        full_stack = _mode_lookup(item["runs"], "full_stack")
        gate_rates.append(float(full_stack["gate_pass_rate"] or 0.0))
        diversity_rates.append(float(full_stack["routing_diversity_rate"] or 0.0))
        unique_models.append(int(full_stack["unique_models"] or 0))

    x = np.arange(len(datasets))
    width = 0.25
    fig, ax1 = plt.subplots(figsize=(10, 5))
    ax2 = ax1.twinx()

    ax1.bar(x - width, gate_rates, width, label="Gate pass rate", color="#20c997")
    ax1.bar(x, diversity_rates, width, label="Routing diversity", color="#6610f2")
    ax2.plot(x + width, unique_models, "o-", color="#dc3545", label="Unique models")

    ax1.set_ylim(0, 1.05)
    ax1.set_title("AdaptiveForecast routing outcomes (full stack)")
    ax1.set_ylabel("Rate")
    ax2.set_ylabel("Unique models")
    ax1.set_xticks(x)
    ax1.set_xticklabels(datasets, rotation=15, ha="right")
    ax1.grid(axis="y", alpha=0.25)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper right", fontsize=8)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def plot_model_distribution(
    results: list[dict[str, Any]],
    output_path: Path,
) -> None:
    fig, axes = plt.subplots(1, len(results), figsize=(4 * len(results), 4), sharey=True)
    if len(results) == 1:
        axes = [axes]

    for axis, item in zip(axes, results, strict=True):
        full_stack = _mode_lookup(item["runs"], "full_stack")
        counts = full_stack.get("model_distribution") or {}
        if not counts:
            counts = {"none": 1}
        labels = list(counts.keys())
        values = [counts[label] for label in labels]
        axis.barh(labels, values, color="#0d6efd")
        axis.set_title(item["dataset"])
        axis.set_xlabel("Entities")
        axis.grid(axis="x", alpha=0.25)

    fig.suptitle("Assigned model families per dataset (full stack)")
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def generate_all_charts(results: list[dict[str, Any]], figures_dir: Path) -> dict[str, str]:
    figures_dir.mkdir(parents=True, exist_ok=True)
    chart_paths = {
        "throughput": figures_dir / "throughput_comparison.png",
        "elapsed": figures_dir / "elapsed_comparison.png",
        "routing": figures_dir / "routing_metrics.png",
        "models": figures_dir / "model_distribution.png",
    }
    plot_throughput_comparison(results, chart_paths["throughput"])
    plot_elapsed_time_comparison(results, chart_paths["elapsed"])
    plot_routing_metrics(results, chart_paths["routing"])
    plot_model_distribution(results, chart_paths["models"])
    return {key: path.name for key, path in chart_paths.items()}
