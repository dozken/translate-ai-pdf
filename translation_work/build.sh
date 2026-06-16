#!/usr/bin/env bash
# Build the book PDF from the canonical translation markdown.
# Pipeline: clean.md --(re-tier headings)--> book.md --(pandoc+tectonic)--> PDF
# Engine: pandoc + tectonic (LaTeX, book class) — industry-standard book typesetting.
set -euo pipefail
cd "$(dirname "$0")"
VENV=../.venv/bin/python

# 1. Re-tier flat ## headings into parts/chapters/subheads + fix superscripts/Arabic
"$VENV" build_pdf.py

# 2. Typeset
pandoc book.md -o Hizmetin_Esaslari_RU.pdf \
  --pdf-engine=tectonic \
  --top-level-division=part \
  --toc --toc-depth=1 \
  -H preamble.tex \
  -V documentclass=book -V classoption=oneside -V fontsize=12pt -V mainfont="PT Serif" \
  -V geometry:a4paper \
  -V geometry:top=24mm -V geometry:bottom=22mm -V geometry:left=26mm -V geometry:right=26mm \
  -M lang=ru \
  -M title="Основы служения" \
  -M subtitle="Hizmetin Esasları" \
  -M author="перевод с турецкого"

echo "Built Hizmetin_Esaslari_RU.pdf"
