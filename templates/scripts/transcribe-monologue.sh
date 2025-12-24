#!/bin/bash
# Transcribes audio/video with 1 speaker (monologue/lecture)
# Usage: transcribe-monologue.sh file1.mp3 [file2.webm ...]

SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
VENV_PYTHON="$HOME/.local/share/abc/venv/bin/python"

for file in "$@"; do
    if [[ -f "$file" ]]; then
        txt_output="${file%.*}_transcript.txt"
        
        "$VENV_PYTHON" "$SCRIPT_DIR/transcribe.py" --num-speakers 1 "$file" --output "$txt_output"
        
        if [[ -f "$txt_output" ]]; then
            echo "✓ Saved transcript to: $txt_output"
        else
            echo "✗ Transcription failed for: $file"
        fi
    fi
done

if command -v notify-send &> /dev/null; then
    notify-send "Transcription Complete" "Finished transcribing $# file(s)"
fi
