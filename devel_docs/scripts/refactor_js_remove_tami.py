#!/usr/bin/env python3
"""
Script to refactor JavaScript files: Remove "tami" references.

This script:
1. Renames Tami* classes to generic names
2. Removes references to "Tami" in comments
3. Changes function/variable names from tami* to generic names
4. Updates module exports
"""

import re
import os
from pathlib import Path

def rename_classes_and_functions(content):
    """Rename Tami-prefixed classes and functions."""
    replacements = [
        # Classes
        (r'class TamiModal', 'class Modal'),
        (r'class TamiWizardProgress', 'class WizardProgress'),
        (r'class TamiWizardValidator', 'class WizardValidator'),
        (r'class TamiWizardDraft', 'class WizardDraft'),
        (r'class TamiNavigation', 'class Navigation'),
        (r'class TamiWizard', 'class Wizard'),

        # Function names
        (r'TamiModal\.', 'Modal.'),
        (r'new TamiModal', 'new Modal'),
        (r'new TamiWizardProgress', 'new WizardProgress'),
        (r'new TamiWizardValidator', 'new WizardValidator'),
        (r'new TamiWizardDraft', 'new WizardDraft'),
        (r'new TamiNavigation', 'new Navigation'),

        # Variables
        (r'tamiModal', 'modal'),
        (r'tamiWizard', 'wizard'),
        (r'tamiProgress', 'progress'),
        (r'tamiValidator', 'validator'),
        (r'tamiDraft', 'draft'),

        # Data attributes
        (r'data-tami-', 'data-'),

        # CSS classes
        (r'\'tami-', '\''),
        (r'"tami-', '"'),
        (r'\.tami-', '.'),

        # Event names
        (r'tami-modal:', 'modal:'),
        (r'tami-wizard:', 'wizard:'),
    ]

    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)

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

def refactor_js_file(input_path, output_path):
    """Refactor a single JavaScript file."""
    print(f"Processing: {input_path} -> {output_path}")

    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Apply transformations
    content = rename_classes_and_functions(content)
    content = remove_tami_references(content)

    # Write output
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"  ✓ Completed: {output_path}")

def main():
    """Main refactoring process."""
    base_dir = Path('/home/bbrelin/course-creator')

    # JavaScript file mappings
    js_files = [
        ('frontend/js/modules/tami-modal.js', 'frontend/js/modules/modal-system.js'),
        ('frontend/js/modules/tami-navigation.js', 'frontend/js/modules/navigation-system.js'),
        ('frontend/js/modules/tami-feedback.js', 'frontend/js/modules/feedback-system.js'),
        ('frontend/js/modules/tami-wizard-progress.js', 'frontend/js/modules/wizard-progress.js'),
        ('frontend/js/modules/tami-wizard-validation.js', 'frontend/js/modules/wizard-validation.js'),
        ('frontend/js/modules/tami-wizard-draft.js', 'frontend/js/modules/wizard-draft.js'),
    ]

    print("=== JavaScript Refactoring: Removing 'Tami' References ===\n")

    for input_file, output_file in js_files:
        input_path = base_dir / input_file
        output_path = base_dir / output_file

        if input_path.exists():
            refactor_js_file(str(input_path), str(output_path))
        else:
            print(f"  ✗ File not found: {input_path}")

    # Remove old tami-feature-flag.js (no longer needed)
    old_flag_file = base_dir / 'frontend/js/tami-feature-flag.js'
    if old_flag_file.exists():
        print(f"\nRemoving feature flag file: {old_flag_file}")
        os.remove(old_flag_file)
        print("  ✓ Removed")

    print("\n✓ JavaScript refactoring complete!")

if __name__ == '__main__':
    main()
