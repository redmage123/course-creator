#!/usr/bin/env python3
"""
Script to clean up duplicate JSDoc comments created by multiple script runs.
Removes duplicate /** ... */ blocks that appear consecutively.
"""

import os
import re
from pathlib import Path

def clean_duplicate_jsdoc(content: str) -> tuple[str, int]:
    """
    Remove duplicate JSDoc comments that appear consecutively.

    Args:
        content: File content with potential duplicate comments

    Returns:
        Tuple of (cleaned content, number of duplicates removed)
    """
    lines = content.split('\n')
    cleaned_lines = []
    duplicates_removed = 0
    i = 0

    while i < len(lines):
        line = lines[i]

        # Check if this line starts a JSDoc comment
        if '/**' in line:
            # Collect this complete JSDoc block
            jsdoc_block = [line]
            i += 1

            # Read until we hit the closing */
            while i < len(lines) and '*/' not in lines[i - 1]:
                jsdoc_block.append(lines[i])
                i += 1

            # Now check if the next non-empty line starts another JSDoc
            j = i
            while j < len(lines) and lines[j].strip() == '':
                j += 1

            # Skip duplicate JSDoc blocks
            while j < len(lines) and '/**' in lines[j]:
                # This is a duplicate, skip it
                duplicates_removed += 1
                j += 1

                # Skip to end of duplicate block
                while j < len(lines) and '*/' not in lines[j - 1]:
                    j += 1

                # Skip empty lines after duplicate
                while j < len(lines) and lines[j].strip() == '':
                    j += 1

            # Add the first (kept) JSDoc block
            cleaned_lines.extend(jsdoc_block)

            # Continue from where we left off
            i = j
        else:
            cleaned_lines.append(line)
            i += 1

    return '\n'.join(cleaned_lines), duplicates_removed

def process_file(filepath: Path) -> int:
    """
    Process a single JavaScript file to remove duplicate JSDoc.

    Args:
        filepath: Path to JavaScript file

    Returns:
        Number of duplicates removed
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        cleaned_content, duplicates_removed = clean_duplicate_jsdoc(content)

        if duplicates_removed > 0:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(cleaned_content)
            print(f"✅ {filepath}: Removed {duplicates_removed} duplicate JSDoc blocks")
            return duplicates_removed

        return 0
    except Exception as e:
        print(f"❌ Error processing {filepath}: {e}")
        return 0

def main():
    """Main execution function."""
    base_path = Path('/home/bbrelin/course-creator')

    directories = [
        base_path / 'frontend' / 'js' / 'modules',
        base_path / 'frontend' / 'js'
    ]

    total_duplicates = 0
    files_cleaned = 0

    for directory in directories:
        if not directory.exists():
            continue

        for js_file in directory.rglob('*.js'):
            count = process_file(js_file)
            if count > 0:
                total_duplicates += count
                files_cleaned += 1

    print(f"\n{'='*60}")
    print(f"✨ Cleanup Complete!")
    print(f"{'='*60}")
    print(f"Files Cleaned: {files_cleaned}")
    print(f"Total Duplicates Removed: {total_duplicates}")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()
