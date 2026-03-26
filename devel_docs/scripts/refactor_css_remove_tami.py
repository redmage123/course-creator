#!/usr/bin/env python3
"""
Script to refactor CSS files: Remove "tami" references and feature flag scoping.

This script:
1. Removes [data-tami-ui="enabled"] selectors
2. Changes --tami-* variables to --ui-*
3. Removes references to "Tami" in comments
4. Applies styles directly (no toggle)
"""

import re
import os
from pathlib import Path

def remove_feature_flag_scoping(content):
    """Remove [data-tami-ui="enabled"] scoping from selectors."""
    # Pattern: [data-tami-ui="enabled"] selector { ... }
    # Replace with: selector { ... }

    # Handle various formats
    patterns = [
        (r'\[data-tami-ui="enabled"\]\s+', ''),  # [data-tami-ui="enabled"] .class
        (r'\[data-tami-ui=\'enabled\'\]\s+', ''),  # [data-tami-ui='enabled'] .class
        (r',\s*\[data-tami-ui="enabled"\]', ''),   # Multiple selectors
    ]

    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)

    return content

def rename_variables(content):
    """Change --tami-* variables to --ui-*."""
    # Replace --tami- with --ui-
    content = re.sub(r'--tami-', '--ui-', content)
    return content

def remove_tami_references(content):
    """Remove or replace 'Tami' references in comments."""
    replacements = [
        (r'Tami-Inspired', 'Modern'),
        (r'Tami\'s', 'Our'),
        (r'Tami', 'the design system'),
        (r'TAMI', 'UI'),
    ]

    for old, new in replacements:
        content = re.sub(old, new, content, flags=re.IGNORECASE)

    return content

def remove_tami_classnames(content):
    """Remove .tami- class names, replace with generic names."""
    patterns = [
        (r'\.tami-modal', '.modal'),
        (r'\.tami-spinner', '.spinner'),
        (r'\.tami-toast', '.toast'),
        (r'\.tami-progress', '.progress'),
        (r'\.tami-card', '.card'),
        (r'\.tami-btn', '.btn'),
        (r'data-tami-', 'data-'),
    ]

    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)

    return content

def refactor_css_file(input_path, output_path):
    """Refactor a single CSS file."""
    print(f"Processing: {input_path} -> {output_path}")

    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Apply transformations
    content = remove_feature_flag_scoping(content)
    content = rename_variables(content)
    content = remove_tami_references(content)
    content = remove_tami_classnames(content)

    # Write output
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"  ✓ Completed: {output_path}")

def main():
    """Main refactoring process."""
    base_dir = Path('/home/bbrelin/course-creator')

    # CSS file mappings
    css_files = [
        ('frontend/css/tami/01-typography.css', 'frontend/css/modern-ui/typography.css'),
        ('frontend/css/tami/02-buttons.css', 'frontend/css/modern-ui/buttons.css'),
        ('frontend/css/tami/03-forms.css', 'frontend/css/modern-ui/forms.css'),
        ('frontend/css/tami/04-cards.css', 'frontend/css/modern-ui/cards.css'),
        ('frontend/css/tami/05-modals.css', 'frontend/css/modern-ui/modals.css'),
        ('frontend/css/tami/06-navigation.css', 'frontend/css/modern-ui/navigation.css'),
        ('frontend/css/tami/07-loading-feedback.css', 'frontend/css/modern-ui/loading-states.css'),
    ]

    print("=== CSS Refactoring: Removing 'Tami' References ===\n")

    for input_file, output_file in css_files:
        input_path = base_dir / input_file
        output_path = base_dir / output_file

        if input_path.exists():
            refactor_css_file(str(input_path), str(output_path))
        else:
            print(f"  ✗ File not found: {input_path}")

    print("\n✓ CSS refactoring complete!")
    print(f"✓ Output directory: {base_dir / 'frontend/css/modern-ui'}")

if __name__ == '__main__':
    main()
