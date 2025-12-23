#!/bin/bash
# Installs the EPUB/MOBI to PDF context menu
# Requires: calibre (provides ebook-convert)

MENU_DIR="$HOME/.local/share/kio/servicemenus"
BIN_DIR="$HOME/.local/bin"

mkdir -p "$MENU_DIR"
mkdir -p "$BIN_DIR"

# Install helper script
cp "$TEMPLATE_DIR/scripts/ebook-to-pdf.sh" "$BIN_DIR/"
chmod +x "$BIN_DIR/ebook-to-pdf.sh"

# Install desktop entry (expand $HOME)
envsubst '$HOME' < "$TEMPLATE_DIR/desktop/ebook-to-pdf.desktop" > "$MENU_DIR/ebook-to-pdf.desktop"
chmod +x "$MENU_DIR/ebook-to-pdf.desktop"

echo "✓ Ebook (EPUB/MOBI) → PDF converter installed"
