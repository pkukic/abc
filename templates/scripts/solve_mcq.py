#!/usr/bin/env python3
"""Solve MCQ Exam - Solve multiple choice questions from a clean PDF exam.

Uses Gemini Pro to:
1. Read the exam PDF (clean LaTeX-generated)
2. Carefully analyze each question and options
3. Provide detailed reasoning for each answer
4. Output a solved exam with explanations

Usage: solve_mcq.py exam.pdf
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


def solve_exam(images: list, config: dict) -> str:
    """Send exam images to Gemini for solving with detailed reasoning."""
    print(f"  Analyzing {len(images)} page(s)...", file=sys.stderr)
    
    prompt = load_prompt("solve_mcq")
    
    result = call_gemini(
        prompt,
        config,
        model=config.get("gemini_model_pro"),  # Use Pro for careful reasoning
        image_paths=images,
    )
    
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Solve MCQ Exam - Solve multiple choice questions with reasoning"
    )
    parser.add_argument("files", nargs="+", help="PDF exam file(s) to solve")
    parser.add_argument("--keep-tex", action="store_true", help="Keep the .tex file")
    args = parser.parse_args()
    
    config = get_config()
    print(f"Using model: {config.get('gemini_model_pro')}", file=sys.stderr)
    
    for exam_file in args.files:
        # Resolve to absolute path to ensure output goes to correct directory
        exam_file = str(Path(exam_file).resolve())
        
        print(f"\n{'='*50}", file=sys.stderr)
        print(f"Processing: {Path(exam_file).name}", file=sys.stderr)
        print(f"{'='*50}", file=sys.stderr)
        
        # Check file exists
        if not Path(exam_file).exists():
            print(f"Error: File not found: {exam_file}", file=sys.stderr)
            continue
        
        if not exam_file.lower().endswith('.pdf'):
            print(f"Error: Expected PDF file, got: {exam_file}", file=sys.stderr)
            continue
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Step 1: Convert PDF to images
            print("Converting exam PDF to images...", file=sys.stderr)
            images = pdf_to_images(exam_file, tmpdir, prefix="exam")
            print(f"  Found {len(images)} page(s)", file=sys.stderr)
            
            # Step 2: Send to Gemini for solving
            print("Solving with Gemini Pro...", file=sys.stderr)
            solved_content = solve_exam(images, config)
            
            # Step 3: Create LaTeX document
            print("Creating LaTeX document...", file=sys.stderr)
            title = Path(exam_file).stem.replace("_", " ").title() + " - Riješeno"
            latex_content = build_latex_document(title, solved_content)
            
            tex_path = os.path.join(tmpdir, "output.tex")
            Path(tex_path).write_text(latex_content)
            
            # Step 4: Compile to PDF
            print("Compiling LaTeX to PDF...", file=sys.stderr)
            pdf_path = compile_latex(tex_path, tmpdir)
            
            # Step 5: Copy output
            output_path = str(Path(exam_file).with_stem(Path(exam_file).stem + "_solved").with_suffix(".pdf"))
            
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
    
    print(f"\n✅ Processed {len(args.files)} file(s)", file=sys.stderr)


if __name__ == "__main__":
    main()
