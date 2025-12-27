#!/bin/bash
# Installs the Office (DOCX/PPTX/ODT/ODP/RTF) to PDF context menu

MENU_DIR="$HOME/.local/share/kio/servicemenus"

mkdir -p "$MENU_DIR"
cp "$TEMPLATE_DIR/desktop/office-to-pdf.desktop" "$MENU_DIR/"
chmod +x "$MENU_DIR/office-to-pdf.desktop"

echo "✓ Office → PDF converter installed"
