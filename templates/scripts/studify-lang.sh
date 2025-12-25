#!/bin/bash
# Studify Lang - Annotate language feature code for Anki flashcards
# Usage: studify-lang.sh file1.java [file2.cpp ...]

source "$(dirname "$(readlink -f "$0")")/lib/common.sh"

echo "=== Studify Language ==="
echo ""

files=("$@")

abc_confirm_batch "Studify Language" "${files[@]}" || { echo "Cancelled."; exit 0; }

echo "Annotating language features..."
echo ""

# Process each file with the studify_lang prompt
success=0
failed=0

for file in "${files[@]}"; do
    echo "[File] $file"
    if $ABC_VENV_PYTHON "$ABC_SCRIPT_DIR/annotate_code.py" --prompt studify_lang --backup "$file"; then
        ((success++))
    else
        ((failed++))
        echo "  ✗ Failed"
    fi
    echo ""
done

echo "----------------------------------------"
echo "✅ Complete! Success: $success, Failed: $failed"

abc_notify "Studify Lang Complete" "Processed ${#files[@]} file(s)"

read -p "Press Enter to close..."
