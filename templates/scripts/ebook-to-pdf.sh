#!/bin/bash
# Converts EPUB/MOBI to PDF using Calibre's ebook-convert
# Usage: ebook-to-pdf.sh file1.epub [file2.mobi ...]

for file in "$@"; do
    if [[ -f "$file" ]]; then
        output="${file%.*}.pdf"
        echo "Converting: $file → $output"
        ebook-convert "$file" "$output" \
            --paper-size a4 \
            --pdf-page-margin-left 72 \
            --pdf-page-margin-right 72 \
            --pdf-page-margin-top 72 \
            --pdf-page-margin-bottom 72
    fi
done
