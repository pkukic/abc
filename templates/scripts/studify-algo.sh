#!/bin/bash
# Studify Algo - Annotate algorithmic code for Anki flashcards
# Usage: studify-algo.sh file1.py [file2.cpp ...]

source "$(dirname "$(readlink -f "$0")")/lib/common.sh"

echo "=== Studify Algorithm ==="
echo ""

files=("$@")

abc_confirm_batch "Studify Algorithm" "${files[@]}" || { echo "Cancelled."; exit 0; }

echo "Annotating algorithms..."
echo ""

# Process each file with the studify_algo prompt
success=0
failed=0

for file in "${files[@]}"; do
    echo "[File] $file"
    if $ABC_VENV_PYTHON "$ABC_SCRIPT_DIR/annotate_code.py" --prompt studify_algo --backup "$file"; then
        ((success++))
    else
        ((failed++))
        echo "  ✗ Failed"
    fi
    echo ""
done

echo "----------------------------------------"
echo "✅ Complete! Success: $success, Failed: $failed"

abc_notify "Studify Algo Complete" "Processed ${#files[@]} file(s)"

read -p "Press Enter to close..."
