"""Build comparative evaluation charts, LaTeX, and PDF across three datasets."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples"))
sys.path.insert(0, str(ROOT / "src"))

from evaluation.benchmark import run_dataset_benchmarks  # noqa: E402
from evaluation.charts import generate_all_figures  # noqa: E402
from evaluation.commercial_kpis import attach_kpis_to_payload  # noqa: E402
from evaluation.datasets import (  # noqa: E402
    dataset_summary,
    load_ett_hourly,
    load_fixture,
    load_intel_berkeley,
    load_uci_household,
    normalize_entity_frame,
)
from evaluation.latex_report import generate_latex_report, write_json_report  # noqa: E402
from evaluation.pdf_fallback import build_pdf_from_figures  # noqa: E402
from evaluation.verdict import attach_verdict_to_payload  # noqa: E402

FIXTURE_PATH = ROOT / "examples" / "evaluation" / "fixtures" / "intel_sample.csv"
DEFAULT_CACHE = ROOT / ".evaluation_cache"
DEFAULT_OUTPUT_DIR = ROOT / "reports" / "comparative_evaluation"

DATASET_CONFIG = {
    "intel": {
        "title": "Intel Berkeley Lab",
        "description": (
            "Classic wireless sensor network with 54 motes and irregular sampling intervals."
        ),
        "infer_freq": True,
        "expected_freq": None,
        "max_entities": 30,
        "max_rows_per_entity": 4000,
    },
    "ett": {
        "title": "ETT Hourly (ETTh1)",
        "description": (
            "Seven electricity transformer load channels on an hourly grid."
        ),
        "infer_freq": False,
        "expected_freq": "1h",
        "max_entities": None,
        "max_rows_per_entity": 4000,
    },
    "uci": {
        "title": "UCI Household Power",
        "description": (
            "Three residential sub-meter channels with minute-level power readings."
        ),
        "infer_freq": True,
        "expected_freq": None,
        "max_entities": None,
        "max_rows_per_entity": 4000,
    },
}


def _load_dataset(name: str, cache_dir: Path) -> tuple[object, dict[str, object]]:
    if name == "fixture":
        frame = load_fixture(FIXTURE_PATH)
        config = {
            "title": "Fixture sample",
            "description": "Bundled offline sample for smoke testing.",
            "infer_freq": True,
            "expected_freq": None,
        }
        return frame, config

    config = DATASET_CONFIG[name]
    if name == "intel":
        frame = load_intel_berkeley(
            cache_dir,
            max_entities=config.get("max_entities"),
            max_rows_per_entity=config.get("max_rows_per_entity"),
        )
    elif name == "ett":
        frame = load_ett_hourly(
            cache_dir,
            max_entities=config.get("max_entities"),
            max_rows_per_entity=config.get("max_rows_per_entity"),
        )
    elif name == "uci":
        frame = load_uci_household(
            cache_dir,
            max_entities=config.get("max_entities"),
            max_rows_per_entity=config.get("max_rows_per_entity"),
        )
    else:
        raise ValueError(f"unknown dataset: {name}")
    return frame, config


def _build_conclusions(results: list[dict[str, object]]) -> list[str]:
    """Placeholder; replaced by attach_verdict_to_payload after KPIs are computed."""
    _ = results
    return []


def compile_pdf(tex_path: Path, payload: dict[str, object] | None = None) -> Path:
    pdf_path = tex_path.with_suffix(".pdf")
    figures_dir = tex_path.parent / "figures"

    tectonic = shutil.which("tectonic")
    if tectonic is not None:
        try:
            subprocess.run(
                [tectonic, tex_path.name],
                cwd=tex_path.parent,
                check=True,
                capture_output=True,
            )
            if pdf_path.exists():
                return pdf_path
        except subprocess.CalledProcessError:
            pass

    pdflatex = shutil.which("pdflatex")
    if pdflatex is not None:
        for _ in range(2):
            subprocess.run(
                [pdflatex, "-interaction=nonstopmode", tex_path.name],
                cwd=tex_path.parent,
                check=False,
                capture_output=True,
            )
        if pdf_path.exists():
            return pdf_path

    if payload is not None:
        build_pdf_from_figures(payload, figures_dir, pdf_path)
        return pdf_path

    raise RuntimeError(
        "No LaTeX compiler found and PDF fallback unavailable. "
        "Install tectonic or TeX Live, then rerun."
    )


def build_report(
    *,
    dataset_names: list[str],
    cache_dir: Path,
    output_dir: Path,
    workers: int,
    compile_pdf_flag: bool,
) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    figures_dir = output_dir / "figures"
    results: list[dict[str, object]] = []

    for name in dataset_names:
        frame, config = _load_dataset(name, cache_dir)
        normalized, entity_key, _ = normalize_entity_frame(frame)
        summary = dataset_summary(normalized, entity_key=entity_key)
        benchmark = run_dataset_benchmarks(
            frame,
            dataset_name=config["title"],
            cache_csv=cache_dir / f"{name}_benchmark.csv",
            infer_freq=bool(config["infer_freq"]),
            expected_freq=config.get("expected_freq"),
            workers=workers,
        )
        benchmark["summary"] = summary
        benchmark["description"] = config["description"]
        benchmark["dataset_key"] = name
        results.append(benchmark)

    payload: dict[str, object] = {
        "generated_on": date.today().isoformat(),
        "datasets": results,
        "conclusions": _build_conclusions(results),
    }
    attach_kpis_to_payload(payload)
    attach_verdict_to_payload(payload)

    figure_names = generate_all_figures(payload, figures_dir)
    payload["figures"] = figure_names

    write_json_report(output_dir / "comparative_report.json", payload)
    tex_path = output_dir / "comparative_report.tex"
    generate_latex_report(payload, figures=figure_names, output_path=tex_path)

    pdf_path: Path | None = None
    if compile_pdf_flag:
        pdf_path = compile_pdf(tex_path, payload)
        payload["pdf"] = str(pdf_path)
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate comparative LaTeX/PDF evaluation report")
    parser.add_argument(
        "--datasets",
        nargs="+",
        default=["intel", "ett", "uci"],
        choices=["intel", "ett", "uci", "fixture"],
    )
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument(
        "--compile-pdf",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Compile LaTeX to PDF if a compiler exists (default: on)",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    compile_flag = args.compile_pdf
    payload = build_report(
        dataset_names=args.datasets,
        cache_dir=args.cache_dir,
        output_dir=args.output_dir,
        workers=args.workers,
        compile_pdf_flag=compile_flag,
    )
    print(json.dumps({"output_dir": str(args.output_dir), "figures": payload["figures"]}, indent=2))
    if compile_flag and "pdf" in payload:
        print(f"PDF written to {payload['pdf']}")
    else:
        print(f"LaTeX written to {args.output_dir / 'comparative_report.tex'}")
        print("Compile with: cd reports/comparative_evaluation && tectonic comparative_report.tex")


if __name__ == "__main__":
    main()
