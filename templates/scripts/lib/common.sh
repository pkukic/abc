#!/bin/bash
# Shared functions for ABC shell scripts
# Source this file: source "$(dirname "$0")/lib/common.sh"

# Get the directory where scripts are installed
ABC_SCRIPT_DIR="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/.."
ABC_VENV_PYTHON="$HOME/.local/share/abc/venv/bin/python"

# Show a confirmation dialog for batch operations
# Usage: abc_confirm_batch "Title" "${files[@]}"
# Returns 0 if confirmed, 1 if cancelled
abc_confirm_batch() {
    local title="$1"
    shift
    local files=("$@")
    local count=${#files[@]}
    
    if [[ $count -le 1 ]]; then
        return 0  # No confirmation needed for single file
    fi
    
    if command -v zenity &> /dev/null; then
        local summary="Files to process:\n\n"
        for file in "${files[@]}"; do
            if [[ -f "$file" ]]; then
                summary+="• $(basename "$file")\n"
            fi
        done
        summary+="\nThis may take a while."
        
        zenity --question --title="$title" \
            --text="$summary" \
            --width=400 \
            2>/dev/null
        
        return $?
    fi
    
    return 0  # No dialog available, proceed
}

# Show completion notification
# Usage: abc_notify "Title" "Message"
abc_notify() {
    local title="$1"
    local message="$2"
    
    if command -v notify-send &> /dev/null; then
        notify-send "$title" "$message"
    fi
}

# Process files with a Python script
# Usage: abc_process_files "script.py" "extra_args" "${files[@]}"
abc_process_files() {
    local script="$1"
    local extra_args="$2"
    shift 2
    local files=("$@")
    local count=${#files[@]}
    local success=0
    local failed=0
    
    for file in "${files[@]}"; do
        if [[ -f "$file" ]]; then
            local filename=$(basename "$file")
            echo "[$((success + failed + 1))/$count] $filename"
            
            if $ABC_VENV_PYTHON "$ABC_SCRIPT_DIR/$script" $extra_args "$file"; then
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
    
    # Return number of failures
    return $failed
}
