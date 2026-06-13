#!/usr/bin/env bash
# Build the comparative evaluation PDF from generated LaTeX.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPORT_DIR="$ROOT/reports/comparative_evaluation"

cd "$ROOT"
MPLCONFIGDIR="${MPLCONFIGDIR:-/tmp/mpl}"
export MPLCONFIGDIR
PYTHONPATH=src python examples/generate_comparative_report.py "$@"

REPORT_DIR="$ROOT/reports/comparative_evaluation"
if command -v tectonic >/dev/null 2>&1; then
  cd "$REPORT_DIR"
  tectonic comparative_report.tex
  echo "PDF: $REPORT_DIR/comparative_report.pdf"
elif command -v pdflatex >/dev/null 2>&1; then
  cd "$REPORT_DIR"
  pdflatex -interaction=nonstopmode comparative_report.tex >/dev/null
  pdflatex -interaction=nonstopmode comparative_report.tex >/dev/null
  echo "PDF: $REPORT_DIR/comparative_report.pdf"
else
  echo "Install tectonic or pdflatex, then run:"
  echo "  cd $REPORT_DIR && tectonic comparative_report.tex"
fi
