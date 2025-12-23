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
| **Transcribe** | `.mp3`, `.webm`, `.wav`, `.ogg`, `.mp4`, `.flac` | Text + JSON | insanely-fast-whisper |
| **Mark as Red/Green** | Folders | Colored folder icon | Built-in |

## Prerequisites

- **Linux** with KDE Plasma (tested on Pop!_OS with Dolphin)
- **LibreOffice** (for document conversion)
- **Calibre** (for ebook conversion): `sudo apt install calibre`
- **insanely-fast-whisper** (for transcription): `pipx install insanely-fast-whisper`

## Installation

```bash
git clone git@github.com:pkukic/abc.git
cd abc
./install_all.sh
```

The installer will:
- Check for required dependencies
- Install right-click context menu entries
- Set up helper scripts in `~/.local/bin/`

## Usage

1. Right-click any supported file in your file manager
2. Select the appropriate action (e.g., "Convert to PDF", "Transcribe")
3. The output file will be created next to the original

### Transcription Output

Transcription creates two files:
- `filename_transcript.json` — Full transcript with timestamps
- `filename_transcript.txt` — Plain text for easy copy/paste into Gemini

## Related

- [Margo](https://github.com/pkukic/margo) — PDF reader for annotating and discussing papers with Gemini

## License

MIT
