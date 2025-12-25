#!/usr/bin/env python3
"""Annotate code files using Gemini LLM.

Supports multiple annotation modes:
- studify_algo: Annotate algorithmic code for Anki flashcards (Big-O, techniques)
- studify_lang: Annotate language feature demos for Anki flashcards
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
                        help="Prompt to use (studify_algo, studify_lang)")
    parser.add_argument("--output", "-o", help="Output file (default: overwrite input)")
    parser.add_argument("--backup", "-b", action="store_true",
                        help="Create a .bak backup before overwriting")
    args = parser.parse_args()
    
    if not Path(args.file).exists():
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)
    
    config = get_config()
    result = annotate_code(args.file, args.prompt, config)
    
    # Output
    output_path = args.output or args.file
    
    if args.backup and output_path == args.file:
        backup_path = args.file + ".bak"
        Path(args.file).rename(backup_path)
        print(f"Backup saved to: {backup_path}", file=sys.stderr)
    
    Path(output_path).write_text(result)
    print(f"Saved to: {output_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
