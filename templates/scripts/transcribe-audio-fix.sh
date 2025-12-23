#!/bin/bash
# Transcribes audio/video files using faster-whisper with LLM correction
# Usage: transcribe-audio-fix.sh file1.mp3 [file2.webm ...]
# Output: Creates a .txt file next to each input file

SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
VENV_PYTHON="$HOME/.local/share/abc/venv/bin/python"

for file in "$@"; do
    if [[ -f "$file" ]]; then
        txt_output="${file%.*}_transcript.txt"
        
        "$VENV_PYTHON" "$SCRIPT_DIR/transcribe.py" "$file" --fix --output "$txt_output"
        
        if [[ -f "$txt_output" ]]; then
            echo "✓ Saved transcript to: $txt_output"
        else
            echo "✗ Transcription failed for: $file"
        fi
    fi
done

# Show notification when done
if command -v notify-send &> /dev/null; then
    notify-send "Transcription Complete" "Finished transcribing $# file(s) with LLM correction"
fi
