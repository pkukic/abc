#!/bin/bash
# Retype PDF - Convert any PDF (handwritten or printed) to clean LaTeX
# Usage: retype-pdf.sh file1.pdf [file2.pdf ...]

source "$(dirname "$(readlink -f "$0")")/lib/common.sh"

echo "=== Retype PDF ==="
echo ""

files=("$@")

abc_confirm_batch "Retype to LaTeX PDF" "${files[@]}" || { echo "Cancelled."; exit 0; }

echo "Starting conversion..."
echo ""

abc_process_files "retype_pdf.py" "--keep-tex" "${files[@]}"

abc_notify "Retype Complete" "Processed ${#files[@]} file(s)"

read -p "Press Enter to close..."
