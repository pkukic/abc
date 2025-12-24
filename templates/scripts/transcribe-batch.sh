#!/bin/bash
# Batch transcribe multiple files - collect all choices first, then process
# Usage: transcribe-batch.sh file1.mp3 file2.webm ...

SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
VENV_PYTHON="$HOME/.local/share/abc/venv/bin/python"

# Arrays to store files and their speaker counts
declare -a files_to_process
declare -a speaker_counts

echo "=== Batch Transcription Setup ==="
echo ""
echo "First, select transcription type for each file..."
echo ""

# Phase 1: Collect all choices upfront
for file in "$@"; do
    if [[ -f "$file" ]]; then
        filename=$(basename "$file")
        
        # Ask user for speaker count
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
        elif command -v kdialog &> /dev/null; then
            choice=$(kdialog --radiolist "Transcribe: $filename" \
                1 "Monologue (1 speaker)" on \
                2 "Dialogue (2 speakers)" off \
                0 "Skip this file" off \
                2>/dev/null)
        else
            # Terminal fallback
            echo "File: $filename"
            echo "  1) Monologue (1 speaker)"
            echo "  2) Dialogue (2 speakers)"
            echo "  0) Skip"
            read -p "Choice [1/2/0]: " choice
        fi
        
        # Store choice if not skipped
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
echo "----------------------------------------"
echo "Selected ${#files_to_process[@]} file(s) for transcription."
echo ""

if [[ ${#files_to_process[@]} -eq 0 ]]; then
    echo "No files selected. Exiting."
    exit 0
fi

# Show summary and confirm
if command -v zenity &> /dev/null; then
    summary="Files to transcribe:\n"
    for i in "${!files_to_process[@]}"; do
        fname=$(basename "${files_to_process[$i]}")
        speakers="${speaker_counts[$i]}"
        summary+="• $fname ($speakers speaker)\n"
    done
    summary+="\nThis may take a while. You can close this terminal and the process will continue in background."
    
    zenity --question --title="Start Transcription?" \
        --text="$summary" \
        --width=400 \
        2>/dev/null
    
    if [[ $? -ne 0 ]]; then
        echo "Cancelled."
        exit 0
    fi
fi

echo "Starting transcription... (you can close this window)"
echo ""

# Phase 2: Process all files
for i in "${!files_to_process[@]}"; do
    file="${files_to_process[$i]}"
    num_speakers="${speaker_counts[$i]}"
    filename=$(basename "$file")
    
    echo "[$((i+1))/${#files_to_process[@]}] $filename ($num_speakers speaker)..."
    
    txt_output="${file%.*}_transcript.txt"
    "$VENV_PYTHON" "$SCRIPT_DIR/transcribe.py" --num-speakers "$num_speakers" "$file" --output "$txt_output"
    
    if [[ -f "$txt_output" ]]; then
        echo "    ✓ Saved: $txt_output"
    else
        echo "    ✗ Failed"
    fi
done

echo ""
echo "----------------------------------------"
echo "✅ Batch transcription complete!"

if command -v notify-send &> /dev/null; then
    notify-send "Transcription Complete" "Finished transcribing ${#files_to_process[@]} file(s)"
fi

read -p "Press Enter to close..."
