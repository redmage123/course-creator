#!/usr/bin/env python3
"""
User Guide Builder Script

Generates HTML and PDF versions of the User Guide from Markdown.
Uses D2 for diagrams and WeasyPrint for PDF generation.
"""

import os
import subprocess
import markdown
from pathlib import Path

# Configuration
SCRIPT_DIR = Path(__file__).parent
GUIDE_MD = SCRIPT_DIR / "USER_GUIDE.md"
GUIDE_HTML = SCRIPT_DIR / "USER_GUIDE.html"
GUIDE_PDF = SCRIPT_DIR / "USER_GUIDE.pdf"
DIAGRAMS_DIR = SCRIPT_DIR / "diagrams"
IMAGES_DIR = SCRIPT_DIR / "images"

# HTML Template
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Course Creator Platform - User Guide</title>
    <style>
        :root {{
            --primary-color: #1976D2;
            --text-color: #333;
            --bg-color: #fff;
            --border-color: #e0e0e0;
            --code-bg: #f5f5f5;
        }}

        * {{
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: var(--text-color);
            max-width: 900px;
            margin: 0 auto;
            padding: 40px 20px;
            background: var(--bg-color);
        }}

        h1 {{
            color: var(--primary-color);
            border-bottom: 3px solid var(--primary-color);
            padding-bottom: 10px;
            margin-top: 40px;
        }}

        h2 {{
            color: #424242;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 8px;
            margin-top: 32px;
        }}

        h3 {{
            color: #616161;
            margin-top: 24px;
        }}

        h4 {{
            color: #757575;
        }}

        a {{
            color: var(--primary-color);
            text-decoration: none;
        }}

        a:hover {{
            text-decoration: underline;
        }}

        img {{
            max-width: 100%;
            height: auto;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            margin: 20px 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}

        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
            font-size: 14px;
        }}

        th, td {{
            border: 1px solid var(--border-color);
            padding: 10px 12px;
            text-align: left;
        }}

        th {{
            background: #f5f5f5;
            font-weight: 600;
        }}

        tr:nth-child(even) {{
            background: #fafafa;
        }}

        code {{
            background: var(--code-bg);
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Monaco', 'Consolas', 'Courier New', monospace;
            font-size: 0.9em;
        }}

        pre {{
            background: #263238;
            color: #fff;
            padding: 16px 20px;
            border-radius: 8px;
            overflow-x: auto;
            font-size: 13px;
            line-height: 1.5;
        }}

        pre code {{
            background: transparent;
            padding: 0;
            color: inherit;
        }}

        blockquote {{
            border-left: 4px solid var(--primary-color);
            margin: 20px 0;
            padding: 10px 20px;
            background: #E3F2FD;
            border-radius: 0 8px 8px 0;
        }}

        hr {{
            border: none;
            border-top: 2px solid var(--border-color);
            margin: 40px 0;
        }}

        ul, ol {{
            padding-left: 24px;
        }}

        li {{
            margin: 8px 0;
        }}

        .toc {{
            background: #f9f9f9;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 20px 30px;
            margin: 30px 0;
        }}

        .toc h2 {{
            margin-top: 0;
            font-size: 18px;
            border: none;
        }}

        .toc ul {{
            list-style: none;
            padding-left: 0;
        }}

        .toc li {{
            margin: 6px 0;
        }}

        .toc a {{
            color: #555;
        }}

        .page-break {{
            page-break-after: always;
        }}

        @media print {{
            body {{
                padding: 20px;
                max-width: 100%;
            }}

            img {{
                max-width: 100%;
                page-break-inside: avoid;
            }}

            h1, h2, h3 {{
                page-break-after: avoid;
            }}

            table {{
                page-break-inside: avoid;
            }}
        }}

        @page {{
            margin: 2cm;
            @bottom-center {{
                content: counter(page);
            }}
        }}
    </style>
</head>
<body>
    <header>
        <h1>Course Creator Platform</h1>
        <p style="font-size: 1.2em; color: #666;">Comprehensive User Guide</p>
        <p style="color: #999;">Version 3.3.1 | December 2025</p>
    </header>

    <main>
        {content}
    </main>

    <footer style="margin-top: 60px; padding-top: 20px; border-top: 1px solid #eee; color: #999; text-align: center;">
        <p>Course Creator Platform - User Guide</p>
        <p>Generated: {date}</p>
    </footer>
</body>
</html>
"""


def generate_diagrams():
    """Generate SVG diagrams from D2 files."""
    print("Generating diagrams...")
    IMAGES_DIR.mkdir(exist_ok=True)

    d2_path = os.path.expanduser("~/.local/bin/d2")
    if not os.path.exists(d2_path):
        d2_path = "d2"

    for d2_file in DIAGRAMS_DIR.glob("*.d2"):
        svg_file = IMAGES_DIR / f"{d2_file.stem}.svg"
        print(f"  → {d2_file.stem}")
        try:
            subprocess.run(
                [d2_path, "--theme=1", str(d2_file), str(svg_file)],
                check=True,
                capture_output=True
            )
        except subprocess.CalledProcessError as e:
            print(f"    Warning: Failed to generate {d2_file.stem}")
            print(f"    Error: {e.stderr.decode()}")

    print("✓ Diagrams generated")


def convert_markdown_to_html(md_content: str) -> str:
    """Convert Markdown to HTML with extensions."""
    extensions = [
        'markdown.extensions.tables',
        'markdown.extensions.fenced_code',
        'markdown.extensions.codehilite',
        'markdown.extensions.toc',
        'markdown.extensions.nl2br',
    ]

    md = markdown.Markdown(extensions=extensions)
    return md.convert(md_content)


def generate_html():
    """Generate HTML version of the guide."""
    print("\nGenerating HTML...")

    # Read markdown
    md_content = GUIDE_MD.read_text()

    # Convert to HTML
    html_content = convert_markdown_to_html(md_content)

    # Wrap in template
    from datetime import datetime
    full_html = HTML_TEMPLATE.format(
        content=html_content,
        date=datetime.now().strftime("%Y-%m-%d")
    )

    # Write HTML
    GUIDE_HTML.write_text(full_html)
    print(f"✓ HTML generated: {GUIDE_HTML}")


def generate_pdf():
    """Generate PDF from HTML using WeasyPrint."""
    print("\nGenerating PDF...")

    try:
        from weasyprint import HTML, CSS

        # Generate HTML first if not exists
        if not GUIDE_HTML.exists():
            generate_html()

        # Convert to PDF
        html = HTML(filename=str(GUIDE_HTML), base_url=str(SCRIPT_DIR))
        html.write_pdf(str(GUIDE_PDF))

        print(f"✓ PDF generated: {GUIDE_PDF}")
    except ImportError:
        print("  WeasyPrint not available. Install with: pip install weasyprint")
    except Exception as e:
        print(f"  Error generating PDF: {e}")


def main():
    """Main build function."""
    print("=" * 50)
    print("Course Creator Platform - User Guide Builder")
    print("=" * 50)
    print()

    os.chdir(SCRIPT_DIR)

    # Generate diagrams
    generate_diagrams()

    # Generate HTML
    generate_html()

    # Generate PDF
    generate_pdf()

    print("\n" + "=" * 50)
    print("Build Complete!")
    print("=" * 50)
    print("\nGenerated files:")

    for svg in IMAGES_DIR.glob("*.svg"):
        print(f"  {svg.relative_to(SCRIPT_DIR)}")

    if GUIDE_HTML.exists():
        print(f"  {GUIDE_HTML.name}")

    if GUIDE_PDF.exists():
        print(f"  {GUIDE_PDF.name}")

    print()


if __name__ == "__main__":
    main()
