#!/bin/bash
# Clean and comment code files using Gemini LLM
# Usage: clean-code.sh file1.py [file2.js ...]

source "$(dirname "$(readlink -f "$0")")/lib/common.sh"

echo "=== Batch Code Cleaning ==="
echo ""

files=("$@")

abc_confirm_batch "Clean & Comment Code" "${files[@]}" || { echo "Cancelled."; exit 0; }

echo "Starting code cleaning..."
echo ""

abc_process_files "clean_code.py" "--backup" "${files[@]}"

abc_notify "Code Cleaning Complete" "Processed ${#files[@]} file(s)"

read -p "Press Enter to close..."
