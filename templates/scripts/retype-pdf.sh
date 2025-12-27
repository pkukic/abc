#!/bin/bash
# Retype to LaTeX - Convert PDF or images to clean LaTeX PDF
# Usage: retype-pdf.sh file1.pdf [file2.jpg ...]
# For images: all selected images are combined into one PDF

source "$(dirname "$(readlink -f "$0")")/lib/common.sh"

echo "=== Retype to LaTeX ==="
echo ""

files=("$@")

abc_confirm_batch "Retype to LaTeX" "${files[@]}" || { echo "Cancelled."; exit 0; }

echo "Starting conversion..."
echo ""

# Check if all files are images
all_images=true
for file in "${files[@]}"; do
    ext="${file##*.}"
    ext_lower=$(echo "$ext" | tr '[:upper:]' '[:lower:]')
    case "$ext_lower" in
        png|jpg|jpeg|webp|gif|bmp|tiff|tif) ;;
        *) all_images=false; break ;;
    esac
done

if $all_images && [ ${#files[@]} -gt 0 ]; then
    # All images - pass them all to the Python script at once
    echo "Processing ${#files[@]} image(s) as single document..."
    $ABC_VENV_PYTHON "$ABC_SCRIPT_DIR/retype_pdf.py" --keep-tex "${files[@]}"
    abc_notify "Retype Complete" "Processed ${#files[@]} image(s)"
else
    # PDF or mixed - process each file separately
    abc_process_files "retype_pdf.py" "--keep-tex" "${files[@]}"
    abc_notify "Retype Complete" "Processed ${#files[@]} file(s)"
fi


