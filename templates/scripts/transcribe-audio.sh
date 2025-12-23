#!/bin/bash
# Transcribes audio/video files using insanely-fast-whisper
# Usage: transcribe-audio.sh file1.mp3 [file2.webm ...]
# Output: Creates a .txt file next to each input file

for file in "$@"; do
    if [[ -f "$file" ]]; then
        json_output="${file%.*}_transcript.json"
        txt_output="${file%.*}_transcript.txt"
        
        echo "Transcribing: $file"
        
        insanely-fast-whisper \
            --file-name "$file" \
            --transcript-path "$json_output" \
            --task transcribe
        
        # Extract just the text from JSON and save as .txt
        if [[ -f "$json_output" ]]; then
            python3 -c "
import json

with open('$json_output', 'r') as f:
    data = json.load(f)

if 'text' in data:
    print(data['text'])
elif 'chunks' in data:
    for chunk in data['chunks']:
        print(chunk.get('text', ''))
" > "$txt_output"
            
            echo "✓ Saved transcript to: $txt_output"
        else
            echo "✗ Transcription failed for: $file"
        fi
    fi
done

# Show notification when done
if command -v notify-send &> /dev/null; then
    notify-send "Transcription Complete" "Finished transcribing $# file(s)"
fi
