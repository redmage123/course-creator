#!/usr/bin/env python3
"""
Analyze JavaScript files for undocumented functions.
Identifies functions that lack JSDoc comments.
"""

import re
import sys
from pathlib import Path

def find_undocumented_functions(file_path):
    """
    Find functions without JSDoc documentation.

    Args:
        file_path: Path to JavaScript file

    Returns:
        List of tuples (line_number, function_name, function_type)
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')

    undocumented = []

    # Patterns for different function types
    patterns = [
        (r'^(\s*)(?:async\s+)?function\s+(\w+)\s*\(', 'function'),
        (r'^(\s*)(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?function\s*\(', 'function_expression'),
        (r'^(\s*)(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>', 'arrow_function'),
        (r'^(\s*)(\w+)\s*:\s*(?:async\s+)?function\s*\(', 'method'),
        (r'^(\s*)(?:async\s+)?(\w+)\s*\([^)]*\)\s*\{', 'method_shorthand'),
    ]

    i = 0
    while i < len(lines):
        line = lines[i]

        # Check if previous line has JSDoc
        has_jsdoc = False
        if i > 0:
            prev_lines = []
            j = i - 1
            # Look back up to 20 lines for JSDoc
            while j >= 0 and j >= i - 20:
                prev_lines.insert(0, lines[j])
                j -= 1

            # Check if there's a JSDoc comment ending just before this line
            combined = '\n'.join(prev_lines)
            if re.search(r'/\*\*[\s\S]*?\*/', combined):
                # Find the last JSDoc comment
                jsdoc_matches = list(re.finditer(r'/\*\*[\s\S]*?\*/', combined))
                if jsdoc_matches:
                    last_jsdoc = jsdoc_matches[-1]
                    # Check if JSDoc is immediately before function (allowing whitespace/comments)
                    after_jsdoc = combined[last_jsdoc.end():]
                    if re.match(r'^[\s\n/]*$', after_jsdoc):
                        has_jsdoc = True

        if not has_jsdoc:
            for pattern, func_type in patterns:
                match = re.match(pattern, line)
                if match:
                    func_name = match.group(2)
                    # Skip some common patterns
                    if func_name not in ['constructor', 'catch', 'then', 'finally']:
                        undocumented.append((i + 1, func_name, func_type))
                    break

        i += 1

    return undocumented

def main():
    """Main analysis function."""
    if len(sys.argv) < 2:
        print("Usage: python3 analyze_js_docs.py <directory>")
        sys.exit(1)

    directory = Path(sys.argv[1])

    if not directory.exists():
        print(f"Directory not found: {directory}")
        sys.exit(1)

    # Find all JavaScript files
    js_files = sorted(directory.glob('*.js'))

    total_undocumented = 0
    results = []

    for js_file in js_files:
        undocumented = find_undocumented_functions(js_file)
        if undocumented:
            total_undocumented += len(undocumented)
            results.append((js_file.name, undocumented))

    # Print results
    print(f"\n{'='*80}")
    print(f"JavaScript Documentation Analysis")
    print(f"{'='*80}\n")

    print(f"Total files analyzed: {len(js_files)}")
    print(f"Files with undocumented functions: {len(results)}")
    print(f"Total undocumented functions: {total_undocumented}\n")

    print(f"{'='*80}")
    print("Files Needing Documentation:")
    print(f"{'='*80}\n")

    for filename, functions in results:
        print(f"\n{filename}: {len(functions)} undocumented functions")
        print("-" * 80)
        for line_num, func_name, func_type in functions[:10]:  # Show first 10
            print(f"  Line {line_num:4d}: {func_name:30s} ({func_type})")
        if len(functions) > 10:
            print(f"  ... and {len(functions) - 10} more")

if __name__ == '__main__':
    main()
