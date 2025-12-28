#!/bin/bash
# Transcribe monologue (1 speaker)
# Usage: transcribe-monologue.sh file1.mp3 [file2.webm ...]

source "$(dirname "$(readlink -f "$0")")/lib/common.sh"

for file in "$@"; do
    if [[ -f "$file" ]]; then
        txt_output="${file%.*}_transcript.txt"
        $ABC_VENV_PYTHON "$ABC_SCRIPT_DIR/transcribe.py" --num-speakers 1 --language english "$file" --output "$txt_output"
        
        if [[ -f "$txt_output" ]]; then
            echo "✓ Saved: $txt_output"
        else
            echo "✗ Failed: $file"
        fi
    fi
done

abc_notify "Transcription Complete" "Finished transcribing $# file(s)"
