#!/bin/bash
# Extract all Python MetaTrader5 official documentation

set -e

OUTPUT_DIR="/tmp/mql5-python-comprehensive/official_docs"
EXTRACTOR="/tmp/mql5-tick-research/official_docs_extractor.py"
PYTHON="/Users/terryli/eon/mql5/.venv/bin/python"

mkdir -p "$OUTPUT_DIR"

echo "=== Extracting 32 Python MetaTrader5 Official Docs ==="
echo "Output: $OUTPUT_DIR"
echo ""

count=0
total=32

while IFS= read -r url; do
    count=$((count + 1))

    # Extract filename from URL
    filename=$(basename "$url")
    html_file="$OUTPUT_DIR/${filename}.html"
    md_file="$OUTPUT_DIR/${filename}.md"

    echo "[$count/$total] Extracting: $filename"
    echo "  URL: $url"

    # Download HTML (will be auto-deleted after extraction)
    curl -s "$url" > "$html_file"

    # Extract with URL (extractor auto-deletes HTML after conversion)
    $PYTHON "$EXTRACTOR" "$html_file" "$url" > /dev/null 2>&1

    # Check if markdown was created
    if [ -f "$md_file" ]; then
        word_count=$(wc -w < "$md_file")
        echo "  ✅ Success: $word_count words"
    else
        echo "  ❌ Failed: markdown not created"
    fi

    # Rate limiting
    sleep 1

done < /tmp/mql5-python-comprehensive/all_python_urls.txt

echo ""
echo "=== Extraction Complete ==="
echo "Total markdown files: $(ls -1 $OUTPUT_DIR/*.md 2>/dev/null | wc -l)"
echo "HTML files auto-deleted: ✅"
echo ""
echo "Location: $OUTPUT_DIR"
