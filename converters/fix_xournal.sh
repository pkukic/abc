#!/bin/bash
# Installs the Xournal PDF fix context menu

MENU_DIR="$HOME/.local/share/kio/servicemenus"
BIN_DIR="$HOME/.local/bin"

mkdir -p "$MENU_DIR"
mkdir -p "$BIN_DIR"

# Install helper scripts
cp "$TEMPLATE_DIR/scripts/fix_xournal.py" "$BIN_DIR/"
cp "$TEMPLATE_DIR/scripts/fix-xournal.sh" "$BIN_DIR/"
chmod +x "$BIN_DIR/fix_xournal.py"
chmod +x "$BIN_DIR/fix-xournal.sh"

# Install desktop entry
cp "$TEMPLATE_DIR/desktop/fix-xournal.desktop" "$MENU_DIR/"
chmod +x "$MENU_DIR/fix-xournal.desktop"

echo "✓ Xournal PDF fix menu installed"
