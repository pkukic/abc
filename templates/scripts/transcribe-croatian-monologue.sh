#!/bin/bash
# Transcribe Croatian monologue (1 speaker)
# Usage: transcribe-croatian-monologue.sh file1.mp3 [file2.webm ...]

source "$(dirname "$(readlink -f "$0")")/lib/common.sh"

MODEL="GoranS/whisper-large-v3-turbo-hr-parla"

echo "=== Croatian Transcription (Monologue) ==="
echo "Using model: $MODEL"
echo ""

for file in "$@"; do
    if [[ -f "$file" ]]; then
        echo "[File] $file"
        txt_output="${file%.*}_transcript.txt"
        $ABC_VENV_PYTHON "$ABC_SCRIPT_DIR/transcribe.py" --model "$MODEL" --num-speakers 1 --language croatian "$file" --output "$txt_output"
        
        if [[ -f "$txt_output" ]]; then
            echo "✓ Saved: $txt_output"
        else
            echo "✗ Failed: $file"
        fi
        echo ""
    fi
done

abc_notify "Croatian Transcription Complete" "Finished transcribing $# file(s)"
