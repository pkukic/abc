#!/bin/bash
# Studify OS - Annotate OS-level C code for Anki flashcards
# Usage: studify-os.sh file1.c [file2.c ...]

source "$(dirname "$(readlink -f "$0")")/lib/common.sh"

echo "=== Studify OS ==="
echo ""

files=("$@")

abc_confirm_batch "Studify OS" "${files[@]}" || { echo "Cancelled."; exit 0; }

echo "Annotating OS code..."
echo ""

# Process each file with the studify_os prompt
success=0
failed=0

for file in "${files[@]}"; do
    echo "[File] $file"
    if $ABC_VENV_PYTHON "$ABC_SCRIPT_DIR/annotate_code.py" --prompt studify_os --backup "$file"; then
        ((success++))
    else
        ((failed++))
        echo "  ✗ Failed"
    fi
    echo ""
done

echo "----------------------------------------"
echo "✅ Complete! Success: $success, Failed: $failed"

abc_notify "Studify OS Complete" "Processed ${#files[@]} file(s)"

read -p "Press Enter to close..."
