#!/bin/bash
# Installs the Retype PDF context menu

MENU_DIR="$HOME/.local/share/kio/servicemenus"
BIN_DIR="$HOME/.local/bin"

mkdir -p "$MENU_DIR"
mkdir -p "$BIN_DIR"

# Install helper scripts
cp "$TEMPLATE_DIR/scripts/retype-pdf.sh" "$BIN_DIR/"
cp "$TEMPLATE_DIR/scripts/retype_pdf.py" "$BIN_DIR/"
chmod +x "$BIN_DIR/retype-pdf.sh"
chmod +x "$BIN_DIR/retype_pdf.py"

# Copy .env file for API keys if it exists
if [[ -f "$SCRIPT_DIR/.env" ]]; then
    cp "$SCRIPT_DIR/.env" "$BIN_DIR/"
fi

# Install desktop entry
cp "$TEMPLATE_DIR/desktop/retype-pdf.desktop" "$MENU_DIR/"
chmod +x "$MENU_DIR/retype-pdf.desktop"

echo "✓ Retype PDF menu installed"
