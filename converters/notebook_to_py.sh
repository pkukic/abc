#!/bin/bash
# Installs the Notebook to Python context menu

MENU_DIR="$HOME/.local/share/kio/servicemenus"

mkdir -p "$MENU_DIR"

cp "$TEMPLATE_DIR/desktop/notebook-to-py.desktop" "$MENU_DIR/"
chmod +x "$MENU_DIR/notebook-to-py.desktop"

echo "✓ Notebook → Python converter installed"
