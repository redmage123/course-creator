#!/usr/bin/env python3
"""
Apply Tami UI classes to org-admin-dashboard.html

This script adds form-input and form-label classes to form elements
that don't already have them.

Author: Course Creator Team
Date: 2025-10-17
"""

import re
import sys


def apply_tami_classes(content: str) -> tuple[str, dict]:
    """
    Apply Tami UI classes to HTML content

    Returns:
        tuple: (modified_content, statistics)
    """
    stats = {
        'inputs_updated': 0,
        'textareas_updated': 0,
        'selects_updated': 0,
        'labels_updated': 0,
    }

    # Track original content
    original_content = content

    # 1. Add form-input to text inputs that don't have it
    pattern = r'<input\s+([^>]*?)type=["\'](?:text|email|tel|url|number|date)["\']([^>]*?)>'
    def add_input_class(match):
        before = match.group(1)
        after = match.group(2)
        full_tag = before + after

        # Skip if already has form-input
        if 'form-input' in full_tag:
            return match.group(0)

        # Skip file inputs and hidden inputs
        if 'file-input' in full_tag or 'type="hidden"' in full_tag or 'hidden' in full_tag:
            return match.group(0)

        # Add or append class
        if 'class=' in full_tag:
            # Find and update class attribute
            tag = match.group(0)[:-1]  # Remove closing >
            tag = re.sub(r'class=["\']([^"\']*)["\']', r'class="\1 form-input"', tag)
            tag += '>'
        else:
            # Add new class attribute
            tag = f'<input {before}type="{match.group(0).split("type=")[1].split('"')[1]}"{after} class="form-input">'

        stats['inputs_updated'] += 1
        return tag

    # Apply to text inputs
    content = re.sub(pattern, add_input_class, content)

    # 2. Add form-input to textareas that don't have it
    pattern = r'<textarea\s+([^>]*?)>'
    def add_textarea_class(match):
        attrs = match.group(1)

        # Skip if already has form-input
        if 'form-input' in attrs:
            return match.group(0)

        if 'class=' in attrs:
            attrs = re.sub(r'class=["\']([^"\']*)["\']', r'class="\1 form-input"', attrs)
        else:
            attrs += ' class="form-input"'

        stats['textareas_updated'] += 1
        return f'<textarea {attrs}>'

    content = re.sub(pattern, add_textarea_class, content)

    # 3. Add form-select to select elements that don't have it
    pattern = r'<select\s+([^>]*?)>'
    def add_select_class(match):
        attrs = match.group(1)

        # Skip if already has form-select
        if 'form-select' in attrs:
            return match.group(0)

        if 'class=' in attrs:
            attrs = re.sub(r'class=["\']([^"\']*)["\']', r'class="\1 form-select"', attrs)
        else:
            attrs += ' class="form-select"'

        stats['selects_updated'] += 1
        return f'<select {attrs}>'

    content = re.sub(pattern, add_select_class, content)

    # 4. Add form-label to labels that don't have it (in form-group divs)
    pattern = r'<label\s+([^>]*?)>'
    def add_label_class(match):
        attrs = match.group(1)

        # Skip if already has form-label
        if 'form-label' in attrs:
            return match.group(0)

        if 'class=' in attrs:
            attrs = re.sub(r'class=["\']([^"\']*)["\']', r'class="form-label \1"', attrs)
        else:
            attrs += ' class="form-label"'

        stats['labels_updated'] += 1
        return f'<label {attrs}>'

    content = re.sub(pattern, add_label_class, content)

    return content, stats


def main():
    """Main function"""
    input_file = '/home/bbrelin/course-creator/frontend/html/org-admin-dashboard.html'

    # Read file
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    print(f"Processing {input_file}...")
    print(f"Original file size: {len(content)} bytes")

    # Apply Tami classes
    modified_content, stats = apply_tami_classes(content)

    # Write back
    with open(input_file, 'w', encoding='utf-8') as f:
        f.write(modified_content)

    print(f"Modified file size: {len(modified_content)} bytes")
    print("\nStatistics:")
    print(f"  - Text/Email/Tel/URL inputs updated: {stats['inputs_updated']}")
    print(f"  - Textareas updated: {stats['textareas_updated']}")
    print(f"  - Select dropdowns updated: {stats['selects_updated']}")
    print(f"  - Labels updated: {stats['labels_updated']}")
    print(f"\nTotal elements updated: {sum(stats.values())}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
