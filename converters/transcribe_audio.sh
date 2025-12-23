#!/bin/bash
# Installs the audio/video transcription context menu
# Requires: insanely-fast-whisper (pipx install insanely-fast-whisper)

MENU_DIR="$HOME/.local/share/kio/servicemenus"
BIN_DIR="$HOME/.local/bin"

mkdir -p "$MENU_DIR"
mkdir -p "$BIN_DIR"

# Install helper scripts
cp "$TEMPLATE_DIR/scripts/transcribe-audio.sh" "$BIN_DIR/"
cp "$TEMPLATE_DIR/scripts/transcribe-audio-fix.sh" "$BIN_DIR/"
cp "$TEMPLATE_DIR/scripts/transcribe.py" "$BIN_DIR/"
chmod +x "$BIN_DIR/transcribe-audio.sh"
chmod +x "$BIN_DIR/transcribe-audio-fix.sh"
chmod +x "$BIN_DIR/transcribe.py"

# Copy .env file for Gemini API key if it exists
if [[ -f "$SCRIPT_DIR/.env" ]]; then
    cp "$SCRIPT_DIR/.env" "$BIN_DIR/"
fi

# Install desktop entry (expand $HOME)
envsubst '$HOME' < "$TEMPLATE_DIR/desktop/transcribe-audio.desktop" > "$MENU_DIR/transcribe-audio.desktop"
chmod +x "$MENU_DIR/transcribe-audio.desktop"

echo "✓ Audio/Video transcription menu installed"
