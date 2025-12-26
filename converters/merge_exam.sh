#!/bin/bash
# Installs the Merge Exam context menu

MENU_DIR="$HOME/.local/share/kio/servicemenus"
BIN_DIR="$HOME/.local/bin"

mkdir -p "$MENU_DIR"
mkdir -p "$BIN_DIR"

# Install helper scripts
cp "$TEMPLATE_DIR/scripts/merge-exam.sh" "$BIN_DIR/"
cp "$TEMPLATE_DIR/scripts/merge_exam.py" "$BIN_DIR/"
chmod +x "$BIN_DIR/merge-exam.sh"
chmod +x "$BIN_DIR/merge_exam.py"

# Copy .env file for API keys if it exists
if [[ -f "$SCRIPT_DIR/.env" ]]; then
    cp "$SCRIPT_DIR/.env" "$BIN_DIR/"
fi

# Install desktop entry
cp "$TEMPLATE_DIR/desktop/merge-exam.desktop" "$MENU_DIR/"
chmod +x "$MENU_DIR/merge-exam.desktop"

echo "✓ Merge Exam menu installed"
