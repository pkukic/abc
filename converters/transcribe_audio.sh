#!/bin/bash
# Installs the audio/video transcription context menu

MENU_DIR="$HOME/.local/share/kio/servicemenus"
BIN_DIR="$HOME/.local/bin"

mkdir -p "$MENU_DIR"
mkdir -p "$BIN_DIR"

# Install helper scripts
cp "$TEMPLATE_DIR/scripts/transcribe-monologue.sh" "$BIN_DIR/"
cp "$TEMPLATE_DIR/scripts/transcribe-dialogue.sh" "$BIN_DIR/"
cp "$TEMPLATE_DIR/scripts/transcribe.py" "$BIN_DIR/"
chmod +x "$BIN_DIR/transcribe-monologue.sh"
chmod +x "$BIN_DIR/transcribe-dialogue.sh"
chmod +x "$BIN_DIR/transcribe.py"

# Remove old script if exists
rm -f "$BIN_DIR/transcribe-audio.sh"

# Copy .env file for API keys if it exists
if [[ -f "$SCRIPT_DIR/.env" ]]; then
    cp "$SCRIPT_DIR/.env" "$BIN_DIR/"
fi

# Install desktop entry (expand $HOME)
envsubst '$HOME' < "$TEMPLATE_DIR/desktop/transcribe-audio.desktop" > "$MENU_DIR/transcribe-audio.desktop"
chmod +x "$MENU_DIR/transcribe-audio.desktop"

echo "✓ Audio/Video transcription menu installed"
