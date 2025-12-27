#!/bin/bash
# Fix Xournal PDF - Update background PDF and export to _notes.pdf
# Usage: fix-xournal.sh file.xoj background.pdf

source "$(dirname "$(readlink -f "$0")")/lib/common.sh"

echo "=== Fix Xournal PDF ==="
echo ""

# Parse arguments - expect exactly one .xoj/.xopp and one .pdf
xoj_file=""
pdf_file=""

for file in "$@"; do
    ext="${file##*.}"
    ext_lower=$(echo "$ext" | tr '[:upper:]' '[:lower:]')
    case "$ext_lower" in
        xoj|xopp)
            xoj_file="$file"
            ;;
        pdf)
            pdf_file="$file"
            ;;
    esac
done

if [[ -z "$xoj_file" ]] || [[ -z "$pdf_file" ]]; then
    echo "Error: Please select exactly one .xoj/.xopp file and one .pdf file"
    echo "  xoj_file: $xoj_file"
    echo "  pdf_file: $pdf_file"
    
    exit 1
fi

echo "Xournal: $xoj_file"
echo "PDF: $pdf_file"
echo ""

$ABC_VENV_PYTHON "$ABC_SCRIPT_DIR/fix_xournal.py" --save "$xoj_file" "$pdf_file"

abc_notify "Xournal Fix Complete" "Exported notes PDF"


