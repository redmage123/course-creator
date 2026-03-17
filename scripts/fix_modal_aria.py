#!/usr/bin/env python3
"""
Fix Modal ARIA Roles Script
Adds proper ARIA attributes to modal dialog elements
"""

import re
from pathlib import Path

BASE_DIR = Path("/home/bbrelin/course-creator/frontend/html")

# Dashboard files that have modals
MODAL_FILES = [
    "student-dashboard.html",
    "instructor-dashboard.html",
    "org-admin-dashboard.html",
    "site-admin-dashboard.html",
    "project-dashboard.html"
]

def fix_modal_aria(content):
    """Add ARIA roles and labelledby to modal divs"""

    # Pattern: <div id="someModal" class="modal"
    # Need to add: role="dialog" aria-modal="true" aria-labelledby="modalTitleId"

    # Find all modal divs
    pattern = r'<div\s+id="([^"]+Modal)"([^>]*?)class="modal"([^>]*?)>'

    def replace_modal(match):
        modal_id = match.group(1)
        before_class = match.group(2)
        after_class = match.group(3)

        # Check if already has role="dialog"
        full_match = match.group(0)
        if 'role="dialog"' in full_match:
            return full_match

        # Construct the title ID (usually modalTitle or modal-title)
        title_id = f"{modal_id}Title"

        # Build the replacement
        replacement = f'<div id="{modal_id}"{before_class}class="modal"{after_class} role="dialog" aria-modal="true" aria-labelledby="{title_id}">'
        return replacement

    new_content = re.sub(pattern, replace_modal, content, flags=re.IGNORECASE)
    return new_content, (new_content != content)

def apply_modal_fixes(filepath):
    """Apply modal ARIA fixes to a file"""
    print(f"\nProcessing: {filepath.name}")

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content
    content, changed = fix_modal_aria(content)

    if changed:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✓ Added ARIA roles to modals")
        return 1
    else:
        print(f"  No changes needed")
        return 0

def main():
    """Main execution"""
    print("="*60)
    print("Modal ARIA Roles Fix")
    print("="*60)

    total_files_modified = 0

    for filename in MODAL_FILES:
        filepath = BASE_DIR / filename
        if filepath.exists():
            result = apply_modal_fixes(filepath)
            total_files_modified += result
        else:
            print(f"\n⚠ File not found: {filepath}")

    print("\n" + "="*60)
    print(f"Files modified: {total_files_modified}/{len(MODAL_FILES)}")
    print("="*60)

if __name__ == "__main__":
    main()
