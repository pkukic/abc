#!/usr/bin/env python3
"""Annotate code files using Gemini LLM.

Supports multiple annotation modes:
- studify_algo: Annotate algorithmic code for Anki flashcards (Big-O, techniques)
- studify_lang: Annotate language feature demos for Anki flashcards
- studify_os: Annotate OS-level C code for Anki flashcards

Refresh feature: If file.bak exists, uses it as source to allow re-running with newer models.
"""

import argparse
import sys
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent / "lib"))
from common import get_config, call_gemini, load_prompt


# Language detection from file extension
LANG_MAP = {
    '.py': 'Python',
    '.js': 'JavaScript',
    '.ts': 'TypeScript',
    '.java': 'Java',
    '.cpp': 'C++',
    '.c': 'C',
    '.h': 'C/C++ Header',
    '.hpp': 'C++ Header',
    '.rs': 'Rust',
    '.go': 'Go',
    '.rb': 'Ruby',
    '.sh': 'Bash',
    '.sql': 'SQL',
    '.hs': 'Haskell',
    '.scala': 'Scala',
    '.kt': 'Kotlin',
    '.swift': 'Swift',
    '.cs': 'C#',
}


def annotate_code(file_path: str, prompt_name: str, config: dict) -> str:
    """Use Gemini to annotate the code file with the specified prompt."""
    content = Path(file_path).read_text()
    filename = Path(file_path).name
    
    # Detect language from extension
    ext = Path(file_path).suffix.lower()
    language = LANG_MAP.get(ext, 'code')
    
    print(f"Processing {filename} ({language})...", file=sys.stderr)
    print(f"Using model: {config['gemini_model']}", file=sys.stderr)
    print(f"Mode: {prompt_name}", file=sys.stderr)
    
    # Load and format prompt
    prompt_template = load_prompt(prompt_name)
    prompt = prompt_template.format(
        language=language,
        language_lower=language.lower(),
        filename=filename,
        content=content,
    )
    
    result = call_gemini(prompt, config)
    print(f"✓ Code annotated", file=sys.stderr)
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Annotate code files using Gemini LLM"
    )
    parser.add_argument("file", help="Code file to process")
    parser.add_argument("--prompt", "-p", default="studify_algo",
                        help="Prompt to use (studify_algo, studify_lang, studify_os)")
    parser.add_argument("--output", "-o", help="Output file (default: overwrite input)")
    parser.add_argument("--backup", "-b", action="store_true",
                        help="Create a .bak backup before overwriting")
    args = parser.parse_args()
    
    file_path = Path(args.file).resolve()  # Use absolute path
    backup_path = file_path.with_suffix(file_path.suffix + ".bak")
    
    # Refresh mode: if .bak exists, use it as source
    if backup_path.exists():
        source_path = backup_path
        print(f"Refresh mode: using {backup_path.name} as source", file=sys.stderr)
    else:
        source_path = file_path
    
    if not source_path.exists():
        print(f"Error: File not found: {source_path}", file=sys.stderr)
        sys.exit(1)
    
    config = get_config()
    result = annotate_code(str(source_path), args.prompt, config)
    
    # Output
    output_path = Path(args.output).resolve() if args.output else file_path
    
    # Create backup if requested and not in refresh mode
    if args.backup and not backup_path.exists() and output_path == file_path:
        file_path.rename(backup_path)
        print(f"Backup saved to: {backup_path}", file=sys.stderr)
    
    output_path.write_text(result)
    print(f"Saved to: {output_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
