#!/bin/bash
# Studify DSP - Annotate digital signal processing code for Anki flashcards
# Usage: studify-dsp.sh file1.py [file2.py ...]

source "$(dirname "$(readlink -f "$0")")/lib/common.sh"

echo "=== Studify DSP ==="
echo ""

files=("$@")

abc_confirm_batch "Studify DSP" "${files[@]}" || { echo "Cancelled."; exit 0; }

echo "Annotating DSP code..."
echo ""

# Process each file with the studify_dsp prompt
success=0
failed=0

for file in "${files[@]}"; do
    echo "[File] $file"
    if $ABC_VENV_PYTHON "$ABC_SCRIPT_DIR/annotate_code.py" --prompt studify_dsp --backup "$file"; then
        ((success++))
    else
        ((failed++))
        echo "  ✗ Failed"
    fi
    echo ""
done

echo "----------------------------------------"
echo "✅ Complete! Success: $success, Failed: $failed"

abc_notify "Studify DSP Complete" "Processed ${#files[@]} file(s)"

