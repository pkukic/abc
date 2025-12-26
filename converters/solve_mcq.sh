#!/bin/bash
# Installs the Solve MCQ Exam context menu

MENU_DIR="$HOME/.local/share/kio/servicemenus"
BIN_DIR="$HOME/.local/bin"

mkdir -p "$MENU_DIR"
mkdir -p "$BIN_DIR"

# Install helper scripts
cp "$TEMPLATE_DIR/scripts/solve-mcq.sh" "$BIN_DIR/"
cp "$TEMPLATE_DIR/scripts/solve_mcq.py" "$BIN_DIR/"
chmod +x "$BIN_DIR/solve-mcq.sh"
chmod +x "$BIN_DIR/solve_mcq.py"

# Copy .env file for API keys if it exists
if [[ -f "$SCRIPT_DIR/.env" ]]; then
    cp "$SCRIPT_DIR/.env" "$BIN_DIR/"
fi

# Install desktop entry
cp "$TEMPLATE_DIR/desktop/solve-mcq.desktop" "$MENU_DIR/"
chmod +x "$MENU_DIR/solve-mcq.desktop"

echo "✓ Solve MCQ Exam menu installed"
