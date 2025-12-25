#!/usr/bin/env python3
"""Fix Xournal PDF Background - Update .xoj/.xopp background PDF path and export.

Fixes the common issue when PDF backgrounds are moved/renamed.
Updates the background reference and exports to _notes.pdf.
"""

import argparse
import gzip
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def fix_xoj_background(xoj_path: str, pdf_path: str) -> str:
    """Fix the background PDF path in a .xoj file and return the updated content.
    
    .xoj files are gzipped XML with background references like:
    <background type="pdf" domain="absolute" filename="/old/path/to.pdf" pageno="1"/>
    """
    # Read and decompress
    with gzip.open(xoj_path, 'rb') as f:
        content = f.read().decode('utf-8')
    
    # Get absolute path to new PDF
    abs_pdf_path = os.path.abspath(pdf_path)
    
    # Update all background filename references
    # Pattern matches: filename="..." or filename='...'
    pattern = r'(<background[^>]*\sfilename=")[^"]*(")'
    replacement = rf'\g<1>{abs_pdf_path}\2'
    updated_content = re.sub(pattern, replacement, content)
    
    # Also handle single quotes
    pattern_sq = r"(<background[^>]*\sfilename=')[^']*(')"
    replacement_sq = rf"\g<1>{abs_pdf_path}\2"
    updated_content = re.sub(pattern_sq, replacement_sq, updated_content)
    
    return updated_content


def fix_xopp_background(xopp_path: str, pdf_path: str) -> str:
    """Fix the background PDF path in a .xopp file (Xournal++)."""
    # .xopp files are gzipped XML, similar to .xoj
    return fix_xoj_background(xopp_path, pdf_path)


def main():
    parser = argparse.ArgumentParser(
        description="Fix Xournal PDF background and export to PDF"
    )
    parser.add_argument("xoj_file", help=".xoj or .xopp file")
    parser.add_argument("pdf_file", help="PDF file to use as background")
    parser.add_argument("--output", "-o", help="Output PDF path (default: input_notes.pdf)")
    parser.add_argument("--save", "-s", action="store_true", 
                        help="Also save the fixed .xoj/.xopp file")
    args = parser.parse_args()
    
    xoj_path = Path(args.xoj_file)
    pdf_path = Path(args.pdf_file)
    
    # Validate inputs
    if not xoj_path.exists():
        print(f"Error: Xournal file not found: {xoj_path}", file=sys.stderr)
        sys.exit(1)
    if not pdf_path.exists():
        print(f"Error: PDF file not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)
    
    suffix = xoj_path.suffix.lower()
    if suffix not in ('.xoj', '.xopp'):
        print(f"Error: Expected .xoj or .xopp file, got: {suffix}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Xournal file: {xoj_path.name}", file=sys.stderr)
    print(f"PDF background: {pdf_path.name}", file=sys.stderr)
    
    # Fix the background reference
    print("Fixing background reference...", file=sys.stderr)
    if suffix == '.xoj':
        updated_content = fix_xoj_background(str(xoj_path), str(pdf_path))
    else:
        updated_content = fix_xopp_background(str(xoj_path), str(pdf_path))
    
    # Create a temporary file with the fixed content
    with tempfile.NamedTemporaryFile(mode='wb', suffix=suffix, delete=False) as tmp:
        tmp_path = tmp.name
        with gzip.open(tmp, 'wb') as gz:
            gz.write(updated_content.encode('utf-8'))
    
    try:
        # Determine output path
        if args.output:
            output_pdf = args.output
        else:
            output_pdf = str(xoj_path.with_stem(xoj_path.stem + "_notes").with_suffix(".pdf"))
        
        # Export to PDF using xournalpp
        print(f"Exporting to: {output_pdf}", file=sys.stderr)
        result = subprocess.run(
            ["xournalpp", "--create-pdf", output_pdf, tmp_path],
            capture_output=True, text=True
        )
        
        if result.returncode != 0:
            # Try with original xournal as fallback
            print("xournalpp failed, trying xournal...", file=sys.stderr)
            result = subprocess.run(
                ["xournal", tmp_path, "-p", output_pdf],
                capture_output=True, text=True
            )
        
        if result.returncode == 0 and Path(output_pdf).exists():
            print(f"✓ Exported: {output_pdf}", file=sys.stderr)
        else:
            print(f"✗ Export failed: {result.stderr}", file=sys.stderr)
            sys.exit(1)
        
        # Optionally save the fixed xoj/xopp file
        if args.save:
            shutil.copy(tmp_path, str(xoj_path))
            print(f"✓ Updated: {xoj_path}", file=sys.stderr)
    
    finally:
        # Clean up temp file
        os.unlink(tmp_path)


if __name__ == "__main__":
    main()
