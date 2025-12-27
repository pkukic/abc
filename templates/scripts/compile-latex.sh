#!/bin/bash
# Compile LaTeX - Compile main.tex in selected directories
# Usage: compile-latex.sh dir1 [dir2 ...]

echo "=== Compile LaTeX ==="
echo ""

success=0
failed=0

for dir in "$@"; do
    # Resolve to absolute path
    dir="$(realpath "$dir")"
    
    if [[ ! -d "$dir" ]]; then
        echo "[Skip] Not a directory: $dir"
        ((failed++))
        continue
    fi
    
    tex_file="$dir/main.tex"
    if [[ ! -f "$tex_file" ]]; then
        echo "[Skip] No main.tex in: $dir"
        ((failed++))
        continue
    fi
    
    echo "[Compiling] $dir"
    
    # Run pdflatex twice to resolve references (from within the directory for images)
    cd "$dir"
    if pdflatex -interaction=nonstopmode -halt-on-error main.tex > /dev/null 2>&1; then
        # Second pass for references/TOC
        pdflatex -interaction=nonstopmode -halt-on-error main.tex > /dev/null 2>&1
        
        if [[ -f "$dir/main.pdf" ]]; then
            echo "  ✓ Created: main.pdf"
            ((success++))
        else
            echo "  ✗ PDF not created"
            ((failed++))
        fi
    else
        echo "  ✗ Compilation failed"
        # Show last few lines of log for debugging
        if [[ -f "$dir/main.log" ]]; then
            echo "  Last error from main.log:"
            grep -A2 "^!" "$dir/main.log" 2>/dev/null | head -6 | sed 's/^/    /'
        fi
        ((failed++))
    fi
    
    # Clean up auxiliary files
    rm -f "$dir/main.aux" "$dir/main.log" "$dir/main.out" "$dir/main.toc" 2>/dev/null
    
    echo ""
done

echo "----------------------------------------"
echo "✅ Complete! Success: $success, Failed: $failed"
