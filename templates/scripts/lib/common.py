"""Shared utilities for ABC scripts.

This module provides common functionality used across all ABC scripts:
- Configuration loading from .env files
- Gemini API client initialization
- Common helper functions
"""

import os
import sys
from pathlib import Path
from typing import Optional

# Config file location - same dir as the script that imports this
def get_script_dir() -> Path:
    """Get directory of the main script (not this lib)."""
    import __main__
    if hasattr(__main__, '__file__'):
        return Path(__main__.__file__).parent
    return Path.cwd()


def get_config() -> dict:
    """Get configuration from environment or .env file.
    
    Looks for .env in the same directory as the calling script.
    
    Returns dict with keys:
        - gemini_api_key
        - gemini_model (default: gemini-3-flash-preview)
        - gemini_model_pro (default: gemini-3-pro-preview)
        - hf_token
    """
    config = {
        "gemini_api_key": os.environ.get("GEMINI_API_KEY"),
        "gemini_model": os.environ.get("GEMINI_MODEL"),
        "gemini_model_pro": os.environ.get("GEMINI_MODEL_PRO"),
        "hf_token": os.environ.get("HF_TOKEN"),
    }
    
    env_file = get_script_dir() / ".env"
    
    if env_file.exists():
        for line in env_file.read_text().splitlines():
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
                elif key == "gemini_model_pro" and not config["gemini_model_pro"]:
                    config["gemini_model_pro"] = value
                elif key == "hf_token" and not config["hf_token"]:
                    config["hf_token"] = value
    
    # Defaults
    if not config["gemini_model"]:
        config["gemini_model"] = "gemini-3-flash-preview"
    if not config["gemini_model_pro"]:
        config["gemini_model_pro"] = "gemini-3-pro-preview"
    
    return config


def get_gemini_client(config: dict = None):
    """Get initialized Gemini client.
    
    Args:
        config: Optional config dict. If not provided, calls get_config().
        
    Returns:
        google.genai.Client instance
        
    Raises:
        SystemExit if google-genai not installed or API key missing
    """
    try:
        from google import genai
    except ImportError:
        print("google-genai not installed. Run: ./install_all.sh", file=sys.stderr)
        sys.exit(1)
    
    if config is None:
        config = get_config()
    
    api_key = config.get("gemini_api_key")
    if not api_key:
        print("Error: GEMINI_API_KEY not set in .env", file=sys.stderr)
        sys.exit(1)
    
    return genai.Client(api_key=api_key)


def load_prompt(name: str) -> str:
    """Load a prompt template from the prompts directory.
    
    Args:
        name: Name of the prompt file (without .txt extension)
        
    Returns:
        Prompt template string
    """
    prompts_dir = get_script_dir() / "prompts"
    prompt_file = prompts_dir / f"{name}.txt"
    
    if not prompt_file.exists():
        print(f"Error: Prompt file not found: {prompt_file}", file=sys.stderr)
        sys.exit(1)
    
    return prompt_file.read_text()


def call_gemini(
    prompt: str,
    config: dict = None,
    model: str = None,
    image_paths: list = None,
    temperature: float = 1.0,
) -> str:
    """Call Gemini API with text and optional images.
    
    Args:
        prompt: The prompt text
        config: Optional config dict
        model: Model name override (default uses config["gemini_model"])
        image_paths: Optional list of image file paths to include
        temperature: Generation temperature (0.0-2.0, higher = more creative)
        
    Returns:
        Response text from Gemini
    """
    import base64
    from google.genai import types
    
    if config is None:
        config = get_config()
    
    client = get_gemini_client(config)
    model_name = model or config.get("gemini_model")
    
    # Build content parts
    parts = [types.Part.from_text(text=prompt)]
    
    if image_paths:
        for img_path in image_paths:
            with open(img_path, "rb") as f:
                image_data = f.read()
            
            # Detect mime type
            ext = Path(img_path).suffix.lower()
            mime_map = {
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.gif': 'image/gif',
                '.webp': 'image/webp',
            }
            mime_type = mime_map.get(ext, 'image/png')
            
            parts.append(types.Part.from_bytes(data=image_data, mime_type=mime_type))
    
    def _do_request(temp: float):
        """Make the actual API request with given temperature."""
        gen_config = types.GenerateContentConfig(
            temperature=temp,
        )
        return client.models.generate_content(
            model=model_name,
            contents=[types.Content(role="user", parts=parts)],
            config=gen_config,
        )
    
    def _is_recitation_error(resp) -> bool:
        """Check if response failed due to RECITATION."""
        if resp.text is not None:
            return False
        if hasattr(resp, 'candidates') and resp.candidates:
            candidate = resp.candidates[0]
            if hasattr(candidate, 'finish_reason'):
                return 'RECITATION' in str(candidate.finish_reason)
        return False
    
    # First attempt with requested temperature
    response = _do_request(temperature)
    
    # If RECITATION error, retry with higher temperature
    if _is_recitation_error(response) and temperature < 1.5:
        print(f"  RECITATION error, retrying with temperature 1.5...", file=sys.stderr)
        response = _do_request(1.5)
    
    # If still RECITATION, try even higher temperature
    if _is_recitation_error(response):
        print(f"  RECITATION error, retrying with temperature 2.0...", file=sys.stderr)
        response = _do_request(2.0)
    
    # Handle None response (blocked content, errors, etc.)
    if response.text is None:
        # Try to get more info about what went wrong
        if hasattr(response, 'prompt_feedback'):
            print(f"Gemini blocked content: {response.prompt_feedback}", file=sys.stderr)
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'finish_reason'):
                print(f"Finish reason: {candidate.finish_reason}", file=sys.stderr)
            if hasattr(candidate, 'safety_ratings'):
                print(f"Safety ratings: {candidate.safety_ratings}", file=sys.stderr)
        raise ValueError("Gemini returned empty response - content may have been blocked or there was an API error")
    
    result = response.text.strip()
    
    # Remove markdown code blocks if present
    if result.startswith("```"):
        lines = result.split("\n")
        lines = lines[1:]  # Remove first line
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        result = "\n".join(lines)
    
    return result
