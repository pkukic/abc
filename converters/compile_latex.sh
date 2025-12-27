#!/bin/bash
# Installs the Compile LaTeX context menu

MENU_DIR="$HOME/.local/share/kio/servicemenus"
BIN_DIR="$HOME/.local/bin"

mkdir -p "$MENU_DIR"
mkdir -p "$BIN_DIR"

cp "$TEMPLATE_DIR/scripts/compile-latex.sh" "$BIN_DIR/"
chmod +x "$BIN_DIR/compile-latex.sh"

cp "$TEMPLATE_DIR/desktop/compile-latex.desktop" "$MENU_DIR/"
chmod +x "$MENU_DIR/compile-latex.desktop"

echo "✓ Compile LaTeX menu installed"
