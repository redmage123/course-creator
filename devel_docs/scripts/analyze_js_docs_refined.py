#!/usr/bin/env python3
"""
Analyze JavaScript files for undocumented functions.
Identifies actual function declarations that lack JSDoc comments.
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
        List of tuples (line_number, function_name, function_signature)
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')

    undocumented = []

    # Patterns for different function types (excluding control flow)
    patterns = [
        # Regular function declarations
        (r'^(\s*)(?:async\s+)?function\s+(\w+)\s*\((.*?)\)', 'function'),
        # Function expressions
        (r'^(\s*)(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?function\s*\((.*?)\)', 'function_expression'),
        # Arrow functions
        (r'^(\s*)(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\((.*?)\)\s*=>', 'arrow_function'),
        # Object method shorthand (but not control flow keywords)
        (r'^(\s*)([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\((.*?)\)\s*\{', 'method_shorthand'),
        # Object method with function keyword
        (r'^(\s*)([a-zA-Z_$][a-zA-Z0-9_$]*)\s*:\s*(?:async\s+)?function\s*\((.*?)\)', 'method'),
    ]

    # Control flow keywords to exclude
    control_flow = {
        'if', 'else', 'for', 'while', 'do', 'switch', 'case', 'catch',
        'try', 'finally', 'with', 'return', 'break', 'continue', 'throw',
        'constructor', 'then'
    }

    i = 0
    while i < len(lines):
        line = lines[i]

        # Skip empty lines and comments
        stripped = line.strip()
        if not stripped or stripped.startswith('//') or stripped.startswith('/*') or stripped.startswith('*'):
            i += 1
            continue

        # Check if previous lines have JSDoc
        has_jsdoc = False
        if i > 0:
            # Look back for JSDoc comment
            j = i - 1
            found_jsdoc = False
            found_non_whitespace = False

            while j >= 0 and j >= i - 10:
                prev_line = lines[j].strip()

                # If we find JSDoc end, mark it
                if prev_line.endswith('*/'):
                    # Check if this is JSDoc (starts with /**)
                    k = j
                    while k >= 0:
                        check_line = lines[k].strip()
                        if check_line.startswith('/**'):
                            found_jsdoc = True
                            break
                        elif check_line.startswith('/*') and not check_line.startswith('/**'):
                            # Regular comment, not JSDoc
                            break
                        k -= 1
                    break
                elif prev_line and not prev_line.startswith('//'):
                    found_non_whitespace = True
                    break

                j -= 1

            has_jsdoc = found_jsdoc and not found_non_whitespace

        if not has_jsdoc:
            for pattern, func_type in patterns:
                match = re.match(pattern, line)
                if match:
                    func_name = match.group(2)
                    # Skip control flow keywords
                    if func_name.lower() not in control_flow:
                        params = match.group(3) if len(match.groups()) >= 3 else ''
                        signature = f"{func_name}({params})"
                        undocumented.append((i + 1, func_name, signature))
                    break

        i += 1

    return undocumented

def main():
    """Main analysis function."""
    if len(sys.argv) < 2:
        print("Usage: python3 analyze_js_docs_refined.py <directory>")
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
    print(f"JavaScript Documentation Analysis - Actual Functions Only")
    print(f"{'='*80}\n")

    print(f"Total files analyzed: {len(js_files)}")
    print(f"Files with undocumented functions: {len(results)}")
    print(f"Total undocumented functions: {total_undocumented}\n")

    print(f"{'='*80}")
    print("Files Needing Documentation (Top Priority):")
    print(f"{'='*80}\n")

    # Sort by number of undocumented functions
    results.sort(key=lambda x: len(x[1]), reverse=True)

    for filename, functions in results:
        print(f"\n{filename}: {len(functions)} undocumented functions")
        print("-" * 80)
        for line_num, func_name, signature in functions[:15]:  # Show first 15
            print(f"  Line {line_num:4d}: {signature}")
        if len(functions) > 15:
            print(f"  ... and {len(functions) - 15} more")

if __name__ == '__main__':
    main()
