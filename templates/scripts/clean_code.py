#!/usr/bin/env python3
"""Clean and comment code files using Gemini LLM.

Removes notebook artifacts, adds clear educational comments,
while keeping the code logic unchanged.
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
    '.rs': 'Rust',
    '.go': 'Go',
    '.rb': 'Ruby',
    '.sh': 'Bash',
    '.sql': 'SQL',
}


def clean_and_comment(file_path: str, config: dict) -> str:
    """Use Gemini to clean and comment the code file."""
    content = Path(file_path).read_text()
    filename = Path(file_path).name
    
    # Detect language from extension
    ext = Path(file_path).suffix.lower()
    language = LANG_MAP.get(ext, 'code')
    
    print(f"Processing {filename} ({language})...", file=sys.stderr)
    print(f"Using model: {config['gemini_model']}", file=sys.stderr)
    
    # Load and format prompt
    prompt_template = load_prompt("clean_code")
    prompt = prompt_template.format(
        language=language,
        language_lower=language.lower(),
        filename=filename,
        content=content,
    )
    
    result = call_gemini(prompt, config)
    print("✓ Code cleaned and commented", file=sys.stderr)
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Clean and comment code files using Gemini LLM"
    )
    parser.add_argument("file", help="Code file to process")
    parser.add_argument("--output", "-o", help="Output file (default: overwrite input)")
    parser.add_argument("--backup", "-b", action="store_true",
                        help="Create a .bak backup before overwriting")
    args = parser.parse_args()
    
    if not Path(args.file).exists():
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)
    
    config = get_config()
    result = clean_and_comment(args.file, config)
    
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
