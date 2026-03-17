#!/bin/bash
# Build script for User Guide PDF generation
# Requires: d2, pandoc, texlive-latex-base

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Course Creator Platform - User Guide Builder ==="
echo ""

# Check for required tools
check_tool() {
    if ! command -v $1 &> /dev/null; then
        echo "Error: $1 is not installed"
        echo "Install with: $2"
        exit 1
    fi
}

# Add d2 to path if installed locally
export PATH=$HOME/.local/bin:$PATH

echo "Checking required tools..."
check_tool "d2" "curl -fsSL https://d2lang.com/install.sh | sh"
check_tool "pandoc" "apt install pandoc"

echo "✓ All tools available"
echo ""

# Generate SVG diagrams from D2 files
echo "Generating diagrams..."
mkdir -p images

for d2file in diagrams/*.d2; do
    filename=$(basename "$d2file" .d2)
    echo "  → $filename"
    d2 --theme=1 "$d2file" "images/${filename}.svg" 2>/dev/null || {
        echo "    Warning: Failed to generate $filename"
    }
done

echo "✓ Diagrams generated"
echo ""

# Generate PNG versions for PDF compatibility (if available)
if command -v rsvg-convert &> /dev/null; then
    echo "Converting SVGs to PNGs..."
    for svg in images/*.svg; do
        filename=$(basename "$svg" .svg)
        rsvg-convert -w 1200 "$svg" > "images/${filename}.png"
    done
    echo "✓ PNG conversion complete"
    echo ""
fi

# Generate PDF if pandoc and latex are available
if command -v pdflatex &> /dev/null; then
    echo "Generating PDF..."
    pandoc USER_GUIDE.md \
        -o USER_GUIDE.pdf \
        --pdf-engine=pdflatex \
        -V geometry:margin=1in \
        -V fontsize=11pt \
        --toc \
        --toc-depth=3 \
        --highlight-style=tango \
        -V colorlinks=true \
        -V linkcolor=blue \
        -V urlcolor=blue \
        --metadata title="Course Creator Platform - User Guide" \
        --metadata author="Course Creator Platform Team" \
        --metadata date="$(date +%Y-%m-%d)"

    echo "✓ PDF generated: USER_GUIDE.pdf"
else
    echo "Note: pdflatex not available. Skipping PDF generation."
    echo "      Install with: apt install texlive-latex-base texlive-fonts-recommended"
fi

# Generate HTML version
echo ""
echo "Generating HTML version..."
pandoc USER_GUIDE.md \
    -o USER_GUIDE.html \
    --standalone \
    --toc \
    --toc-depth=3 \
    --highlight-style=tango \
    --metadata title="Course Creator Platform - User Guide" \
    -c https://cdn.jsdelivr.net/npm/github-markdown-css/github-markdown.min.css \
    --template=- << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>$title$</title>
    <style>
        body {
            box-sizing: border-box;
            min-width: 200px;
            max-width: 980px;
            margin: 0 auto;
            padding: 45px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
        }
        img { max-width: 100%; height: auto; }
        table { border-collapse: collapse; width: 100%; margin: 1em 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f5f5f5; }
        code { background: #f5f5f5; padding: 2px 6px; border-radius: 3px; }
        pre { background: #f5f5f5; padding: 16px; overflow-x: auto; }
        h1, h2, h3 { border-bottom: 1px solid #eee; padding-bottom: 0.3em; }
        #TOC { background: #f9f9f9; padding: 20px; border-radius: 8px; margin-bottom: 2em; }
        #TOC ul { list-style: none; padding-left: 1em; }
        #TOC > ul { padding-left: 0; }
        @media print {
            body { max-width: 100%; padding: 20px; }
        }
    </style>
</head>
<body>
    <h1>$title$</h1>
    $if(toc)$
    <nav id="TOC">
        <h2>Table of Contents</h2>
        $toc$
    </nav>
    $endif$
    $body$
</body>
</html>
EOF

echo "✓ HTML generated: USER_GUIDE.html"
echo ""

echo "=== Build Complete ==="
echo ""
echo "Generated files:"
ls -la images/*.svg 2>/dev/null | awk '{print "  " $NF}'
[ -f USER_GUIDE.pdf ] && echo "  USER_GUIDE.pdf"
[ -f USER_GUIDE.html ] && echo "  USER_GUIDE.html"
echo ""
echo "Done!"
