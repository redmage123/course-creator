#!/usr/bin/env python3
"""
Add focus-manager.js to all HTML files

This script automatically adds the focus-manager.js script tag to all HTML files
in the frontend/html directory that don't already have it.

Purpose:
- Ensures consistent focus management across all pages
- Implements WCAG 2.4.7 Level AA: Focus Visible requirement
- Adds script before closing </body> tag

Business Context:
This is part of Phase 2 accessibility improvements to make keyboard focus
clearly visible for users with motor disabilities or keyboard-only navigation.
"""

import os
import re
from pathlib import Path

# Configuration
HTML_DIR = Path(__file__).parent.parent / "frontend" / "html"
FOCUS_MANAGER_SCRIPT = '    <script src="../js/focus-manager.js"></script>\n'

def add_focus_manager_to_file(file_path):
    """
    Add focus-manager.js script to HTML file if not already present

    Args:
        file_path: Path to HTML file

    Returns:
        bool: True if file was modified, False if already had script
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if focus-manager.js is already included
    if 'focus-manager.js' in content:
        print(f"✓ {file_path.name} - Already has focus-manager.js")
        return False

    # Find the closing </body> tag
    body_close_pattern = r'</body>'
    if not re.search(body_close_pattern, content):
        print(f"⚠️ {file_path.name} - No </body> tag found, skipping")
        return False

    # Add script before </body>
    modified_content = re.sub(
        r'(\s*</body>)',
        f'\n{FOCUS_MANAGER_SCRIPT}\\1',
        content
    )

    # Write back to file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(modified_content)

    print(f"✅ {file_path.name} - Added focus-manager.js")
    return True

def main():
    """Process all HTML files in the directory"""
    print("=" * 80)
    print("Adding focus-manager.js to all HTML files")
    print("=" * 80)
    print()

    html_files = sorted(HTML_DIR.glob("*.html"))

    if not html_files:
        print(f"❌ No HTML files found in {HTML_DIR}")
        return

    modified_count = 0
    skipped_count = 0

    for html_file in html_files:
        if add_focus_manager_to_file(html_file):
            modified_count += 1
        else:
            skipped_count += 1

    print()
    print("=" * 80)
    print("Summary:")
    print(f"  Total files: {len(html_files)}")
    print(f"  Modified: {modified_count}")
    print(f"  Skipped: {skipped_count}")
    print("=" * 80)

if __name__ == "__main__":
    main()
