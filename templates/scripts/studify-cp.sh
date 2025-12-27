#!/bin/bash
# Studify CP - Annotate MiniZinc constraint programming code for Anki flashcards
# Usage: studify-cp.sh file1.mzn [file2.mzn ...]

source "$(dirname "$(readlink -f "$0")")/lib/common.sh"

echo "=== Studify Constraint Programming ==="
echo ""

files=("$@")

abc_confirm_batch "Studify CP" "${files[@]}" || { echo "Cancelled."; exit 0; }

echo "Annotating MiniZinc models..."
echo ""

# Process each file with the studify_cp prompt
success=0
failed=0

for file in "${files[@]}"; do
    echo "[File] $file"
    if $ABC_VENV_PYTHON "$ABC_SCRIPT_DIR/annotate_code.py" --prompt studify_cp --backup "$file"; then
        ((success++))
    else
        ((failed++))
        echo "  ✗ Failed"
    fi
    echo ""
done

echo "----------------------------------------"
echo "✅ Complete! Success: $success, Failed: $failed"

abc_notify "Studify CP Complete" "Processed ${#files[@]} file(s)"

