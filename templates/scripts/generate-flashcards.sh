#!/bin/bash
# Generate Flashcards - Create Anki flashcards from files using AI
# Usage: generate-flashcards.sh file1 [file2 ...]

source "$(dirname "$(readlink -f "$0")")/lib/common.sh"

echo "=== Generate Anki Flashcards ==="
echo ""

files=("$@")

if [[ ${#files[@]} -eq 0 ]]; then
    echo "Error: No files provided"
    exit 1
fi

abc_confirm_batch "Generate Flashcards" "${files[@]}" || { echo "Cancelled."; exit 0; }

echo "Generating flashcards..."
echo ""

# Process all files
$ABC_VENV_PYTHON "$ABC_SCRIPT_DIR/generate_flashcards.py" "${files[@]}"
result=$?

echo ""

if [[ $result -eq 0 ]]; then
    abc_notify "Flashcards Generated" "Successfully processed ${#files[@]} file(s)"
else
    abc_notify "Flashcard Generation" "Completed with errors"
fi
