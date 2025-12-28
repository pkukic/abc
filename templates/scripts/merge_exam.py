#!/usr/bin/env python3
"""Merge Exam - Combine exam PDF with solutions (images, text, or code) into clean LaTeX.

Uses Gemini AI to:
1. Extract questions from an answers/exam PDF
2. Parse solutions from various formats:
   - Handwritten images (PNG, JPG, etc.)
   - Text files (.txt, .md)
   - Source code files (.py, .c, .cpp, .java, etc.)
   - Another PDF with solutions
3. Merge into a formatted LaTeX document
4. Compile to clean PDF

Usage: merge_exam.py exam.pdf solution1.png solution2.py notes.txt ...
"""

import argparse
import os
import shutil
import sys
import tempfile
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent / "lib"))
from common import (
    get_config, call_gemini, load_prompt,
    pdf_to_images, compile_latex, build_latex_document
)


# File type definitions
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp', '.tiff', '.tif'}
TEXT_EXTENSIONS = {'.txt', '.md', '.text', '.sol', '.ans', '.solution'}
CODE_EXTENSIONS = {
    '.py': 'Python',
    '.c': 'C',
    '.cpp': 'C++',
    '.h': 'C/C++ Header',
    '.java': 'Java',
    '.js': 'JavaScript',
    '.ts': 'TypeScript',
    '.rs': 'Rust',
    '.go': 'Go',
    '.rb': 'Ruby',
    '.m': 'MATLAB/Octave',
    '.r': 'R',
    '.sql': 'SQL',
    '.sh': 'Shell',
    '.hs': 'Haskell',
}


def classify_file(path: str) -> str:
    """Classify a file by type.
    
    Returns: 'pdf', 'image', 'text', 'code', or 'unknown'
    """
    suffix = Path(path).suffix.lower()
    
    if suffix == '.pdf':
        return 'pdf'
    elif suffix in IMAGE_EXTENSIONS:
        return 'image'
    elif suffix in TEXT_EXTENSIONS:
        return 'text'
    elif suffix in CODE_EXTENSIONS:
        return 'code'
    else:
        # Try to read as text
        try:
            with open(path, 'r', encoding='utf-8') as f:
                f.read(100)
            return 'text'
        except:
            return 'unknown'


def is_exam_pdf(path: str) -> bool:
    """Heuristic to detect if a PDF is likely the exam (not solutions)."""
    name_lower = Path(path).stem.lower()
    solution_keywords = ['sol', 'rje', 'answer', 'solution', 'odg', 'ries']
    return not any(kw in name_lower for kw in solution_keywords)


def organize_files(files: list) -> tuple:
    """Organize input files into exam PDF and solution materials.
    
    Returns: (exam_pdf, solution_images, solution_texts, solution_codes)
    
    If no PDF is provided, exam_pdf will be None and all images are treated
    as source material for generating the exam.
    """
    pdfs = []
    images = []
    texts = []
    codes = []
    
    for f in files:
        if not Path(f).exists():
            print(f"Error: File not found: {f}", file=sys.stderr)
            sys.exit(1)
        
        ftype = classify_file(f)
        
        if ftype == 'pdf':
            pdfs.append(f)
        elif ftype == 'image':
            images.append(f)
        elif ftype == 'text':
            texts.append(f)
        elif ftype == 'code':
            codes.append(f)
        else:
            print(f"Warning: Unknown file type, treating as text: {f}", file=sys.stderr)
            texts.append(f)
    
    # Identify exam PDF
    exam_pdf = None
    solution_pdfs = []
    
    if len(pdfs) == 0:
        # No PDF - images-only mode
        if not images:
            print("Error: No PDF or images provided.", file=sys.stderr)
            sys.exit(1)
        # All images will be processed together
        return None, [], images, texts, codes
    
    if len(pdfs) == 1:
        # If only one PDF and we have other solution materials, it's the exam
        if images or texts or codes:
            exam_pdf = pdfs[0]
        else:
            # Single PDF with no other files - assume it's the exam
            print("Warning: Only one PDF provided with no solution files.", file=sys.stderr)
            exam_pdf = pdfs[0]
    elif len(pdfs) >= 2:
        # Multiple PDFs - identify which is the exam
        for pdf in pdfs:
            if is_exam_pdf(pdf):
                if exam_pdf is None:
                    exam_pdf = pdf
                else:
                    # Multiple potential exam PDFs - use alphabetically first
                    solution_pdfs.append(pdf)
            else:
                solution_pdfs.append(pdf)
        
        if exam_pdf is None:
            # All PDFs look like solutions - use first alphabetically as exam
            sorted_pdfs = sorted(pdfs)
            exam_pdf = sorted_pdfs[0]
            solution_pdfs = sorted_pdfs[1:]
    
    return exam_pdf, solution_pdfs, images, texts, codes


def read_code_files(code_files: list) -> str:
    """Read source code files and format them for the prompt."""
    if not code_files:
        return ""
    
    parts = []
    for code_file in code_files:
        path = Path(code_file)
        lang = CODE_EXTENSIONS.get(path.suffix.lower(), 'Code')
        content = path.read_text(encoding='utf-8')
        
        parts.append(f"### {path.name} ({lang})\n```{path.suffix[1:]}\n{content}\n```")
    
    return "\n\n".join(parts)


def read_text_files(text_files: list) -> str:
    """Read text files and combine them."""
    if not text_files:
        return ""
    
    parts = []
    for text_file in text_files:
        path = Path(text_file)
        content = path.read_text(encoding='utf-8')
        parts.append(f"### {path.name}\n{content}")
    
    return "\n\n".join(parts)


def merge_with_gemini(
    exam_images: list,
    solution_images: list,
    text_content: str,
    code_content: str,
    config: dict
) -> str:
    """Send all materials to Gemini for intelligent merging."""
    
    # Build the prompt with available materials
    prompt_parts = []
    prompt_parts.append(load_prompt("merge_exam_mixed"))
    
    # Add text/code content to prompt
    materials_section = []
    
    if text_content:
        materials_section.append(f"## TEXT NOTES/SOLUTIONS:\n{text_content}")
    
    if code_content:
        materials_section.append(f"## SOURCE CODE FILES:\n{code_content}")
    
    if materials_section:
        prompt_parts.append("\n\n---\n" + "\n\n".join(materials_section))
    
    prompt = "\n".join(prompt_parts)
    
    # Combine all images
    all_images = exam_images + solution_images
    
    # Summary for user
    print(f"  Sending to Gemini:", file=sys.stderr)
    print(f"    - {len(exam_images)} exam page(s)", file=sys.stderr)
    if solution_images:
        print(f"    - {len(solution_images)} solution image(s)", file=sys.stderr)
    if text_content:
        print(f"    - Text notes included", file=sys.stderr)
    if code_content:
        print(f"    - Source code included", file=sys.stderr)
    
    result = call_gemini(
        prompt,
        config,
        model=config.get("gemini_model_pro"),
        image_paths=all_images,
    )
    
    return result


def merge_images_only_with_gemini(
    images: list,
    text_content: str,
    code_content: str,
    config: dict
) -> str:
    """Generate exam from images only (no PDF source)."""
    
    # Build the prompt with available materials
    prompt_parts = []
    prompt_parts.append(load_prompt("merge_exam_from_images"))
    
    # Add text/code content to prompt
    materials_section = []
    
    if text_content:
        materials_section.append(f"## TEXT NOTES/SOLUTIONS:\n{text_content}")
    
    if code_content:
        materials_section.append(f"## SOURCE CODE FILES:\n{code_content}")
    
    if materials_section:
        prompt_parts.append("\n\n---\n" + "\n\n".join(materials_section))
    
    prompt = "\n".join(prompt_parts)
    
    # Summary for user
    print(f"  Sending to Gemini:", file=sys.stderr)
    print(f"    - {len(images)} source image(s)", file=sys.stderr)
    if text_content:
        print(f"    - Text notes included", file=sys.stderr)
    if code_content:
        print(f"    - Source code included", file=sys.stderr)
    
    result = call_gemini(
        prompt,
        config,
        model=config.get("gemini_model_pro"),
        image_paths=images,
    )
    
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Merge Exam - Combine exam PDF with solutions (images, text, code) or generate from images only"
    )
    parser.add_argument("files", nargs="+", help="Exam PDF + solution files, OR just images (any order)")
    parser.add_argument("--output", "-o", help="Output PDF path (default: input_solved.pdf)")
    parser.add_argument("--keep-tex", action="store_true", help="Keep the .tex file")
    args = parser.parse_args()
    
    # Organize files by type
    exam_pdf, solution_pdfs, images, texts, codes = organize_files(args.files)
    
    config = get_config()
    
    # Check if images-only mode
    if exam_pdf is None:
        # Images-only mode
        print(f"=== Images-Only Mode ===", file=sys.stderr)
        print(f"Source images: {len(images)}", file=sys.stderr)
        if texts:
            print(f"Text files: {', '.join(Path(p).name for p in texts)}", file=sys.stderr)
        if codes:
            print(f"Code files: {', '.join(Path(p).name for p in codes)}", file=sys.stderr)
        print(f"Using model: {config.get('gemini_model_pro')}", file=sys.stderr)
        
        # Sort images by name for consistent ordering
        images = sorted(images)
        
        # Resolve paths
        images = [str(Path(p).resolve()) for p in images]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Read text and code files
            text_content = read_text_files(texts)
            code_content = read_code_files(codes)
            
            # Send to Gemini for generation
            print("Generating exam with Gemini AI...", file=sys.stderr)
            merged_content = merge_images_only_with_gemini(
                images, text_content, code_content, config
            )
            
            # Create LaTeX document
            print("Creating LaTeX document...", file=sys.stderr)
            # Use first image name as title basis
            title = Path(images[0]).stem.replace("_", " ").title()
            if len(images) > 1:
                title = "Exam"  # Generic title for multiple images
            latex_content = build_latex_document(title, merged_content)
            
            tex_path = os.path.join(tmpdir, "output.tex")
            Path(tex_path).write_text(latex_content)
            
            # Compile to PDF
            print("Compiling LaTeX to PDF...", file=sys.stderr)
            pdf_path = compile_latex(tex_path, tmpdir)
            
            # Copy output
            if args.output:
                output_path = args.output
            else:
                # Use first image directory and name
                first_image = Path(images[0])
                output_path = str(first_image.parent / (first_image.stem + "_exam.pdf"))
            
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
        return
    
    # Standard PDF mode
    exam_pdf = str(Path(exam_pdf).resolve())
    
    # Print summary
    print(f"Exam PDF: {Path(exam_pdf).name}", file=sys.stderr)
    if solution_pdfs:
        print(f"Solution PDFs: {', '.join(Path(p).name for p in solution_pdfs)}", file=sys.stderr)
    if images:
        print(f"Solution images: {', '.join(Path(p).name for p in images)}", file=sys.stderr)
    if texts:
        print(f"Text files: {', '.join(Path(p).name for p in texts)}", file=sys.stderr)
    if codes:
        print(f"Code files: {', '.join(Path(p).name for p in codes)}", file=sys.stderr)
    print(f"Using model: {config.get('gemini_model_pro')}", file=sys.stderr)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Step 1: Convert exam PDF to images
        print("Converting exam PDF to images...", file=sys.stderr)
        exam_images = pdf_to_images(exam_pdf, tmpdir, prefix="exam")
        print(f"  Found {len(exam_images)} exam page(s)", file=sys.stderr)
        
        # Step 2: Collect solution images (including from PDFs)
        solution_images = list(images)  # Start with directly provided images
        
        for i, sol_pdf in enumerate(solution_pdfs):
            print(f"Converting solution PDF to images: {Path(sol_pdf).name}...", file=sys.stderr)
            pdf_images = pdf_to_images(sol_pdf, tmpdir, prefix=f"sol{i}")
            solution_images.extend(pdf_images)
            print(f"  Found {len(pdf_images)} page(s)", file=sys.stderr)
        
        # Step 3: Read text and code files
        text_content = read_text_files(texts)
        code_content = read_code_files(codes)
        
        # Step 4: Send to Gemini for merging
        print("Merging with Gemini AI...", file=sys.stderr)
        merged_content = merge_with_gemini(
            exam_images, solution_images, text_content, code_content, config
        )
        
        # Step 5: Create LaTeX document
        print("Creating LaTeX document...", file=sys.stderr)
        title = Path(exam_pdf).stem.replace("_", " ").title()
        latex_content = build_latex_document(title, merged_content)
        
        tex_path = os.path.join(tmpdir, "output.tex")
        Path(tex_path).write_text(latex_content)
        
        # Step 6: Compile to PDF
        print("Compiling LaTeX to PDF...", file=sys.stderr)
        pdf_path = compile_latex(tex_path, tmpdir)
        
        # Step 7: Copy output
        if args.output:
            output_path = args.output
        else:
            output_path = str(Path(exam_pdf).with_stem(Path(exam_pdf).stem + "_solved").with_suffix(".pdf"))
        
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
