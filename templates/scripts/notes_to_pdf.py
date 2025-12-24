#!/usr/bin/env python3
"""Convert handwritten PDF notes to LaTeX and then to clean PDF.

Uses Gemini 3 Pro Preview to:
1. Recognize handwritten text, math, and sketches
2. Convert to proper LaTeX
3. Synthesize questions if only answers are present
4. Compile to PDF
"""

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent / "lib"))
from common import get_config, call_gemini, load_prompt


# LaTeX document template
LATEX_PREAMBLE = r"""\documentclass[11pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{amsmath,amssymb,amsfonts}
\usepackage{physics}
\usepackage{graphicx}
\usepackage{geometry}
\usepackage{tikz}
\usepackage{esint}
\usepackage{enumitem}
\geometry{margin=2.5cm}

\title{%s}
\date{\today}

\begin{document}
\maketitle

"""

LATEX_CLOSING = r"""

\end{document}
"""


def pdf_to_images(pdf_path: str, output_dir: str) -> list:
    """Convert PDF pages to images using pdftoppm."""
    prefix = os.path.join(output_dir, "page")
    
    result = subprocess.run(
        ["pdftoppm", "-png", "-r", "200", pdf_path, prefix],
        capture_output=True, text=True
    )
    
    if result.returncode != 0:
        print(f"Error converting PDF: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    
    return sorted(str(f) for f in Path(output_dir).glob("page-*.png"))


def process_page(image_path: str, page_num: int, total_pages: int, config: dict) -> str:
    """Send page image to Gemini and get LaTeX output."""
    print(f"  Processing page {page_num}/{total_pages}...", file=sys.stderr)
    
    prompt = load_prompt("notes_to_latex")
    
    result = call_gemini(
        prompt,
        config,
        model=config.get("gemini_model_pro"),
        image_paths=[image_path],
    )
    
    return result


def compile_latex(tex_path: str, output_dir: str) -> str:
    """Compile LaTeX to PDF using pdflatex."""
    for _ in range(2):  # Run twice for references
        subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "-output-directory", output_dir, tex_path],
            capture_output=True, text=True, cwd=output_dir
        )
    
    tex_name = Path(tex_path).stem
    pdf_path = os.path.join(output_dir, tex_name + ".pdf")
    
    if os.path.exists(pdf_path):
        return pdf_path
    
    print("Warning: PDF compilation may have failed. Check .log file.", file=sys.stderr)
    return pdf_path


def main():
    parser = argparse.ArgumentParser(
        description="Convert handwritten PDF notes to clean LaTeX PDF"
    )
    parser.add_argument("file", help="PDF file to process")
    parser.add_argument("--output", "-o", help="Output PDF path (default: input_clean.pdf)")
    parser.add_argument("--keep-tex", action="store_true", help="Keep the .tex file")
    args = parser.parse_args()
    
    if not Path(args.file).exists():
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)
    
    config = get_config()
    input_path = Path(args.file)
    
    print(f"Processing: {input_path.name}", file=sys.stderr)
    print(f"Using model: {config.get('gemini_model_pro')}", file=sys.stderr)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Step 1: Convert PDF to images
        print("Converting PDF to images...", file=sys.stderr)
        images = pdf_to_images(args.file, tmpdir)
        print(f"  Found {len(images)} page(s)", file=sys.stderr)
        
        # Step 2: Process each page with Gemini
        print("Processing pages with Gemini...", file=sys.stderr)
        pages_content = []
        for i, img_path in enumerate(images, 1):
            content = process_page(img_path, i, len(images), config)
            pages_content.append(content)
        
        # Step 3: Create LaTeX document
        print("Creating LaTeX document...", file=sys.stderr)
        title = input_path.stem.replace("_", " ").title().replace("_", r"\_")
        latex_content = LATEX_PREAMBLE % title
        latex_content += "\n\n\\newpage\n\n".join(pages_content)
        latex_content += LATEX_CLOSING
        
        tex_path = os.path.join(tmpdir, "output.tex")
        Path(tex_path).write_text(latex_content)
        
        # Step 4: Compile to PDF
        print("Compiling LaTeX to PDF...", file=sys.stderr)
        pdf_path = compile_latex(tex_path, tmpdir)
        
        # Step 5: Copy output
        if args.output:
            output_path = args.output
        else:
            output_path = str(input_path.with_stem(input_path.stem + "_clean").with_suffix(".pdf"))
        
        import shutil
        if os.path.exists(pdf_path):
            shutil.copy(pdf_path, output_path)
            print(f"✓ Saved PDF: {output_path}", file=sys.stderr)
            
            if args.keep_tex:
                tex_output = output_path.replace(".pdf", ".tex")
                shutil.copy(tex_path, tex_output)
                print(f"✓ Saved TeX: {tex_output}", file=sys.stderr)
        else:
            print("✗ PDF compilation failed", file=sys.stderr)
            tex_output = output_path.replace(".pdf", ".tex")
            shutil.copy(tex_path, tex_output)
            print(f"  Saved TeX for debugging: {tex_output}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
