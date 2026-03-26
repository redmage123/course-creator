#!/usr/bin/env python3
"""
Script to refactor HTML files: Remove "tami" references and update imports.

This script:
1. Removes tami-feature-flag.js import
2. Updates CSS imports to modern-ui
3. Changes data-tami-* attributes to data-*
4. Updates navigation structure
"""

import re
import os
from pathlib import Path

def update_css_imports(content):
    """Replace individual tami CSS imports with single modern-ui import."""
    # Remove old tami CSS imports
    patterns_to_remove = [
        r'<link rel="stylesheet" href="[^"]*tami/\d+-[^"]+\.css">',
        r'<link rel="stylesheet" href="[^"]*tami/tami-enhancements\.css">',
    ]

    for pattern in patterns_to_remove:
        content = re.sub(pattern, '', content)

    # Remove tami-feature-flag.js
    content = re.sub(r'<script src="[^"]*tami-feature-flag\.js"></script>', '', content)

    # Add modern-ui CSS import (if not already present)
    if 'modern-ui.css' not in content:
        # Find head tag and add import
        head_pattern = r'(<head>)'
        modern_ui_import = r'\1\n    <link rel="stylesheet" href="../css/modern-ui/modern-ui.css">'
        content = re.sub(head_pattern, modern_ui_import, content)

    return content

def update_data_attributes(content):
    """Change data-tami-* to data-*."""
    content = re.sub(r'data-tami-', 'data-', content)
    return content

def refactor_html_file(file_path):
    """Refactor a single HTML file."""
    print(f"Processing: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Apply transformations
    content = update_css_imports(content)
    content = update_data_attributes(content)

    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"  ✓ Completed: {file_path}")

def main():
    """Main refactoring process."""
    base_dir = Path('/home/bbrelin/course-creator')
    html_dir = base_dir / 'frontend/html'

    # Find all HTML files
    html_files = list(html_dir.glob('*.html'))

    print("=== HTML Refactoring: Removing 'Tami' References ===\n")

    for html_file in html_files:
        # Skip backup files
        if 'backup' in str(html_file).lower():
            print(f"Skipping backup: {html_file}")
            continue

        refactor_html_file(str(html_file))

    print("\n✓ HTML refactoring complete!")
    print(f"✓ Processed {len(html_files)} files")

if __name__ == '__main__':
    main()
