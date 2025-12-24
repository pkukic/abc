#!/usr/bin/env python3
"""Transcribe audio/video with speaker diarization and LLM correction.

Uses insanely-fast-whisper for transcription and diarization,
then Gemini for speaker identification and error correction.
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent / "lib"))
from common import get_config, call_gemini, load_prompt


def transcribe_with_diarization(
    file_path: str,
    model_name: str = "distil-whisper/distil-large-v3",
    batch_size: int = 1,
    hf_token: str = None,
    num_speakers: int = 2,
) -> str:
    """Transcribe audio file with speaker diarization using insanely-fast-whisper."""
    
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        output_path = tmp.name
    
    try:
        cmd = [
            "insanely-fast-whisper",
            "--file-name", file_path,
            "--model-name", model_name,
            "--batch-size", str(batch_size),
            "--transcript-path", output_path,
            "--timestamp", "chunk",
        ]
        
        if hf_token:
            cmd.extend([
                "--hf-token", hf_token,
                "--num-speakers", str(num_speakers),
            ])
            print(f"Speaker diarization: enabled ({num_speakers} speaker{'s' if num_speakers > 1 else ''})", file=sys.stderr)
        else:
            print("⚠ No HF_TOKEN provided - diarization disabled", file=sys.stderr)
        
        print(f"Transcribing with {model_name}...", file=sys.stderr)
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error running insanely-fast-whisper:", file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            sys.exit(1)
        
        with open(output_path) as f:
            data = json.load(f)
        
        return format_transcript(data)
        
    finally:
        if os.path.exists(output_path):
            os.remove(output_path)


def format_transcript(data: dict) -> str:
    """Format transcript data to [Speaker][timestamp] text format."""
    lines = []
    
    if "speakers" in data and data["speakers"]:
        for segment in data["speakers"]:
            speaker = segment.get("speaker", "Unknown")
            if speaker and speaker.startswith("SPEAKER_"):
                speaker_num = int(speaker.split("_")[1]) + 1
                speaker = f"Speaker {speaker_num}"
            elif not speaker:
                speaker = "Unknown"
            
            timestamp = segment.get("timestamp", [0, 0])
            start = timestamp[0] if timestamp and timestamp[0] is not None else 0
            end = timestamp[1] if timestamp and len(timestamp) > 1 and timestamp[1] is not None else start
            text = segment.get("text", "").strip()
            
            if text:
                lines.append(f"[{speaker}][{start:.2f}s -> {end:.2f}s] {text}")
    
    elif "chunks" in data:
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


def identify_speakers_and_fix(transcript: str, filename: str, config: dict) -> str:
    """Use Gemini to identify speakers from filename and fix errors."""
    if not config.get("gemini_api_key"):
        print("⚠ No GEMINI_API_KEY - skipping speaker identification", file=sys.stderr)
        return transcript
    
    print("Identifying speakers and fixing errors...", file=sys.stderr)
    
    prompt_template = load_prompt("transcribe_fix")
    prompt = prompt_template.format(
        filename=filename,
        transcript=transcript,
    )
    
    try:
        result = call_gemini(prompt, config)
        if result and "[" in result:
            print("✓ Speakers identified and errors fixed", file=sys.stderr)
            return result
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
        hf_token=config.get("hf_token"),
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
