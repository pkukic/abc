#!/usr/bin/env python3
"""Transcribe audio/video files using faster-whisper with progress output."""

import argparse
import os
import sys
from pathlib import Path

from faster_whisper import WhisperModel


# Gemini API configuration - check multiple locations
SCRIPT_DIR = Path(__file__).parent
ENV_LOCATIONS = [
    SCRIPT_DIR / ".env",  # Same dir as script (for development)
    Path.home() / ".config" / "abc" / ".env",  # User config
]


def format_timestamp(seconds: float) -> str:
    """Format seconds as MM:SS."""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"


def get_audio_duration(file_path: str) -> float:
    """Get audio duration using ffprobe if available."""
    import subprocess
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", file_path],
            capture_output=True, text=True
        )
        return float(result.stdout.strip())
    except (subprocess.SubprocessError, ValueError):
        return 0.0


def get_gemini_config() -> tuple[str | None, str]:
    """Get Gemini API key and model from environment or config file."""
    api_key = os.environ.get("GEMINI_API_KEY")
    model = os.environ.get("GEMINI_MODEL")
    
    # Check config files if not in env
    for env_file in ENV_LOCATIONS:
        if env_file.exists():
            config = env_file.read_text()
            for line in config.splitlines():
                if not api_key and line.startswith("GEMINI_API_KEY="):
                    api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                if not model and line.startswith("GEMINI_MODEL="):
                    model = line.split("=", 1)[1].strip().strip('"').strip("'")
            
            if api_key and model:
                break
    
    # Default to Gemini 3 Flash (Preview) if not specified
    if not model:
        model = "gemini-3-flash-preview"
        
    return api_key, model


def fix_transcription(transcript: str) -> str:
    """Use Gemini API to fix transcription errors."""
    try:
        from google import genai
    except ImportError:
        print("google-genai not installed. Run: ./install_all.sh", file=sys.stderr)
        return transcript
    
    api_key, model_name = get_gemini_config()
    if not api_key:
        print(f"Gemini API key not found. Create {ENV_FILE} with:", file=sys.stderr)
        print(f"  GEMINI_API_KEY=your_key_here", file=sys.stderr)
        return transcript
    
    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        print(f"Error creating Gemini client: {e}", file=sys.stderr)
        return transcript
    
    print(f"Fixing transcription with {model_name}...", file=sys.stderr)
    
    prompt = f"""You are a specialized text processing tool. Your goal is to fix transcription errors in technical audio transcripts.

Instructions:
1. Fix obvious errors in technical terms (e.g., "SISC" -> "CISC", "TinyGuard" -> "TinyGrad", "RISIS" -> "Rice's", "Kuda" -> "CUDA").
2. Fix proper nouns (names, libraries, etc.).
3. Fix obvious word substitutions that don't make sense in context.
4. DO NOT rephrase or change the meaning.
5. KEEP the timestamps exactly as they are.
6. OUTPUT ONLY the corrected text. Do not add any introduction, explanation, or conclusion.

Input Text:
{transcript}

Corrected Text:"""

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )
        fixed_text = response.text.strip()
        
        # Validate that we got a reasonable response (should have timestamps)
        if fixed_text and "[" in fixed_text and "->" in fixed_text:
            print("✓ Text correction complete", file=sys.stderr)
            return fixed_text
        else:
            print("Warning: Unexpected response format, keeping original", file=sys.stderr)
            return transcript
    except Exception as e:
        print(f"Gemini API error: {e}", file=sys.stderr)
        return transcript


def transcribe(file_path: str, model_name: str = "distil-large-v3") -> str:
    """Transcribe audio file with progress output."""
    print(f"Loading model: {model_name}", file=sys.stderr)
    
    # Try CUDA first, fall back to CPU if cuDNN is missing
    try:
        model = WhisperModel(model_name, device="cuda", compute_type="float16")
        print("Using GPU (CUDA)", file=sys.stderr)
    except Exception as e:
        if "cudnn" in str(e).lower() or "cuda" in str(e).lower():
            print(f"CUDA unavailable, using CPU (run install_cuda.sh for GPU support)", file=sys.stderr)
        else:
            print(f"CUDA failed: {e}, using CPU", file=sys.stderr)
        model = WhisperModel(model_name, device="cpu", compute_type="int8")
        print("Using CPU", file=sys.stderr)
    
    # Get audio duration for progress calculation
    duration = get_audio_duration(file_path)
    if duration > 0:
        print(f"Audio duration: {format_timestamp(duration)}", file=sys.stderr)
    
    print(f"Transcribing: {file_path}", file=sys.stderr)
    print("-" * 40, file=sys.stderr)
    
    segments, info = model.transcribe(
        file_path,
        beam_size=5,
        vad_filter=True,  # Skip silent parts
    )
    
    print(f"Detected language: {info.language} ({info.language_probability:.0%})", file=sys.stderr)
    
    full_text = []
    last_progress_minute = -1
    
    for segment in segments:
        # Format: [0.00s -> 5.00s] text
        line = "[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text.strip())
        full_text.append(line)
        
        # Show progress every minute of audio
        current_minute = int(segment.end // 60)
        if current_minute > last_progress_minute:
            if duration > 0:
                progress = min(100, (segment.end / duration) * 100)
                print(f"  [{format_timestamp(segment.end)}] {progress:.0f}% complete", file=sys.stderr)
            else:
                print(f"  [{format_timestamp(segment.end)}] processing...", file=sys.stderr)
            last_progress_minute = current_minute
    
    print("-" * 40, file=sys.stderr)
    print("✓ Transcription complete", file=sys.stderr)
    
    return "\n".join(full_text)


def main():
    parser = argparse.ArgumentParser(description="Transcribe audio using faster-whisper")
    parser.add_argument("file", help="Audio/video file to transcribe")
    parser.add_argument("--model", default="distil-large-v3",
                        help="Whisper model to use (default: distil-large-v3)")
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")
    parser.add_argument("--fix", action="store_true",
                        help="Use Gemini API to fix transcription errors")
    args = parser.parse_args()
    
    if not Path(args.file).exists():
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)
    
    text = transcribe(args.file, args.model)
    
    if args.fix:
        text = fix_transcription(text)
    
    if args.output:
        Path(args.output).write_text(text)
        print(f"Saved to: {args.output}", file=sys.stderr)
    else:
        print(text)


if __name__ == "__main__":
    main()
