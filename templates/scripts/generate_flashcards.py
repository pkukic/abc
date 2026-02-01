#!/usr/bin/env python3
"""Generate Anki flashcards from files using AI.

Uses Anki-Connect API to add cards directly to Anki.
Requires Anki desktop app with Anki-Connect add-on (code: 2055492159).
"""

import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent / "lib"))
from common import get_config, call_gemini, load_prompt, pdf_to_images

ANKI_CONNECT_URL = "http://127.0.0.1:8765"

# Supported file extensions for direct text reading
TEXT_EXTENSIONS = {
    '.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.hpp', '.rs', '.go',
    '.rb', '.sh', '.sql', '.hs', '.scala', '.kt', '.swift', '.cs', '.mzn',
    '.txt', '.md', '.rst', '.tex', '.json', '.yaml', '.yml', '.toml', '.xml',
    '.html', '.css', '.scss', '.less', '.vue', '.jsx', '.tsx',
}


def anki_invoke(action: str, max_retries: int = 3, **params) -> dict:
    """Send a request to Anki-Connect API with retry logic.
    
    Args:
        action: Anki-Connect action name
        max_retries: Maximum number of retry attempts for transient errors
        **params: Action parameters
        
    Returns:
        Response result from Anki-Connect
        
    Raises:
        Exception: If Anki-Connect is not reachable or returns an error
    """
    import time
    
    request_data = json.dumps({
        'action': action,
        'version': 6,
        'params': params
    }).encode('utf-8')
    
    last_error = None
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(ANKI_CONNECT_URL, request_data)
            response = json.load(urllib.request.urlopen(req, timeout=30))
            
            if len(response) != 2:
                raise Exception('Unexpected response format from Anki-Connect')
            
            error = response.get('error')
            if error is not None:
                # Check for retryable errors (500 INTERNAL, etc.)
                if 'INTERNAL' in str(error) or '500' in str(error):
                    last_error = Exception(f"Anki-Connect error: {error}")
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 2  # 2, 4, 6 seconds
                        print(f"  Retrying in {wait_time}s due to: {error}", file=sys.stderr)
                        time.sleep(wait_time)
                        continue
                raise Exception(f"Anki-Connect error: {error}")
            
            return response['result']
            
        except urllib.error.URLError as e:
            last_error = e
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2
                print(f"  Connection failed, retrying in {wait_time}s...", file=sys.stderr)
                time.sleep(wait_time)
                continue
            raise Exception(
                "Cannot connect to Anki. Make sure Anki is running with "
                "Anki-Connect add-on installed (code: 2055492159)"
            ) from e
    
    # If we exhausted retries
    if last_error:
        raise last_error
    raise Exception("Failed after all retry attempts")


def is_anki_running() -> bool:
    """Check if Anki-Connect is available."""
    try:
        anki_invoke('version')
        return True
    except Exception:
        return False


def ensure_anki_running(max_wait: int = 30) -> bool:
    """Ensure Anki is running, launching it if necessary.
    
    Args:
        max_wait: Maximum seconds to wait for Anki to start
        
    Returns:
        True if Anki is running, False if failed to start
    """
    import subprocess
    import time
    
    if is_anki_running():
        return True
    
    print("Starting Anki...", file=sys.stderr)
    
    # Launch Anki in background
    try:
        subprocess.Popen(
            ['anki'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
    except FileNotFoundError:
        print("✗ Anki not found. Please install Anki.", file=sys.stderr)
        return False
    
    # Wait for Anki-Connect to become available
    start_time = time.time()
    while time.time() - start_time < max_wait:
        time.sleep(1)
        if is_anki_running():
            print("✓ Anki started", file=sys.stderr)
            return True
        print("  Waiting for Anki-Connect...", file=sys.stderr)
    
    print("✗ Timed out waiting for Anki to start", file=sys.stderr)
    return False


def get_deck_names() -> list:
    """Get list of all deck names in Anki."""
    return anki_invoke('deckNames')


def get_model_names() -> list:
    """Get list of all model (note type) names in Anki."""
    return anki_invoke('modelNames')


def create_deck(name: str) -> int:
    """Create a new deck (or get existing deck ID).
    
    Args:
        name: Deck name (use :: for hierarchy, e.g., "Parent::Child")
        
    Returns:
        Deck ID
    """
    return anki_invoke('createDeck', deck=name)


def add_notes(deck: str, cards: list, available_models: list) -> list:
    """Add multiple notes to Anki with various card types.
    
    Args:
        deck: Target deck name
        cards: List of card dicts with 'type' and content fields
        available_models: List of available model names in Anki
        
    Returns:
        List of note IDs (None for failed notes)
    """
    notes = []
    for card in cards:
        card_type = card.get('type', 'Basic')
        
        # Validate model exists, fallback to Basic
        if card_type not in available_models:
            card_type = 'Basic'
        
        # Build note based on card type
        if card_type == 'Cloze':
            # Cloze cards use 'Text' field
            note = {
                'deckName': deck,
                'modelName': 'Cloze',
                'fields': {
                    'Text': card.get('text', ''),
                    'Extra': card.get('extra', '')
                }
            }
        else:
            # Basic and reversed cards use Front/Back
            note = {
                'deckName': deck,
                'modelName': card_type,
                'fields': {
                    'Front': card.get('front', ''),
                    'Back': card.get('back', '')
                }
            }
        
        note['options'] = {
            'allowDuplicate': False,
            'duplicateScope': 'deck'
        }
        notes.append(note)
    
    return anki_invoke('addNotes', notes=notes)


def extract_content(file_path: str, config: dict) -> tuple:
    """Extract content from a file.
    
    Args:
        file_path: Path to the file
        config: Config dict for potential LLM calls
        
    Returns:
        Tuple of (content_string, is_image_based)
        For PDFs, returns list of image paths instead of content string
    """
    path = Path(file_path)
    ext = path.suffix.lower()
    
    if ext == '.pdf':
        # Convert PDF to images for LLM processing
        import tempfile
        import os
        temp_dir = tempfile.mkdtemp()
        images = pdf_to_images(str(path), temp_dir, prefix="page")
        return images, True
    
    if ext in TEXT_EXTENSIONS:
        return path.read_text(errors='ignore'), False
    
    # For unknown types, try to read as text
    try:
        return path.read_text(errors='ignore'), False
    except Exception:
        raise ValueError(f"Cannot read file: {file_path}")


# Tag for marking files that have flashcards generated
ANKI_TAG = 'anki-flashcards'


def get_file_tags(file_path: str) -> list:
    """Get KDE file tags from extended attributes.
    
    Args:
        file_path: Path to file
        
    Returns:
        List of tag strings
    """
    try:
        tags_bytes = os.getxattr(file_path, 'user.xdg.tags')
        return [t.strip() for t in tags_bytes.decode('utf-8').split(',') if t.strip()]
    except OSError:
        return []


def set_file_tags(file_path: str, tags: list) -> bool:
    """Set KDE file tags via extended attributes.
    
    Args:
        file_path: Path to file
        tags: List of tag strings
        
    Returns:
        True if successful
    """
    try:
        tags_str = ','.join(tags)
        os.setxattr(file_path, 'user.xdg.tags', tags_str.encode('utf-8'))
        return True
    except OSError as e:
        print(f"  ⚠ Could not set file tags: {e}", file=sys.stderr)
        return False


def has_flashcards_tag(file_path: str) -> bool:
    """Check if file has the anki-flashcards tag."""
    return ANKI_TAG in get_file_tags(file_path)


def mark_file_as_processed(file_path: str) -> bool:
    """Add the anki-flashcards tag to a file.
    
    Args:
        file_path: Path to file
        
    Returns:
        True if tag was added successfully
    """
    tags = get_file_tags(file_path)
    if ANKI_TAG not in tags:
        tags.append(ANKI_TAG)
        return set_file_tags(file_path, tags)
    return True  # Already tagged


def _fix_math_in_text(text: str) -> str:
    """Convert $...$ math notation to Anki's MathJax format.
    
    Converts:
    - $$...$$ -> \\[...\\] (display math)
    - $...$ -> \\(...\\) (inline math)
    - Also fixes double-escaped backslashes
    """
    import re
    
    if not text:
        return text
    
    # Fix double-escaped backslashes (\\\\( -> \\()
    text = re.sub(r'\\\\\\\\', r'\\\\', text)
    
    # Convert display math first ($$...$$) to \[...\]
    text = re.sub(r'\$\$(.+?)\$\$', r'\\[\1\\]', text, flags=re.DOTALL)
    
    # Convert inline math ($...$) to \(...\)
    # Be careful not to match already-converted \[...\]
    text = re.sub(r'(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)', r'\\(\1\\)', text)
    
    return text


def _fix_math_formatting(card: dict) -> dict:
    """Fix math formatting in all text fields of a card."""
    result = card.copy()
    
    # Fix front/back for Basic cards
    if 'front' in result:
        result['front'] = _fix_math_in_text(result['front'])
    if 'back' in result:
        result['back'] = _fix_math_in_text(result['back'])
    
    # Fix text for Cloze cards
    if 'text' in result:
        result['text'] = _fix_math_in_text(result['text'])
    
    return result


def _fix_json_escapes(json_str: str) -> str:
    r"""Fix invalid JSON escape sequences that LLMs sometimes produce.
    
    JSON only allows: \", \\, \/, \b, \f, \n, \r, \t, \uXXXX
    LLMs sometimes produce invalid escapes like \e, \a, \s, \(, \[, etc.
    """
    # Valid JSON escape characters (the character after backslash)
    valid_escapes = {'"', '\\', '/', 'b', 'f', 'n', 'r', 't', 'u'}
    
    result = []
    i = 0
    while i < len(json_str):
        char = json_str[i]
        
        if char == '\\' and i + 1 < len(json_str):
            next_char = json_str[i + 1]
            
            if next_char in valid_escapes:
                # Valid escape sequence - keep as is
                result.append(char)
                result.append(next_char)
                i += 2
                # Handle \uXXXX
                if next_char == 'u' and i + 4 <= len(json_str):
                    result.append(json_str[i:i+4])
                    i += 4
            elif next_char == '\\':
                # Already escaped backslash
                result.append('\\\\')
                i += 2
            else:
                # Invalid escape - double the backslash to escape it
                result.append('\\\\')
                result.append(next_char)
                i += 2
        else:
            result.append(char)
            i += 1
    
    return ''.join(result)

def generate_flashcards(file_path: str, content, is_images: bool, config: dict, 
                        available_models: list, existing_decks: list) -> dict:
    """Generate flashcards from content using LLM.
    
    Args:
        file_path: Original file path (for context)
        content: Text content or list of image paths
        is_images: True if content is image paths
        config: Config dict with API keys
        available_models: List of available Anki note types
        existing_decks: List of existing deck names in Anki
        
    Returns:
        Dict with 'deck' and 'cards' keys
    """
    filename = Path(file_path).name
    
    # Format available models for prompt
    # Focus on the useful ones for flashcard generation
    useful_models = [m for m in available_models if m in [
        'Basic', 'Basic (and reversed card)', 'Basic (optional reversed card)',
        'Basic (type in the answer)', 'Cloze'
    ]]
    models_str = ', '.join(useful_models) if useful_models else 'Basic, Cloze'
    
    # Format existing decks for prompt (exclude Default)
    decks_list = [d for d in existing_decks if d != 'Default']
    decks_str = '\n'.join(f"- {d}" for d in decks_list) if decks_list else '(No existing decks)'
    
    # Load prompt template
    prompt_template = load_prompt('generate_flashcards')
    
    if is_images:
        # For PDFs/images, include filename context
        prompt = prompt_template.format(
            filename=filename,
            content="[Document images attached - analyze the visual content]",
            available_models=models_str,
            existing_decks=decks_str
        )
        result = call_gemini(prompt, config, model=config.get('gemini_model_pro'), image_paths=content)
    else:
        prompt = prompt_template.format(
            filename=filename,
            content=content[:50000],  # Limit content size
            available_models=models_str,
            existing_decks=decks_str
        )
        result = call_gemini(prompt, config, model=config.get('gemini_model_pro'))
    
    # Parse JSON response
    try:
        # Try to extract JSON from the response
        # First, strip whitespace
        result = result.strip()
        
        # Handle markdown code blocks (```json ... ``` or ``` ... ```)
        if '```' in result:
            # Find content between code blocks
            import re
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', result)
            if json_match:
                result = json_match.group(1).strip()
        
        # Try to find JSON object in the response
        # Look for the opening brace
        start_idx = result.find('{')
        if start_idx == -1:
            raise ValueError("No JSON object found in response")
        
        # Find the matching closing brace
        brace_count = 0
        end_idx = start_idx
        for i, char in enumerate(result[start_idx:], start_idx):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_idx = i + 1
                    break
        
        json_str = result[start_idx:end_idx]
        
        # Fix common JSON escape issues from LLM output
        json_str = _fix_json_escapes(json_str)
        
        data = json.loads(json_str)
        
        if 'deck' not in data or 'cards' not in data:
            raise ValueError("Response missing 'deck' or 'cards' field")
        
        # Post-process cards to fix math formatting
        data['cards'] = [_fix_math_formatting(card) for card in data['cards']]
        
        return data
    except json.JSONDecodeError as e:
        print(f"Failed to parse LLM response as JSON: {e}", file=sys.stderr)
        print(f"Response was: {result[:500]}...", file=sys.stderr)
        raise ValueError("LLM did not return valid JSON") from e


def process_file(file_path: str, config: dict) -> dict:
    """Process a single file and add flashcards to Anki.
    
    Args:
        file_path: Path to the file
        config: Config dict
        
    Returns:
        Dict with processing results
    """
    print(f"Processing: {file_path}", file=sys.stderr)
    
    # Get available models and existing decks
    available_models = get_model_names()
    existing_decks = get_deck_names()
    
    # Extract content
    content, is_images = extract_content(file_path, config)
    
    # Generate flashcards
    print("  Generating flashcards...", file=sys.stderr)
    result = generate_flashcards(file_path, content, is_images, config, available_models, existing_decks)
    
    deck = result['deck']
    cards = result['cards']
    
    # Count card types
    type_counts = {}
    for card in cards:
        t = card.get('type', 'Basic')
        type_counts[t] = type_counts.get(t, 0) + 1
    type_summary = ', '.join(f"{v} {k}" for k, v in type_counts.items())
    
    print(f"  Deck: {deck}", file=sys.stderr)
    print(f"  Cards: {len(cards)} ({type_summary})", file=sys.stderr)
    
    # Create deck if needed
    existing_decks = get_deck_names()
    if deck not in existing_decks:
        print(f"  Creating new deck: {deck}", file=sys.stderr)
        create_deck(deck)
    
    # Add notes
    note_ids = add_notes(deck, cards, available_models)
    
    added = sum(1 for nid in note_ids if nid is not None)
    skipped = len(note_ids) - added
    
    print(f"  ✓ Added {added} cards", file=sys.stderr)
    if skipped > 0:
        print(f"  ⚠ Skipped {skipped} duplicates", file=sys.stderr)
    
    # Tag file as processed (for Dolphin visual indicator)
    if added > 0:
        if mark_file_as_processed(file_path):
            print(f"  ✓ Tagged file (visible in Dolphin tags column)", file=sys.stderr)
    
    return {
        'file': file_path,
        'deck': deck,
        'added': added,
        'skipped': skipped
    }


def main():
    parser = argparse.ArgumentParser(
        description="Generate Anki flashcards from files using AI"
    )
    parser.add_argument("files", nargs='+', help="Files to process")
    args = parser.parse_args()
    
    config = get_config()
    
    # Ensure Anki is running (launch if needed)
    if not ensure_anki_running():
        sys.exit(1)
    print("✓ Connected to Anki", file=sys.stderr)
    
    results = []
    for file_path in args.files:
        try:
            result = process_file(file_path, config)
            results.append(result)
        except Exception as e:
            print(f"  ✗ Error: {e}", file=sys.stderr)
            results.append({'file': file_path, 'error': str(e)})
    
    # Summary
    print("\n" + "=" * 40, file=sys.stderr)
    total_added = sum(r.get('added', 0) for r in results)
    total_skipped = sum(r.get('skipped', 0) for r in results)
    errors = sum(1 for r in results if 'error' in r)
    
    print(f"Total: {total_added} cards added, {total_skipped} skipped, {errors} errors", file=sys.stderr)


if __name__ == "__main__":
    main()
