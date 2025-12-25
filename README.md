# ABC - Auto Build Cards

<p align="center">
  <img src="assets/logo.png" alt="ABC Logo" width="128">
</p>

**ABC** is a collection of right-click context menu utilities for file conversion and AI-powered processing on Linux (KDE). The goal: prepare documents, ebooks, code, and audio/video for Anki flashcard generation.

The name stands for **A**uto **B**uild **C**ards. It's also a pun—[ABC sir](https://www.abcsir.hr/) is a popular brand of spreadable cheese in Croatia.

## Features

| Feature | Description |
|---------|-------------|
| **Document → PDF** | Convert DOCX/ODT/RTF to PDF via LibreOffice |
| **Ebook → PDF** | Convert EPUB/MOBI to PDF via Calibre |
| **Transcribe (Monologue)** | Audio/video → text for 1 speaker (supports batch) |
| **Transcribe (Dialogue)** | Audio/video → text for 2 speakers with diarization (supports batch) |
| **Studify Algorithm** | Annotate algorithmic code for Anki flashcards (Big-O, techniques) |
| **Studify Language** | Annotate language feature demos for Anki flashcards |
| **Studify OS** | Annotate OS-level C code (paging, signals, threads) for Anki |
| **Retype to LaTeX** | Convert PDF or images (handwritten/printed) to clean LaTeX PDF |
| **Folder Colors** | Set folder colors in Dolphin |

**Refresh feature:** All LLM-powered tools preserve originals (`.bak` files for code, separate outputs for others). Re-run anytime to regenerate with newer models.

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
├── assets/
│   └── logo.png
├── converters/             # Installer scripts for each feature
│   ├── annotate_code.sh
│   ├── docx_to_pdf.sh
│   ├── epub_to_pdf.sh
│   ├── folder_colors.sh
│   ├── retype_pdf.sh
│   ├── shared_libs.sh
│   └── transcribe_audio.sh
├── templates/
│   ├── desktop/            # KDE service menu files
│   │   ├── annotate-code.desktop
│   │   ├── docx-to-pdf.desktop
│   │   ├── ebook-to-pdf.desktop
│   │   ├── folder-colors.desktop
│   │   ├── retype-pdf.desktop
│   │   └── transcribe-audio.desktop
│   ├── prompts/            # LLM prompt templates
│   │   ├── retype_to_latex.txt
│   │   ├── studify_algo.txt
│   │   ├── studify_lang.txt
│   │   ├── studify_os.txt
│   │   └── transcribe_fix.txt
│   └── scripts/            # Python and shell scripts
│       ├── lib/
│       │   ├── common.py
│       │   ├── common.sh
│       │   └── __init__.py
│       ├── annotate_code.py
│       ├── retype_pdf.py
│       ├── transcribe.py
│       └── *.sh            # Shell wrappers
├── install_all.sh
├── install_cuda.sh
├── LICENSE
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

## Related

- [Margo](https://github.com/pkukic/margo) — PDF reader for annotating and discussing papers with Gemini

## License

MIT
