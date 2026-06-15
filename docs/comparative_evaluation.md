# Comparative evaluation PDF

Professional LaTeX report comparing vanilla pandas, AdaptiveForecast-only, TimeSeriesFlow, and the full stack on three public datasets.

## Datasets

| Key | Source | Entity type |
|-----|--------|-------------|
| `intel` | [Intel Berkeley Lab](https://db.csail.mit.edu/labdata/labdata.html) | 54 sensor motes |
| `ett` | [ETT-small ETTh1](https://github.com/zhouhaoyi/ETDataset) | 7 load channels |
| `uci` | [UCI Household Power](https://archive.ics.uci.edu/dataset/235/individual+household+electric+power+consumption) | 3 sub-meters |

## Approaches compared

1. **Vanilla pandas** - manual `groupby` loop
2. **AdaptiveForecast loop** - profiling per entity, no orchestration
3. **TimeSeriesFlow** - `EntityRunner` with lightweight summaries
4. **Full stack** - `EntityRunner` + AdaptiveForecast routing and gates

## Generate report

```bash
pip install -e ".[dev]"
PYTHONPATH=src python examples/generate_comparative_report.py --compile-pdf
```

Or use the helper script:

```bash
chmod +x reports/build_comparative_pdf.sh
./reports/build_comparative_pdf.sh
```

## Outputs

| File | Description |
|------|-------------|
| `reports/comparative_evaluation/comparative_report.tex` | LaTeX source |
| `reports/comparative_evaluation/comparative_report.pdf` | Compiled PDF |
| `reports/comparative_evaluation/comparative_report.json` | Raw metrics |
| `reports/comparative_evaluation/figures/*.png` | Chart PNG previews |
| `reports/comparative_evaluation/figures/*.pdf` | Vector figures embedded in PDF |

## Commercial KPIs in the report

- Training jobs avoided (gate block rate)
- Routing diversity and unique models assigned
- Screening throughput (entities per second)
- Mean data coverage ratio
- Profiling cost factor vs vanilla pandas
- Portfolio summary across all datasets

## Phase 1 executive verdict

The report opens with a clear effectiveness section:

- Bottom-line executive summary
- When to use / when not to use the stack
- Decision table (Pass, Partial, Fail, Not tested) per product and criterion
- Per-product verdict with use-when and do-not-use-when bullets
- One-sentence conclusion per product (TimeSeriesFlow, AdaptiveForecast, full stack)

Forecast accuracy is explicitly marked **Not tested** until Phase 2 backtest work lands.

## Figure quality

Charts use publication styling: serif fonts, 300 DPI PNG, vector PDF companions, colorblind-safe palette, and panel labels (a-f). The LaTeX PDF embeds vector figures when compiled with tectonic or pdflatex. If no TeX compiler is available, a matplotlib PDF fallback is generated automatically.

## LaTeX requirement

Install one of:

- [MacTeX](https://www.tug.org/mactex/) (macOS)
- TeX Live (`apt install texlive-latex-extra` on Linux)
- [Tectonic](https://tectonic-typesetting.github.io/) (`brew install tectonic`)

## Quick offline smoke test

```bash
PYTHONPATH=src python examples/generate_comparative_report.py --datasets fixture
```
