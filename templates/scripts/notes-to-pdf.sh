#!/bin/bash
# Convert handwritten PDF notes to clean LaTeX PDF
# Usage: notes-to-pdf.sh file1.pdf [file2.pdf ...]

source "$(dirname "$(readlink -f "$0")")/lib/common.sh"

echo "=== Handwritten Notes to PDF ==="
echo ""

files=("$@")

abc_confirm_batch "Notes to LaTeX PDF" "${files[@]}" || { echo "Cancelled."; exit 0; }

echo "Starting conversion..."
echo ""

abc_process_files "notes_to_pdf.py" "--keep-tex" "${files[@]}"

abc_notify "Notes Conversion Complete" "Processed ${#files[@]} file(s)"

read -p "Press Enter to close..."
