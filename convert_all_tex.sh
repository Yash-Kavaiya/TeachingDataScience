#!/bin/bash
# Quick script to convert all .tex files to PDF
# Usage: ./convert_all_tex.sh [options]
#
# Options:
#   --dry-run     : Show files without converting
#   --workers N   : Use N parallel workers (default: 4)
#   --pattern P   : Only convert files matching pattern

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if pdflatex is installed
if ! command -v pdflatex &> /dev/null; then
    echo "pdflatex not found. Installing texlive..."
    sudo apt-get update
    sudo apt-get install -y texlive-latex-base texlive-latex-extra texlive-fonts-recommended texlive-science
fi

# Create Artifacts directory
mkdir -p Artifacts/PDFs

echo "========================================"
echo "LaTeX to PDF Converter"
echo "========================================"
echo "Source: $SCRIPT_DIR"
echo "Output: $SCRIPT_DIR/Artifacts/PDFs"
echo "========================================"

# Run the Python converter
python3 tex_to_pdf_converter.py \
    --source "$SCRIPT_DIR" \
    --output "$SCRIPT_DIR/Artifacts/PDFs" \
    "$@"

echo ""
echo "Conversion complete! PDFs saved to: Artifacts/PDFs/"
