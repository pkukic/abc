#!/bin/bash
# Installs the handwritten notes to PDF context menu

MENU_DIR="$HOME/.local/share/kio/servicemenus"
BIN_DIR="$HOME/.local/bin"

mkdir -p "$MENU_DIR"
mkdir -p "$BIN_DIR"

# Install helper scripts
cp "$TEMPLATE_DIR/scripts/notes-to-pdf.sh" "$BIN_DIR/"
cp "$TEMPLATE_DIR/scripts/notes_to_pdf.py" "$BIN_DIR/"
chmod +x "$BIN_DIR/notes-to-pdf.sh"
chmod +x "$BIN_DIR/notes_to_pdf.py"

# Copy .env file for API keys if it exists
if [[ -f "$SCRIPT_DIR/.env" ]]; then
    cp "$SCRIPT_DIR/.env" "$BIN_DIR/"
fi

# Install desktop entry
cp "$TEMPLATE_DIR/desktop/notes-to-pdf.desktop" "$MENU_DIR/"
chmod +x "$MENU_DIR/notes-to-pdf.desktop"

echo "✓ Notes to PDF menu installed"
