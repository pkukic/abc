#!/bin/bash
# Merge Exam - Combine answers PDF with solutions text
# Uses Gemini AI to merge into formatted LaTeX

VENV_DIR="$HOME/.local/share/abc/venv"
SCRIPT_DIR="$(dirname "$0")"

# Activate venv
source "$VENV_DIR/bin/activate"

# Run the Python script with all arguments
python3 "$SCRIPT_DIR/merge_exam.py" "$@"
