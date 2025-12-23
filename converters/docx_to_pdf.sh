#!/bin/bash
# Installs the DOCX/ODT/RTF to PDF context menu

MENU_DIR="$HOME/.local/share/kio/servicemenus"

mkdir -p "$MENU_DIR"
cp "$TEMPLATE_DIR/desktop/docx-to-pdf.desktop" "$MENU_DIR/"
chmod +x "$MENU_DIR/docx-to-pdf.desktop"

echo "✓ Document → PDF converter installed"
