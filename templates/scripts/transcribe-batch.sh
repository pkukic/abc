#!/bin/bash
# Batch transcribe multiple files - choose monologue/dialogue for each
# Usage: transcribe-batch.sh file1.mp3 file2.webm ...

source "$(dirname "$(readlink -f "$0")")/lib/common.sh"

echo "=== Batch Transcription Setup ==="
echo ""

# Arrays to store files and their speaker counts
declare -a files_to_process
declare -a speaker_counts

# Phase 1: Collect choices upfront
for file in "$@"; do
    if [[ -f "$file" ]]; then
        filename=$(basename "$file")
        
        if command -v zenity &> /dev/null; then
            choice=$(zenity --list --radiolist \
                --title="Transcribe: $filename" \
                --text="Select transcription type:" \
                --column="" --column="Value" --column="Option" \
                TRUE "1" "Monologue (1 speaker)" \
                FALSE "2" "Dialogue (2 speakers)" \
                FALSE "0" "Skip this file" \
                --hide-column=2 --print-column=2 \
                --width=400 --height=250 \
                2>/dev/null)
        else
            echo "File: $filename"
            echo "  1) Monologue  2) Dialogue  0) Skip"
            read -p "Choice: " choice
        fi
        
        if [[ "$choice" == "1" || "$choice" == "2" ]]; then
            files_to_process+=("$file")
            speaker_counts+=("$choice")
            echo "✓ $filename → $choice speaker(s)"
        else
            echo "○ $filename → skipped"
        fi
    fi
done

echo ""
echo "Selected ${#files_to_process[@]} file(s) for transcription."

if [[ ${#files_to_process[@]} -eq 0 ]]; then
    echo "No files selected."
    exit 0
fi

# Confirm before processing
abc_confirm_batch "Start Transcription?" "${files_to_process[@]}" || { echo "Cancelled."; exit 0; }

echo ""
echo "Starting transcription..."
echo ""

# Phase 2: Process all files
for i in "${!files_to_process[@]}"; do
    file="${files_to_process[$i]}"
    num_speakers="${speaker_counts[$i]}"
    filename=$(basename "$file")
    
    echo "[$((i+1))/${#files_to_process[@]}] $filename ($num_speakers speaker)..."
    
    txt_output="${file%.*}_transcript.txt"
    $ABC_VENV_PYTHON "$ABC_SCRIPT_DIR/transcribe.py" --num-speakers "$num_speakers" "$file" --output "$txt_output"
    
    if [[ -f "$txt_output" ]]; then
        echo "    ✓ Saved: $txt_output"
    else
        echo "    ✗ Failed"
    fi
done

echo ""
echo "----------------------------------------"
echo "✅ Batch transcription complete!"

abc_notify "Transcription Complete" "Processed ${#files_to_process[@]} file(s)"

read -p "Press Enter to close..."
