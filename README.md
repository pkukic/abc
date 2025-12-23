# ABC - Auto Build Cards

<p align="center">
  <img src="assets/logo.png" alt="ABC Logo" width="128">
</p>

**ABC** is a collection of scripts that add right-click context menu options for converting files into formats optimized for [Gemini](https://gemini.google.com/app). The goal: prepare documents, ebooks, and audio/video for AI-assisted Anki flashcard generation.

The name stands for **A**uto **B**uild **C**ards. It's also a pun—[ABC sir](https://www.abcsir.hr/) is a popular brand of spreadable cheese in Croatia. 

> 🚧 **Work in Progress** - More converters coming soon!

## Why?

When using Gemini to create Anki flashcards from study materials:

1. **Format compatibility**: Some formats aren't directly accepted by Gemini (like `.docx`, `.epub`, `.mobi`)—these get converted to **PDF**
2. **Token efficiency**: Audio/video files are expensive in tokens—transcribing them to **text** is much cheaper and often more useful

## Current Features

| Right-click Option | Input Formats | Output | Tool Used |
|--------------------|---------------|--------|-----------|
| **Convert to PDF** | `.docx`, `.doc`, `.odt`, `.rtf`, `.txt` | PDF | LibreOffice |
| **Convert to PDF** | `.epub`, `.mobi` | PDF | Calibre |
| **Transcribe** | `.mp3`, `.webm`, `.wav`, `.ogg`, `.mp4`, `.flac` | Text with timestamps | faster-whisper |
| **Transcribe + Fix** | `.mp3`, `.webm`, `.wav`, `.ogg`, `.mp4`, `.flac` | Text with AI correction | faster-whisper + Gemini |
| **Mark as Red/Green** | Folders | Colored folder icon | Built-in |

## Installation

```bash
git clone git@github.com:pkukic/abc.git
cd abc
./install_all.sh
```

The installer will automatically:
- Install required dependencies (LibreOffice, Calibre, uv)
- Create a Python virtual environment at `~/.local/share/abc/venv`
- Install Python packages (faster-whisper, google-generativeai)
- Set up right-click context menu entries

> **Note**: You may be prompted for your password to install system packages.

### Gemini API Key (for Transcribe + Fix)

To use the "Transcribe + Fix" feature, add your Gemini API key:

```bash
mkdir -p ~/.config/abc
echo "GEMINI_API_KEY=your_key_here" > ~/.config/abc/.env
```

Get your API key at: https://aistudio.google.com/apikey

## Usage

1. Right-click any supported file in your file manager
2. Select the appropriate action (e.g., "Convert to PDF", "Transcribe")
3. The output file will be created next to the original

### Transcription

Transcription uses [faster-whisper](https://github.com/SYSTRAN/faster-whisper) with the `distil-large-v3` model.

**Options:**
- **Transcribe** — Fast transcription with timestamps
- **Transcribe + Fix** — Same as above, but uses Gemini API to fix errors like misheard technical terms (SISC→CISC, TinyGuard→TinyGrad)

Output format:
```
[0.00s -> 5.23s] What possible ideas do you have for how human species ends?
[5.23s -> 12.45s] Sure. So I think the most obvious way to me is wireheading.
...
```

Output: `filename_transcript.txt` — Text with timestamps for easy reference

## Related

- [Margo](https://github.com/pkukic/margo) — PDF reader for annotating and discussing papers with Gemini

## License

MIT
