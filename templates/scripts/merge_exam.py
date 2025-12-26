#!/usr/bin/env python3
"""Merge Exam - Combine answers PDF with solutions (text or PDF) into clean LaTeX.

Uses Gemini AI to:
1. Extract questions from an answers/exam PDF
2. Parse solutions from a text file OR handwritten PDF
3. Merge into a formatted LaTeX document
4. Compile to clean PDF

Usage: merge_exam.py exam.pdf solutions.pdf
       merge_exam.py exam.pdf solutions.txt
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


# Text file extensions we accept for solutions
TEXT_EXTENSIONS = {'.txt', '.md', '.text', '.sol', '.ans', '.solution'}


def is_text_file(path: str) -> bool:
    """Check if a file is a text file based on extension."""
    return Path(path).suffix.lower() in TEXT_EXTENSIONS


def is_pdf(path: str) -> bool:
    """Check if a file is a PDF."""
    return Path(path).suffix.lower() == '.pdf'


def merge_with_gemini_text(exam_images: list, solutions_text: str, config: dict) -> str:
    """Send exam images and text solutions to Gemini for merging."""
    print(f"  Processing {len(exam_images)} exam page(s) with text solutions...", file=sys.stderr)
    
    # Load prompt and inject solutions
    prompt_template = load_prompt("merge_exam")
    prompt = prompt_template.replace("{{SOLUTIONS_TEXT}}", solutions_text)
    
    result = call_gemini(
        prompt,
        config,
        model=config.get("gemini_model_pro"),
        image_paths=exam_images,
    )
    
    return result


def merge_with_gemini_images(exam_images: list, solution_images: list, config: dict) -> str:
    """Send exam images and solution images to Gemini for merging."""
    print(f"  Processing {len(exam_images)} exam page(s) + {len(solution_images)} solution page(s)...", file=sys.stderr)
    
    # Load the image-based prompt
    prompt = load_prompt("merge_exam_images")
    
    # Combine all images: exam pages first, then solution pages
    all_images = exam_images + solution_images
    
    result = call_gemini(
        prompt,
        config,
        model=config.get("gemini_model_pro"),
        image_paths=all_images,
    )
    
    return result


def identify_files(files: list) -> tuple:
    """Identify which file is the exam and which is the solutions.
    
    Returns: (exam_pdf, solutions_file, solutions_is_pdf)
    """
    pdfs = []
    text_files = []
    
    for f in files:
        if not Path(f).exists():
            print(f"Error: File not found: {f}", file=sys.stderr)
            sys.exit(1)
        
        if is_pdf(f):
            pdfs.append(f)
        elif is_text_file(f):
            text_files.append(f)
        else:
            # Try to detect by content
            try:
                with open(f, 'r', encoding='utf-8') as fh:
                    fh.read(100)
                text_files.append(f)
            except:
                print(f"Error: Cannot identify file type: {f}", file=sys.stderr)
                sys.exit(1)
    
    # Case 1: One PDF + one text file
    if len(pdfs) == 1 and len(text_files) == 1:
        return pdfs[0], text_files[0], False
    
    # Case 2: Two PDFs - need to identify which is exam vs solutions
    if len(pdfs) == 2:
        # Heuristic: the file with "sol", "rje", "answer", "solution" in name is solutions
        solution_keywords = ['sol', 'rje', 'answer', 'solution', 'odg']
        
        for pdf in pdfs:
            name_lower = Path(pdf).stem.lower()
            if any(kw in name_lower for kw in solution_keywords):
                solutions_pdf = pdf
                exam_pdf = [p for p in pdfs if p != pdf][0]
                return exam_pdf, solutions_pdf, True
        
        # If no clear match, assume first (alphabetically) is exam, second is solutions
        sorted_pdfs = sorted(pdfs)
        print(f"  Note: Assuming '{Path(sorted_pdfs[0]).name}' is the exam", file=sys.stderr)
        print(f"        and '{Path(sorted_pdfs[1]).name}' is the solutions", file=sys.stderr)
        return sorted_pdfs[0], sorted_pdfs[1], True
    
    # Invalid combination
    if len(pdfs) == 0:
        print("Error: No PDF file provided. Need at least one exam PDF.", file=sys.stderr)
    elif len(pdfs) > 2:
        print("Error: Too many PDFs. Provide exactly one exam PDF and one solutions file.", file=sys.stderr)
    else:
        print("Error: Invalid file combination. Need one exam PDF and one solutions file (text or PDF).", file=sys.stderr)
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Merge Exam - Combine answers PDF with solutions (text or PDF)"
    )
    parser.add_argument("files", nargs=2, help="Exam PDF + solutions file (text or PDF, any order)")
    parser.add_argument("--output", "-o", help="Output PDF path (default: input_solved.pdf)")
    parser.add_argument("--keep-tex", action="store_true", help="Keep the .tex file")
    args = parser.parse_args()
    
    # Identify files
    exam_pdf, solutions_file, solutions_is_pdf = identify_files(args.files)
    
    config = get_config()
    
    print(f"Exam PDF: {Path(exam_pdf).name}", file=sys.stderr)
    print(f"Solutions: {Path(solutions_file).name} ({'PDF' if solutions_is_pdf else 'text'})", file=sys.stderr)
    print(f"Using model: {config.get('gemini_model_pro')}", file=sys.stderr)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Step 1: Convert exam PDF to images
        print("Converting exam PDF to images...", file=sys.stderr)
        exam_images = pdf_to_images(exam_pdf, tmpdir, prefix="exam")
        print(f"  Found {len(exam_images)} exam page(s)", file=sys.stderr)
        
        # Step 2: Process solutions (text or PDF)
        if solutions_is_pdf:
            print("Converting solutions PDF to images...", file=sys.stderr)
            solution_images = pdf_to_images(solutions_file, tmpdir, prefix="sol")
            print(f"  Found {len(solution_images)} solution page(s)", file=sys.stderr)
            
            # Merge using image-based approach
            print("Merging with Gemini AI...", file=sys.stderr)
            merged_content = merge_with_gemini_images(exam_images, solution_images, config)
        else:
            # Read solutions text
            solutions_text = Path(solutions_file).read_text(encoding='utf-8')
            print(f"  Solutions: {len(solutions_text)} characters", file=sys.stderr)
            
            # Merge using text-based approach
            print("Merging with Gemini AI...", file=sys.stderr)
            merged_content = merge_with_gemini_text(exam_images, solutions_text, config)
        
        # Step 3: Create LaTeX document
        print("Creating LaTeX document...", file=sys.stderr)
        title = Path(exam_pdf).stem.replace("_", " ").title()
        latex_content = build_latex_document(title, merged_content)
        
        tex_path = os.path.join(tmpdir, "output.tex")
        Path(tex_path).write_text(latex_content)
        
        # Step 4: Compile to PDF
        print("Compiling LaTeX to PDF...", file=sys.stderr)
        pdf_path = compile_latex(tex_path, tmpdir)
        
        # Step 5: Copy output
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
