#!/usr/bin/env python3
"""
Script to analyze JavaScript files and identify undocumented functions.
Generates a comprehensive report of all functions needing JSDoc comments.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Tuple

def extract_functions(content: str, filepath: str) -> List[Dict]:
    """
    Extract all function declarations from JavaScript content.

    Args:
        content: JavaScript file content
        filepath: Path to the file for reporting

    Returns:
        List of dictionaries containing function information
    """
    functions = []
    lines = content.split('\n')

    # Patterns to match various function declarations
    patterns = [
        # Regular function declarations: function name() {}
        (r'^\s*function\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\([^)]*\)', 'function'),
        # Arrow functions assigned to const/let/var: const name = () => {}
        (r'^\s*(?:const|let|var)\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>', 'arrow'),
        # Method definitions in objects/classes: methodName() {}
        (r'^\s*(?:async\s+)?([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\([^)]*\)\s*\{', 'method'),
        # Arrow functions in object properties: name: () => {}
        (r'^\s*([a-zA-Z_$][a-zA-Z0-9_$]*)\s*:\s*(?:async\s*)?\([^)]*\)\s*=>', 'arrow_method'),
    ]

    for line_num, line in enumerate(lines, 1):
        # Check if line is already documented (has /** above it)
        is_documented = False
        if line_num > 1:
            # Check previous 3 lines for JSDoc comment
            for i in range(max(0, line_num - 4), line_num - 1):
                if i < len(lines) and '/**' in lines[i]:
                    is_documented = True
                    break

        # Try each pattern
        for pattern, func_type in patterns:
            match = re.match(pattern, line)
            if match:
                func_name = match.group(1)

                # Skip common non-function patterns
                if func_name in ['if', 'for', 'while', 'switch', 'catch']:
                    continue

                # Skip already documented functions
                if is_documented:
                    continue

                functions.append({
                    'name': func_name,
                    'line': line_num,
                    'type': func_type,
                    'code': line.strip(),
                    'file': filepath
                })
                break

    return functions

def analyze_directory(base_path: str, patterns: List[str]) -> Dict:
    """
    Analyze all JavaScript files in specified directories.

    Args:
        base_path: Base directory path
        patterns: List of glob patterns to match

    Returns:
        Dictionary with analysis results
    """
    all_functions = []
    file_count = 0

    for pattern in patterns:
        full_pattern = os.path.join(base_path, pattern)
        for filepath in Path(base_path).glob(pattern.replace(base_path + '/', '')):
            if filepath.is_file() and filepath.suffix == '.js':
                file_count += 1
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        functions = extract_functions(content, str(filepath))
                        all_functions.extend(functions)
                except Exception as e:
                    print(f"Error reading {filepath}: {e}")

    # Group by file
    by_file = {}
    for func in all_functions:
        if func['file'] not in by_file:
            by_file[func['file']] = []
        by_file[func['file']].append(func)

    return {
        'functions': all_functions,
        'by_file': by_file,
        'file_count': file_count,
        'function_count': len(all_functions)
    }

def generate_report(results: Dict) -> str:
    """
    Generate a comprehensive markdown report.

    Args:
        results: Analysis results dictionary

    Returns:
        Markdown formatted report
    """
    report = []
    report.append("# JavaScript Function Documentation Analysis Report")
    report.append("")
    report.append("## Summary")
    report.append(f"- **Total Files Analyzed**: {results['file_count']}")
    report.append(f"- **Total Undocumented Functions**: {results['function_count']}")
    report.append("")

    report.append("## Files Requiring Documentation")
    report.append("")

    # Sort by number of undocumented functions (descending)
    sorted_files = sorted(results['by_file'].items(),
                         key=lambda x: len(x[1]), reverse=True)

    for filepath, functions in sorted_files:
        rel_path = filepath.replace('/home/bbrelin/course-creator/', '')
        report.append(f"### {rel_path}")
        report.append(f"**Undocumented Functions**: {len(functions)}")
        report.append("")

        for func in functions:
            report.append(f"- **Line {func['line']}**: `{func['name']}()` ({func['type']})")
            report.append(f"  ```javascript")
            report.append(f"  {func['code']}")
            report.append(f"  ```")
        report.append("")

    return '\n'.join(report)

if __name__ == '__main__':
    base_path = '/home/bbrelin/course-creator'

    patterns = [
        'frontend/js/modules/**/*.js',
        'frontend/js/*.js'
    ]

    print("Analyzing JavaScript files...")
    results = analyze_directory(base_path, patterns)

    print(f"\nAnalysis Complete:")
    print(f"  Files Analyzed: {results['file_count']}")
    print(f"  Undocumented Functions Found: {results['function_count']}")

    # Generate report
    report = generate_report(results)

    # Save report
    report_path = os.path.join(base_path, 'JAVASCRIPT_DOCUMENTATION_ANALYSIS.md')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\nReport saved to: {report_path}")
