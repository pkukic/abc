#!/usr/bin/env python3
"""Clean and comment code files using Gemini LLM.

Removes notebook artifacts, adds clear educational comments,
while keeping the code logic unchanged.
"""

import argparse
import os
import sys
from pathlib import Path

# Config file location
SCRIPT_DIR = Path(__file__).parent
ENV_FILE = SCRIPT_DIR / ".env"


def get_config() -> dict:
    """Get configuration from environment or config file."""
    config = {
        "gemini_api_key": os.environ.get("GEMINI_API_KEY"),
        "gemini_model": os.environ.get("GEMINI_MODEL"),
    }
    
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
    
    if not config["gemini_model"]:
        config["gemini_model"] = "gemini-3-flash-preview"
    
    return config


def clean_and_comment(file_path: str, config: dict) -> str:
    """Use Gemini to clean and comment the code file."""
    try:
        from google import genai
    except ImportError:
        print("google-genai not installed. Run: ./install_all.sh", file=sys.stderr)
        sys.exit(1)
    
    api_key = config["gemini_api_key"]
    model_name = config["gemini_model"]
    
    if not api_key:
        print("Error: GEMINI_API_KEY not set in ~/.local/bin/.env", file=sys.stderr)
        sys.exit(1)
    
    # Read the file
    content = Path(file_path).read_text()
    filename = Path(file_path).name
    
    # Detect language from extension
    ext = Path(file_path).suffix.lower()
    lang_map = {
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
    language = lang_map.get(ext, 'code')
    
    print(f"Processing {filename} ({language})...", file=sys.stderr)
    print(f"Using model: {model_name}", file=sys.stderr)
    
    prompt = f"""You are an expert code reviewer and technical writer. Your task is to clean up and add educational comments to the following {language} code.

RULES:
1. DO NOT change any code logic, variable names, or functionality
2. REMOVE all notebook artifacts like:
   - "# In[N]:" or "# In[ ]:" markers
   - Empty cells or redundant blank lines
   - "#!/usr/bin/env python" and "# coding: utf-8" if duplicated
3. ADD clear, educational comments that explain:
   - What each function does and why
   - The algorithm or approach being used
   - Key insights or tricks in the solution
   - Any mathematical formulas or concepts being applied
4. Keep the problem description at the top if present, but clean it up
5. The comments should be detailed enough that someone could understand HOW to solve this problem just by reading the comments (useful for study/Anki flashcards)
6. Use docstrings for functions where appropriate
7. Output ONLY the cleaned code, no explanations before or after

FILE: {filename}

```{language.lower()}
{content}
```

OUTPUT (cleaned and commented code only):"""

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )
        
        result = response.text.strip()
        
        # Remove markdown code blocks if present
        if result.startswith("```"):
            lines = result.split("\n")
            # Remove first line (```python or similar)
            lines = lines[1:]
            # Remove last line if it's ```
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            result = "\n".join(lines)
        
        print("✓ Code cleaned and commented", file=sys.stderr)
        return result
        
    except Exception as e:
        print(f"Gemini API error: {e}", file=sys.stderr)
        sys.exit(1)


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
    
    # Clean and comment
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
