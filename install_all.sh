#!/bin/bash
# Master installer for KDE right-click context menu utilities
# Adds options for converting files to PDF, transcribing audio, and more

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export TEMPLATE_DIR="$SCRIPT_DIR/templates"
VENV_DIR="$HOME/.local/share/abc/venv"

echo "Installing context menu utilities..."
echo ""

# Check and install dependencies
check_and_install() {
    local cmd="$1"
    local pkg="$2"
    local desc="$3"
    local install_cmd="$4"
    
    if command -v "$cmd" &> /dev/null; then
        echo "✓ $desc found"
        return 0
    else
        echo "⚠ $desc not found, installing..."
        eval "$install_cmd"
        if command -v "$cmd" &> /dev/null; then
            echo "✓ $desc installed successfully"
            return 0
        else
            echo "✗ Failed to install $desc"
            return 1
        fi
    fi
}

echo "Checking dependencies..."
echo ""

# LibreOffice (for document conversion)
check_and_install "libreoffice" "libreoffice" "LibreOffice" \
    "sudo apt install -y libreoffice"

# Calibre (for ebook conversion)
check_and_install "ebook-convert" "calibre" "Calibre" \
    "sudo apt install -y calibre"

# Poppler utils (for PDF to image conversion)
check_and_install "pdftoppm" "poppler-utils" "Poppler utils" \
    "sudo apt install -y poppler-utils"

# TeX Live (for LaTeX compilation)
check_and_install "pdflatex" "texlive" "TeX Live" \
    "sudo apt install -y texlive-latex-base texlive-latex-extra texlive-fonts-recommended texlive-science"

# Check for CUDA/cuDNN (optional, for GPU acceleration)
if ldconfig -p 2>/dev/null | grep -q "libcudnn_ops.so.9"; then
    echo "✓ cuDNN 9 found (GPU acceleration enabled)"
else
    echo "⚠ cuDNN 9 not found (transcription will use CPU)"
    echo "  For GPU acceleration, run: ./install_cuda.sh"
fi

# Install uv if not present
if ! command -v uv &> /dev/null; then
    echo "⚠ uv not found, installing..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    echo "✓ uv installed"
else
    echo "✓ uv found"
fi

# Create venv and install Python dependencies
echo ""
echo "Setting up Python virtual environment..."
mkdir -p "$(dirname "$VENV_DIR")"

if [[ ! -d "$VENV_DIR" ]]; then
    uv venv "$VENV_DIR"
fi

echo "Installing Python packages in venv..."
# Core transcription packages
uv pip install --python "$VENV_DIR/bin/python" faster-whisper google-genai

# Install insanely-fast-whisper for diarization (uses pyannote.audio)
echo "Installing insanely-fast-whisper for speaker diarization..."
uv pip install --python "$VENV_DIR/bin/python" insanely-fast-whisper

echo "✓ Python packages installed"

echo ""
echo "Installing context menus..."
echo ""

# Install shared libraries first
source "$SCRIPT_DIR/converters/shared_libs.sh"

# Install converters
source "$SCRIPT_DIR/converters/docx_to_pdf.sh"
source "$SCRIPT_DIR/converters/epub_to_pdf.sh"
source "$SCRIPT_DIR/converters/transcribe_audio.sh"
source "$SCRIPT_DIR/converters/folder_colors.sh"
source "$SCRIPT_DIR/converters/clean_code.sh"
source "$SCRIPT_DIR/converters/retype_pdf.sh"

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
echo ""
echo "📝 Add your API keys to .env in this directory, then re-run ./install_all.sh:"
echo "   GEMINI_API_KEY=your_gemini_key"
echo "   HF_TOKEN=your_huggingface_token"
echo ""
echo "   Get keys at:"
echo "   - Gemini: https://aistudio.google.com/apikey"
echo "   - HuggingFace: https://huggingface.co/settings/tokens"
echo "   - Accept model terms: https://huggingface.co/pyannote/speaker-diarization"
