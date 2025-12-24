#!/usr/bin/env python3
"""Transcribe audio/video files with speaker diarization and LLM correction.

Uses insanely-fast-whisper with pyannote.audio for speaker diarization,
then Gemini to identify speakers from the filename and fix transcription errors.

Output format: [Speaker Name][0.00s -> 5.23s] Text content here
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

# Config file location - same dir as script (copied during install)
SCRIPT_DIR = Path(__file__).parent
ENV_FILE = SCRIPT_DIR / ".env"


def get_config() -> dict:
    """Get configuration from environment or config file."""
    config = {
        "gemini_api_key": os.environ.get("GEMINI_API_KEY"),
        "gemini_model": os.environ.get("GEMINI_MODEL"),
        "hf_token": os.environ.get("HF_TOKEN"),
    }
    
    # Check config file
    if ENV_FILE.exists():
        file_config = ENV_FILE.read_text()
        for line in file_config.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip().lower()
                value = value.strip().strip('"').strip("'")
                
                if key == "gemini_api_key" and not config["gemini_api_key"]:
                    config["gemini_api_key"] = value
                elif key == "gemini_model" and not config["gemini_model"]:
                    config["gemini_model"] = value
                elif key == "hf_token" and not config["hf_token"]:
                    config["hf_token"] = value
    
    # Default Gemini model
    if not config["gemini_model"]:
        config["gemini_model"] = "gemini-3-flash-preview"
        
    
    return config


def transcribe_with_diarization(
    file_path: str,
    model_name: str = "distil-whisper/distil-large-v3",
    batch_size: int = 1,
    hf_token: str = None,
    num_speakers: int = 2,
) -> str:
    """Transcribe audio file with speaker diarization using insanely-fast-whisper.
    
    Returns transcript in format: [Speaker N][start -> end] text
    """
    # Create temp file for output
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        output_path = tmp.name
    
    try:
        # Build command
        cmd = [
            "insanely-fast-whisper",
            "--file-name", file_path,
            "--model-name", model_name,
            "--batch-size", str(batch_size),
            "--transcript-path", output_path,
            "--timestamp", "chunk",  # chunk works for all models (word requires alignment_heads)
        ]
        
        # Add diarization if HF token is provided
        if hf_token:
            cmd.extend([
                "--hf-token", hf_token,
                "--num-speakers", str(num_speakers),
            ])
            print(f"Speaker diarization: enabled ({num_speakers} speaker{'s' if num_speakers > 1 else ''})", file=sys.stderr)
        else:
            print("⚠ No HF_TOKEN provided - diarization disabled", file=sys.stderr)
            print("  Add HF_TOKEN=your_token to ~/.config/abc/.env", file=sys.stderr)
        
        print(f"Transcribing with {model_name}...", file=sys.stderr)
        
        # Run insanely-fast-whisper
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error running insanely-fast-whisper:", file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            sys.exit(1)
        
        # Parse output JSON
        with open(output_path) as f:
            data = json.load(f)
        
        # Format output
        lines = []
        
        if "speakers" in data and data["speakers"]:
            # Diarization was performed
            for segment in data["speakers"]:
                speaker = segment.get("speaker", "Unknown")
                if speaker.startswith("SPEAKER_"):
                    speaker_num = int(speaker.split("_")[1]) + 1
                    speaker = f"Speaker {speaker_num}"
                
                start = segment.get("timestamp", [0, 0])[0]
                end = segment.get("timestamp", [0, 0])[1]
                text = segment.get("text", "").strip()
                
                if text:
                    lines.append(f"[{speaker}][{start:.2f}s -> {end:.2f}s] {text}")
        
        elif "chunks" in data:
            # No diarization - use chunks
            for chunk in data["chunks"]:
                start = chunk.get("timestamp", [0, 0])[0] or 0
                end = chunk.get("timestamp", [0, 0])[1] or start
                text = chunk.get("text", "").strip()
                
                if text:
                    lines.append(f"[Speaker 1][{start:.2f}s -> {end:.2f}s] {text}")
        
        elif "text" in data:
            lines.append(f"[Speaker 1][0.00s -> 0.00s] {data['text']}")
        
        print("✓ Transcription complete", file=sys.stderr)
        return "\n".join(lines)
        
    finally:
        if os.path.exists(output_path):
            os.remove(output_path)


def identify_speakers_and_fix(transcript: str, filename: str, config: dict) -> str:
    """Use Gemini to identify speakers from filename and fix transcription errors."""
    try:
        from google import genai
    except ImportError:
        print("google-genai not installed. Run: ./install_all.sh", file=sys.stderr)
        return transcript
    
    api_key = config["gemini_api_key"]
    model_name = config["gemini_model"]
    
    if not api_key:
        print("⚠ No GEMINI_API_KEY - skipping speaker identification", file=sys.stderr)
        return transcript
    
    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        print(f"Error creating Gemini client: {e}", file=sys.stderr)
        return transcript
    
    print(f"Identifying speakers and fixing errors with {model_name}...", file=sys.stderr)
    
    prompt = f"""You are a specialized text processing tool for fixing podcast/interview transcripts.

The audio filename is: {filename}

Instructions:
1. IDENTIFY THE SPEAKERS: Based on the filename, identify who "Speaker 1", "Speaker 2", etc. likely are.
   - The filename often contains names of the people in the conversation (e.g., "George_Hotz_Lex_Fridman" means George Hotz and Lex Fridman are talking)
   - Replace "[Speaker N]" with the actual person's name in brackets, e.g., "[Lex Fridman]"
   - If there is only ONE speaker (e.g., a solo lecture or monologue), identify them and use their name for all lines
   - If there are TWO speakers (e.g., an interview), identify both and assign names correctly based on context
   - If you can't determine who a speaker is, keep the original "[Speaker N]" format

2. FIX TRANSCRIPTION ERRORS:
   - Fix obvious errors in technical terms (e.g., "SISC" -> "CISC", "TinyGuard" -> "TinyGrad", "Kuda" -> "CUDA")
   - Fix proper nouns (names, libraries, etc.)
   - Fix obvious word substitutions that don't make sense in context

3. PRESERVE FORMAT:
   - Keep the timestamps exactly as they are in format [Name][Xs -> Ys]
   - DO NOT rephrase or change the meaning

4. OUTPUT ONLY the corrected transcript. No introduction or explanation.

Input Transcript:
{transcript}

Corrected Transcript:"""

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )
        fixed_text = response.text.strip()
        
        if fixed_text and "[" in fixed_text and "->" in fixed_text:
            print("✓ Speaker identification and correction complete", file=sys.stderr)
            return fixed_text
        else:
            print("Warning: Unexpected response format, keeping original", file=sys.stderr)
            return transcript
    except Exception as e:
        print(f"Gemini API error: {e}", file=sys.stderr)
        return transcript


def main():
    parser = argparse.ArgumentParser(
        description="Transcribe audio with speaker diarization and LLM correction"
    )
    parser.add_argument("file", help="Audio/video file to transcribe")
    parser.add_argument("--model", default="distil-whisper/distil-large-v3",
                        help="Whisper model (default: distil-whisper/distil-large-v3)")
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")
    parser.add_argument("--batch-size", type=int, default=1,
                        help="Batch size (default: 1, reduce for less VRAM)")
    parser.add_argument("--num-speakers", type=int, default=2,
                        help="Number of speakers (default: 2, use 1 for solo content)")
    args = parser.parse_args()
    
    if not Path(args.file).exists():
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)
    
    config = get_config()
    
    # Step 1: Transcribe with diarization
    transcript = transcribe_with_diarization(
        args.file,
        model_name=args.model,
        batch_size=args.batch_size,
        hf_token=config["hf_token"],
        num_speakers=args.num_speakers,
    )
    
    # Step 2: Identify speakers and fix errors with LLM
    filename = Path(args.file).name
    transcript = identify_speakers_and_fix(transcript, filename, config)
    
    # Output
    if args.output:
        Path(args.output).write_text(transcript)
        print(f"Saved to: {args.output}", file=sys.stderr)
    else:
        print(transcript)


if __name__ == "__main__":
    main()
