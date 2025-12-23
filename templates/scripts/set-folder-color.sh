#!/bin/bash
# Sets folder color in Dolphin by writing a .directory file
# Usage: set-folder-color.sh <color> <folder1> [folder2] ...
# color: red, green, or clear

COLOR="$1"
shift

for dir in "$@"; do
    if [[ -d "$dir" ]]; then
        if [[ "$COLOR" == "clear" ]]; then
            rm -f "$dir/.directory"
        else
            cat > "$dir/.directory" << EOF
[Desktop Entry]
Icon=folder-$COLOR
EOF
        fi
    fi
done
