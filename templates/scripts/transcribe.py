#!/usr/bin/env python3
"""Transcribe audio/video with speaker diarization and LLM correction.

Uses insanely-fast-whisper for transcription and diarization,
with Gemini fallback when GPU is busy.
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
from common import get_config, call_gemini, load_prompt, get_gemini_client


def is_gpu_available() -> bool:
    """Check if GPU is available for transcription.
    
    Uses nvidia-smi to check for running compute processes on the GPU.
    If any process is using the GPU, considers it "busy" to prevent
    CUDA OOM errors when multiple scripts start simultaneously.
    
    Returns:
        True if GPU is available (no compute processes), False if busy or not present.
    """
    try:
        # Check for running GPU compute processes
        result = subprocess.run(
            ["nvidia-smi", "--query-compute-apps=pid,name", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=5
        )
        
        if result.returncode != 0:
            print("⚠ nvidia-smi failed, assuming GPU unavailable", file=sys.stderr)
            return False
        
        # If output is not empty, there are processes using the GPU
        processes = result.stdout.strip()
        if processes:
            # Count running processes
            process_lines = [l for l in processes.split('\n') if l.strip()]
            print(f"⚠ GPU busy ({len(process_lines)} process(es) running), using Gemini fallback", file=sys.stderr)
            return False
        
        print("✓ GPU available (no compute processes)", file=sys.stderr)
        return True
        
    except FileNotFoundError:
        print("⚠ nvidia-smi not found, using Gemini fallback", file=sys.stderr)
        return False
    except Exception as e:
        print(f"⚠ GPU check failed: {e}, using Gemini fallback", file=sys.stderr)
        return False


def transcribe_with_gemini(
    file_path: str,
    language: str = "english",
    num_speakers: int = 1,
    config: dict = None,
) -> str:
    """Transcribe audio file using Gemini API.
    
    Args:
        file_path: Path to audio/video file
        language: "english" or "croatian" 
        num_speakers: Number of speakers (1 for monologue, 2+ for dialogue)
        config: Config dict with API keys
        
    Returns:
        Transcript in [Speaker X][timestamp] format
    """
    from google.genai import types
    
    if config is None:
        config = get_config()
    
    client = get_gemini_client(config)
    
    # Upload file to Gemini
    print(f"Uploading audio to Gemini...", file=sys.stderr)
    
    # Detect mime type
    ext = Path(file_path).suffix.lower()
    mime_map = {
        '.mp3': 'audio/mp3',
        '.wav': 'audio/wav',
        '.m4a': 'audio/mp4',
        '.mp4': 'video/mp4',
        '.webm': 'video/webm',
        '.ogg': 'audio/ogg',
        '.flac': 'audio/flac',
        '.aac': 'audio/aac',
    }
    mime_type = mime_map.get(ext, 'audio/mpeg')
    
    # Copy to temp file with safe ASCII name (Gemini API has issues with unicode filenames)
    import shutil
    temp_dir = tempfile.mkdtemp()
    safe_filename = f"audio{ext}"
    temp_path = os.path.join(temp_dir, safe_filename)
    shutil.copy2(file_path, temp_path)
    
    try:
        uploaded_file = client.files.upload(file=temp_path)
        print(f"✓ File uploaded, waiting for processing...", file=sys.stderr)
        
        # Wait for file to become ACTIVE (Gemini processes files asynchronously)
        import time
        max_wait = 28800  # 8 hours
        wait_interval = 2
        waited = 0
        while waited < max_wait:
            file_info = client.files.get(name=uploaded_file.name)
            if file_info.state.name == "ACTIVE":
                break
            if file_info.state.name == "FAILED":
                raise RuntimeError(f"File processing failed: {file_info.state}")
            time.sleep(wait_interval)
            waited += wait_interval
            print(f"  Waiting for file processing... ({waited}s)", file=sys.stderr)
        else:
            raise RuntimeError(f"File did not become ACTIVE after {max_wait}s")
        
        print(f"✓ File ready", file=sys.stderr)
        
        # Build transcription prompt
        lang_display = "Croatian" if language == "croatian" else "English"
        
        if num_speakers == 1:
            speaker_instruction = """This is a monologue with a single speaker.
Label all text as [Speaker 1]."""
        else:
            speaker_instruction = f"""This is a dialogue with approximately {num_speakers} speakers.
Identify distinct speakers and label them as [Speaker 1], [Speaker 2], etc.
If you can identify speakers by name from context, still use Speaker N format."""
        
        prompt_template = load_prompt("transcribe_gemini")
        prompt = prompt_template.format(
            language=lang_display,
            speaker_instruction=speaker_instruction,
        )

        print(f"Transcribing with Gemini ({lang_display}, {num_speakers} speaker{'s' if num_speakers > 1 else ''})...", file=sys.stderr)
        
        response = client.models.generate_content(
            model=config.get("gemini_model", "gemini-3-flash-preview"),
            contents=[
                types.Content(
                    parts=[
                        types.Part.from_uri(file_uri=uploaded_file.uri, mime_type=mime_type),
                        types.Part.from_text(text=prompt),
                    ]
                )
            ],
        )
        
        result = response.text.strip() if response.text else ""
        
        # Clean up: remove any markdown code blocks
        if result.startswith("```"):
            lines = result.split("\n")
            lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            result = "\n".join(lines)
        
        # Delete uploaded file from Gemini
        try:
            client.files.delete(name=uploaded_file.name)
        except:
            pass  # Ignore deletion errors
        
        print("✓ Transcription complete (Gemini)", file=sys.stderr)
        return result
    
    finally:
        # Clean up temp directory
        shutil.rmtree(temp_dir, ignore_errors=True)


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
    parser.add_argument("--language", choices=["english", "croatian"], default="english",
                        help="Audio language (default: english)")
    parser.add_argument("--fallback", choices=["auto", "gemini", "gpu"], default="auto",
                        help="Transcription backend: auto (GPU if available), gemini (force), gpu (force)")
    args = parser.parse_args()
    
    if not Path(args.file).exists():
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)
    
    config = get_config()
    
    # Determine which backend to use
    use_gpu = False
    if args.fallback == "gpu":
        use_gpu = True
        print("Using GPU transcription (forced)", file=sys.stderr)
    elif args.fallback == "gemini":
        use_gpu = False
        print("Using Gemini transcription (forced)", file=sys.stderr)
    else:  # auto
        use_gpu = is_gpu_available()
    
    # Step 1: Transcribe
    if use_gpu:
        transcript = transcribe_with_diarization(
            args.file,
            model_name=args.model,
            batch_size=args.batch_size,
            hf_token=config.get("hf_token"),
            num_speakers=args.num_speakers,
        )
    else:
        transcript = transcribe_with_gemini(
            args.file,
            language=args.language,
            num_speakers=args.num_speakers,
            config=config,
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
