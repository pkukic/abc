#!/bin/bash
# Installs the code cleaning context menu

MENU_DIR="$HOME/.local/share/kio/servicemenus"
BIN_DIR="$HOME/.local/bin"

mkdir -p "$MENU_DIR"
mkdir -p "$BIN_DIR"

# Install helper scripts
cp "$TEMPLATE_DIR/scripts/clean-code.sh" "$BIN_DIR/"
cp "$TEMPLATE_DIR/scripts/clean_code.py" "$BIN_DIR/"
chmod +x "$BIN_DIR/clean-code.sh"
chmod +x "$BIN_DIR/clean_code.py"

# Copy .env file for API keys if it exists
if [[ -f "$SCRIPT_DIR/.env" ]]; then
    cp "$SCRIPT_DIR/.env" "$BIN_DIR/"
fi

# Install desktop entry
cp "$TEMPLATE_DIR/desktop/clean-code.desktop" "$MENU_DIR/"
chmod +x "$MENU_DIR/clean-code.desktop"

echo "✓ Code cleaning menu installed"
