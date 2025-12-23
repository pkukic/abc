#!/bin/bash
# Master installer for KDE right-click context menu utilities
# Adds options for converting files to PDF, transcribing audio, and more

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export TEMPLATE_DIR="$SCRIPT_DIR/templates"

echo "Installing context menu utilities..."
echo ""

# Check dependencies
check_dependency() {
    if ! command -v "$1" &> /dev/null; then
        echo "⚠ Warning: '$1' not found. Install it for $2 support."
        return 1
    fi
    return 0
}

# Install PDF converters
source "$SCRIPT_DIR/converters/docx_to_pdf.sh"

if check_dependency "ebook-convert" "EPUB/MOBI → PDF"; then
    source "$SCRIPT_DIR/converters/epub_to_pdf.sh"
else
    echo "  Install with: sudo apt install calibre"
fi

# Audio/Video transcription
if check_dependency "insanely-fast-whisper" "audio transcription"; then
    source "$SCRIPT_DIR/converters/transcribe_audio.sh"
else
    echo "  Install with: pipx install insanely-fast-whisper"
fi

# Folder utilities
source "$SCRIPT_DIR/converters/folder_colors.sh"

echo ""

# Refresh KDE configuration
echo "Refreshing KDE menus..."
if command -v kbuildsycoca6 &> /dev/null; then
    kbuildsycoca6 2>/dev/null
else
    kbuildsycoca5 2>/dev/null
fi

echo ""
echo "✅ Done! Right-click files to see new context menu options."
