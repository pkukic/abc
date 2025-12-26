#!/bin/bash
# Solve MCQ Exam - Solve multiple choice questions with reasoning
# Uses Gemini Pro for careful analysis

VENV_DIR="$HOME/.local/share/abc/venv"
SCRIPT_DIR="$(dirname "$0")"

# Activate venv
source "$VENV_DIR/bin/activate"

# Run the Python script with all arguments (always keep tex)
python3 "$SCRIPT_DIR/solve_mcq.py" --keep-tex "$@"
