#!/usr/bin/env python3
"""Retype PDF - Convert PDF or images (handwritten or printed) to clean LaTeX.

Uses Gemini AI to:
1. Recognize text, math, and diagrams (handwritten or printed)
2. Convert to proper LaTeX
3. Compile to clean PDF

Supports both PDF files and direct image input.
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent / "lib"))
from common import get_config, call_gemini, load_prompt


# Image extensions we support
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp', '.tiff', '.tif'}

# LaTeX document template
LATEX_PREAMBLE = r"""\documentclass[11pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{amsmath,amssymb,amsfonts}
\usepackage{physics}
\usepackage{graphicx}
\usepackage{geometry}
\usepackage{tikz}
\usepackage{circuitikz}
\usepackage{esint}
\usepackage{enumitem}
\usepackage{siunitx}
\usepackage{multicol}
\usepackage{cancel}
\usepackage{booktabs}
\usepackage{tikz-3dplot}
\usetikzlibrary{arrows.meta,calc,patterns,decorations.markings,decorations.pathmorphing,shapes,positioning,3d}
\geometry{margin=1.5cm}
\setlength{\parindent}{0pt}
\setlength{\parskip}{0.3em}

\title{%s}
\date{\today}

\begin{document}
\maketitle

"""

LATEX_CLOSING = r"""

\end{document}
"""


def is_image(path: str) -> bool:
    """Check if a file is an image based on extension."""
    return Path(path).suffix.lower() in IMAGE_EXTENSIONS


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
    
    prompt = load_prompt("retype_to_latex")
    
    result = call_gemini(
        prompt,
        config,
        model=config.get("gemini_model"),  # Use Flash for speed
        image_paths=[image_path],
    )
    
    return result


def compile_latex(tex_path: str, output_dir: str) -> str:
    """Compile LaTeX to PDF using pdflatex."""
    for _ in range(2):  # Run twice for references
        subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "-output-directory", output_dir, tex_path],
            capture_output=True, cwd=output_dir  # Don't decode output (may contain non-UTF8)
        )
    
    tex_name = Path(tex_path).stem
    pdf_path = os.path.join(output_dir, tex_name + ".pdf")
    
    if os.path.exists(pdf_path):
        return pdf_path
    
    print("Warning: PDF compilation may have failed. Check .log file.", file=sys.stderr)
    return pdf_path


def main():
    parser = argparse.ArgumentParser(
        description="Retype PDF - Convert PDF or images to clean LaTeX"
    )
    parser.add_argument("files", nargs="+", help="PDF file or image files to process")
    parser.add_argument("--output", "-o", help="Output PDF path (default: input_clean.pdf)")
    parser.add_argument("--keep-tex", action="store_true", help="Keep the .tex file")
    args = parser.parse_args()
    
    # Check all files exist
    for f in args.files:
        if not Path(f).exists():
            print(f"Error: File not found: {f}", file=sys.stderr)
            sys.exit(1)
    
    config = get_config()
    
    # Determine if we're processing images or a PDF
    all_images = all(is_image(f) for f in args.files)
    
    if all_images:
        # Direct image input - sort by name for consistent ordering
        images = sorted(args.files)
        # Use first image's name for output
        input_path = Path(images[0])
        print(f"Processing {len(images)} image(s)...", file=sys.stderr)
    else:
        # PDF input - only accept single PDF
        if len(args.files) > 1:
            print("Error: Multiple PDFs not supported. Use images for batch input.", file=sys.stderr)
            sys.exit(1)
        input_path = Path(args.files[0])
        if input_path.suffix.lower() != '.pdf':
            print(f"Error: Expected PDF or images, got: {input_path.suffix}", file=sys.stderr)
            sys.exit(1)
        images = None  # Will be populated from PDF
        print(f"Processing: {input_path.name}", file=sys.stderr)
    
    print(f"Using model: {config.get('gemini_model')}", file=sys.stderr)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Step 1: Get images (convert PDF if needed)
        if images is None:
            print("Converting PDF to images...", file=sys.stderr)
            images = pdf_to_images(str(input_path), tmpdir)
        print(f"  Found {len(images)} page(s)", file=sys.stderr)
        
        # Step 2: Process each page with Gemini
        print("Processing pages with Gemini...", file=sys.stderr)
        pages_content = []
        skipped_pages = []
        for i, img_path in enumerate(images, 1):
            try:
                content = process_page(img_path, i, len(images), config)
                pages_content.append(content)
            except ValueError as e:
                print(f"  ⚠ Skipping page {i}: {e}", file=sys.stderr)
                skipped_pages.append(i)
                pages_content.append(f"% Page {i} skipped due to content restrictions")
        
        if skipped_pages:
            print(f"  Warning: Skipped pages: {skipped_pages}", file=sys.stderr)
        
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
