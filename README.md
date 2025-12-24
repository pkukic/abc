# ABC - AI-powered Batch Converters

A collection of right-click context menu utilities for file conversion and AI-powered processing on Linux (KDE).

## Features

| Feature | Description |
|---------|-------------|
| **Document → PDF** | Convert DOCX/ODT/RTF to PDF via LibreOffice |
| **Ebook → PDF** | Convert EPUB/MOBI to PDF via Calibre |
| **Transcribe (Monologue)** | Audio/video transcription for 1 speaker |
| **Transcribe (Dialogue)** | Audio/video transcription for 2 speakers with diarization |
| **Transcribe (Batch)** | Select multiple files, choose type per file |
| **Clean & Comment Code** | Use Gemini to add educational comments to code |
| **Notes to LaTeX PDF** | Convert handwritten PDF notes to typeset LaTeX PDF |
| **Folder Colors** | Set folder colors in Dolphin |

## Installation

```bash
git clone https://github.com/pkukic/abc.git
cd abc
cp .env.example .env
# Edit .env with your API keys
./install_all.sh
```

## Configuration

Create a `.env` file in the project root (copy from `.env.example`):

```bash
# Google Gemini API Key (required for LLM features)
GEMINI_API_KEY=your-gemini-api-key-here

# Models (optional, defaults shown)
GEMINI_MODEL=gemini-3-flash-preview
GEMINI_MODEL_PRO=gemini-3-pro-preview

# HuggingFace Token (required for speaker diarization)
HF_TOKEN=your-huggingface-token-here
```

Get your API keys:
- **Gemini**: https://aistudio.google.com/apikey
- **HuggingFace**: https://huggingface.co/settings/tokens
  - Also accept model terms at: https://huggingface.co/pyannote/speaker-diarization-3.1

## Project Structure

```
abc/
├── install_all.sh          # Main installer
├── .env.example            # API key template
├── converters/             # Installer scripts for each feature
│   ├── shared_libs.sh      # Installs shared libraries
│   ├── docx_to_pdf.sh
│   ├── epub_to_pdf.sh
│   ├── transcribe_audio.sh
│   ├── clean_code.sh
│   ├── notes_to_pdf.sh
│   └── folder_colors.sh
├── templates/
│   ├── desktop/            # KDE service menu files
│   ├── prompts/            # External LLM prompt templates
│   │   ├── clean_code.txt
│   │   ├── notes_to_latex.txt
│   │   └── transcribe_fix.txt
│   └── scripts/            # Python and shell scripts
│       ├── lib/            # Shared libraries
│       │   ├── common.py   # Python utilities (config, Gemini)
│       │   └── common.sh   # Shell utilities (batch, notify)
│       ├── transcribe.py
│       ├── clean_code.py
│       ├── notes_to_pdf.py
│       └── *.sh            # Shell wrappers
└── README.md
```

## Dependencies

Automatically installed/checked:
- **LibreOffice** - Document conversion
- **Calibre** - Ebook conversion
- **Poppler utils** - PDF to image conversion
- **TeX Live** - LaTeX compilation
- **uv** - Python package manager
- **insanely-fast-whisper** - Transcription with diarization
- **google-genai** - Gemini API client

Optional for GPU acceleration:
- **cuDNN 9** - CUDA deep neural network library

## Usage

After installation, right-click files in Dolphin to see context menu options.

## License

MIT
