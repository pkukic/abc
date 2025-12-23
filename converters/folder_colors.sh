#!/bin/bash
# Installs the folder color context menu

MENU_DIR="$HOME/.local/share/kio/servicemenus"
BIN_DIR="$HOME/.local/bin"

mkdir -p "$MENU_DIR"
mkdir -p "$BIN_DIR"

# Install helper script
cp "$TEMPLATE_DIR/scripts/set-folder-color.sh" "$BIN_DIR/"
chmod +x "$BIN_DIR/set-folder-color.sh"

# Install desktop entry (expand $HOME)
envsubst '$HOME' < "$TEMPLATE_DIR/desktop/folder-colors.desktop" > "$MENU_DIR/folder-colors.desktop"
chmod +x "$MENU_DIR/folder-colors.desktop"

echo "✓ Folder color menu installed"
