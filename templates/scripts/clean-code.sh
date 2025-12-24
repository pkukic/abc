#!/bin/bash
# Batch clean and comment code files using Gemini LLM
# Shows confirmation before processing
# Usage: clean-code.sh file1.py [file2.js ...]

SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
VENV_PYTHON="$HOME/.local/share/abc/venv/bin/python"

echo "=== Batch Code Cleaning ==="
echo ""

# Collect files to process
files=("$@")
count=${#files[@]}

if [[ $count -eq 0 ]]; then
    echo "No files provided."
    exit 0
fi

echo "Files to process: $count"
echo ""

# Show summary and confirm
if command -v zenity &> /dev/null && [[ $count -gt 1 ]]; then
    summary="Files to clean and comment:\n\n"
    for file in "${files[@]}"; do
        if [[ -f "$file" ]]; then
            summary+="• $(basename "$file")\n"
        fi
    done
    summary+="\nBackups will be created (.bak files).\nThis may take a while for large files."
    
    zenity --question --title="Clean & Comment Code" \
        --text="$summary" \
        --width=400 \
        2>/dev/null
    
    if [[ $? -ne 0 ]]; then
        echo "Cancelled."
        exit 0
    fi
fi

echo "Starting code cleaning..."
echo ""

# Process each file
success=0
failed=0

for file in "${files[@]}"; do
    if [[ -f "$file" ]]; then
        filename=$(basename "$file")
        echo "[$((success + failed + 1))/$count] $filename"
        
        # Create backup and process
        "$VENV_PYTHON" "$SCRIPT_DIR/clean_code.py" --backup "$file"
        
        if [[ $? -eq 0 ]]; then
            echo "    ✓ Done"
            ((success++))
        else
            echo "    ✗ Failed"
            ((failed++))
        fi
        echo ""
    fi
done

echo "----------------------------------------"
echo "✅ Complete! Success: $success, Failed: $failed"

if command -v notify-send &> /dev/null; then
    notify-send "Code Cleaning Complete" "Processed $success of $count file(s)"
fi

read -p "Press Enter to close..."
