#!/bin/bash
# Installs the audio/video transcription context menu
# Requires: insanely-fast-whisper (pipx install insanely-fast-whisper)

MENU_DIR="$HOME/.local/share/kio/servicemenus"
BIN_DIR="$HOME/.local/bin"

mkdir -p "$MENU_DIR"
mkdir -p "$BIN_DIR"

# Install helper script
cp "$TEMPLATE_DIR/scripts/transcribe-audio.sh" "$BIN_DIR/"
chmod +x "$BIN_DIR/transcribe-audio.sh"

# Install desktop entry (expand $HOME)
envsubst '$HOME' < "$TEMPLATE_DIR/desktop/transcribe-audio.desktop" > "$MENU_DIR/transcribe-audio.desktop"
chmod +x "$MENU_DIR/transcribe-audio.desktop"

echo "✓ Audio/Video transcription menu installed"
