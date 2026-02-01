#!/bin/bash
# Installs the Anki flashcard generator context menu

MENU_DIR="$HOME/.local/share/kio/servicemenus"
BIN_DIR="$HOME/.local/bin"

mkdir -p "$MENU_DIR"
mkdir -p "$BIN_DIR"

# Install Python script
cp "$TEMPLATE_DIR/scripts/generate_flashcards.py" "$BIN_DIR/"
chmod +x "$BIN_DIR/generate_flashcards.py"

# Install shell wrapper
cp "$TEMPLATE_DIR/scripts/generate-flashcards.sh" "$BIN_DIR/"
chmod +x "$BIN_DIR/generate-flashcards.sh"

# Copy .env file for API keys if it exists
if [[ -f "$SCRIPT_DIR/.env" ]]; then
    cp "$SCRIPT_DIR/.env" "$BIN_DIR/"
fi

# Install desktop entry
cp "$TEMPLATE_DIR/desktop/generate-flashcards.desktop" "$MENU_DIR/"
chmod +x "$MENU_DIR/generate-flashcards.desktop"

echo "✓ Anki flashcard generator installed"
