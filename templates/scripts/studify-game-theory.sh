#!/bin/bash
# Studify Game Theory - Annotate game theory code for Anki flashcards
# Usage: studify-game-theory.sh file1.py [file2.cpp ...]

source "$(dirname "$(readlink -f "$0")")/lib/common.sh"

echo "=== Studify Game Theory ==="
echo ""

files=("$@")

abc_confirm_batch "Studify Game Theory" "${files[@]}" || { echo "Cancelled."; exit 0; }

echo "Annotating game theory code..."
echo ""

# Process each file with the studify_game_theory prompt
success=0
failed=0

for file in "${files[@]}"; do
    echo "[File] $file"
    if $ABC_VENV_PYTHON "$ABC_SCRIPT_DIR/annotate_code.py" --prompt studify_game_theory --backup "$file"; then
        ((success++))
    else
        ((failed++))
        echo "  ✗ Failed"
    fi
    echo ""
done

echo "----------------------------------------"
echo "✅ Complete! Success: $success, Failed: $failed"

abc_notify "Studify Game Theory Complete" "Processed ${#files[@]} file(s)"

