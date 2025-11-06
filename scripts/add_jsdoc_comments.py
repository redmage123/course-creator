#!/usr/bin/env python3
"""
Script to automatically add JSDoc comments to undocumented JavaScript functions.
Generates comprehensive JSDoc blocks based on function signatures and context.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Tuple

def has_jsdoc_comment(lines: List[str], line_num: int) -> bool:
    """
    Check if a function has a JSDoc comment above it.

    Args:
        lines: List of file lines
        line_num: Line number of the function (0-indexed)

    Returns:
        True if JSDoc comment exists, False otherwise
    """
    # Check previous 5 lines for /** comment start
    for i in range(max(0, line_num - 5), line_num):
        if '/**' in lines[i]:
            return True
    return False

def extract_params_from_signature(signature: str) -> List[str]:
    """Extract parameter names from function signature."""
    # Extract content between parentheses
    match = re.search(r'\(([^)]*)\)', signature)
    if not match:
        return []

    params_str = match.group(1)
    if not params_str.strip():
        return []

    # Split by comma and clean up
    params = [p.strip().split('=')[0].strip() for p in params_str.split(',')]
    return [p for p in params if p and p != '...']

def generate_jsdoc(func_name: str, signature: str, func_type: str) -> str:
    """
    Generate JSDoc comment for a function.

    Args:
        func_name: Function name
        signature: Full function signature line
        func_type: Type of function (function, arrow, method, etc.)

    Returns:
        JSDoc comment string
    """
    params = extract_params_from_signature(signature)

    # Determine what the function does based on name
    purpose = generate_purpose_from_name(func_name)
    why = generate_why_from_name(func_name)

    lines = ['    /**']
    lines.append(f'     * {purpose.upper()}')
    lines.append(f'     * PURPOSE: {purpose}')
    lines.append(f'     * WHY: {why}')

    if params:
        lines.append('     *')
        for param in params:
            param_desc = generate_param_description(param, func_name)
            lines.append(f'     * @param {{{get_param_type(param, func_name)}}} {param} - {param_desc}')

    # Add returns if function name suggests it returns something
    if should_have_return(func_name, signature):
        return_type, return_desc = get_return_info(func_name, signature)
        lines.append('     *')
        lines.append(f'     * @returns {{{return_type}}} {return_desc}')

    # Add throws if function might throw errors
    if might_throw_errors(func_name, signature):
        lines.append('     *')
        lines.append('     * @throws {Error} If operation fails or validation errors occur')

    lines.append('     */')
    return '\n'.join(lines)

def generate_purpose_from_name(func_name: str) -> str:
    """Generate purpose description from function name."""
    # Convert camelCase/snake_case to words
    words = re.sub(r'([A-Z])', r' \1', func_name).split()
    words = [w.lower() for w in words if w]

    # Common patterns
    if func_name.startswith('init'):
        return f"Initialize {' '.join(words[1:])} component"
    elif func_name.startswith('load'):
        return f"Load {' '.join(words[1:])} data from server"
    elif func_name.startswith('render'):
        return f"Render {' '.join(words[1:])} UI component"
    elif func_name.startswith('show') or func_name.startswith('display'):
        return f"Display {' '.join(words[1:])} interface"
    elif func_name.startswith('hide') or func_name.startswith('close'):
        return f"Hide {' '.join(words[1:])} interface"
    elif func_name.startswith('handle'):
        return f"Handle {' '.join(words[1:])} event"
    elif func_name.startswith('update'):
        return f"Update {' '.join(words[1:])} state"
    elif func_name.startswith('get'):
        return f"Retrieve {' '.join(words[1:])} information"
    elif func_name.startswith('set'):
        return f"Set {' '.join(words[1:])} value"
    elif func_name.startswith('create'):
        return f"Create new {' '.join(words[1:])} instance"
    elif func_name.startswith('delete') or func_name.startswith('remove'):
        return f"Remove {' '.join(words[1:])} from system"
    elif func_name.startswith('validate'):
        return f"Validate {' '.join(words[1:])} input"
    elif func_name.startswith('format'):
        return f"Format {' '.join(words[1:])} for display"
    elif func_name.startswith('filter'):
        return f"Filter {' '.join(words[1:])} based on criteria"
    elif func_name.startswith('sort'):
        return f"Sort {' '.join(words[1:])} in specified order"
    elif func_name.startswith('search'):
        return f"Search for {' '.join(words[1:])}"
    elif func_name.startswith('fetch'):
        return f"Fetch {' '.join(words[1:])} from API"
    elif func_name.startswith('save'):
        return f"Save {' '.join(words[1:])} to storage"
    elif func_name.startswith('on'):
        return f"Event handler for {' '.join(words[1:])} events"
    elif func_name.startswith('toggle'):
        return f"Toggle {' '.join(words[1:])} state"
    elif func_name.startswith('enable'):
        return f"Enable {' '.join(words[1:])} functionality"
    elif func_name.startswith('disable'):
        return f"Disable {' '.join(words[1:])} functionality"
    elif func_name == 'constructor':
        return "Initialize class instance with default state"
    else:
        return f"Execute {func_name.replace('_', ' ')} operation"

def generate_why_from_name(func_name: str) -> str:
    """Generate why description from function name."""
    if func_name.startswith('init'):
        return "Proper initialization ensures component reliability and correct state"
    elif func_name.startswith('load'):
        return "Dynamic data loading enables real-time content updates"
    elif func_name.startswith('render'):
        return "Separates presentation logic for maintainable UI code"
    elif func_name.startswith('show') or func_name.startswith('display'):
        return "Provides user interface for interaction and data visualization"
    elif func_name.startswith('hide') or func_name.startswith('close'):
        return "Improves UX by managing interface visibility and state"
    elif func_name.startswith('handle'):
        return "Encapsulates event handling logic for better code organization"
    elif func_name.startswith('update'):
        return "Keeps application state synchronized with user actions and data changes"
    elif func_name.startswith('get'):
        return "Provides controlled access to internal data and state"
    elif func_name.startswith('set'):
        return "Maintains data integrity through controlled mutation"
    elif func_name.startswith('create'):
        return "Factory method pattern for consistent object creation"
    elif func_name.startswith('delete') or func_name.startswith('remove'):
        return "Manages resource cleanup and data consistency"
    elif func_name.startswith('validate'):
        return "Ensures data integrity and prevents invalid states"
    elif func_name.startswith('format'):
        return "Consistent data presentation improves user experience"
    elif func_name.startswith('filter'):
        return "Enables users to find relevant data quickly"
    elif func_name.startswith('sort'):
        return "Organized data presentation improves usability"
    elif func_name.startswith('search'):
        return "Enables efficient data discovery and navigation"
    elif func_name.startswith('fetch'):
        return "Centralizes API communication for consistent error handling"
    elif func_name.startswith('save'):
        return "Persists user data and application state"
    elif func_name.startswith('on'):
        return "Responds to user interactions and system events"
    elif func_name.startswith('toggle'):
        return "Provides binary state management for UI elements"
    elif func_name.startswith('enable') or func_name.startswith('disable'):
        return "Controls feature availability based on user permissions or state"
    elif func_name == 'constructor':
        return "Establishes initial state required for class functionality"
    else:
        return "Implements required business logic for system functionality"

def generate_param_description(param: str, func_name: str) -> str:
    """Generate parameter description."""
    # Common parameter names
    param_lower = param.lower()

    if param_lower in ['id', 'userid', 'orgid', 'projectid', 'trackid', 'courseid']:
        return "Unique identifier"
    elif param_lower in ['name', 'username', 'orgname']:
        return "Name value"
    elif param_lower in ['email']:
        return "Email address"
    elif param_lower in ['data', 'payload']:
        return "Data object"
    elif param_lower in ['event', 'e']:
        return "Event object"
    elif param_lower in ['callback', 'cb']:
        return "Callback function"
    elif param_lower in ['options', 'opts', 'config']:
        return "Configuration options"
    elif param_lower in ['index', 'idx']:
        return "Array index"
    elif param_lower in ['type']:
        return "Type identifier"
    elif param_lower in ['value', 'val']:
        return "Value to set or process"
    elif param_lower in ['filter']:
        return "Filter criteria"
    elif param_lower in ['sort', 'sortby']:
        return "Sort specification"
    elif param_lower in ['limit']:
        return "Maximum number of results"
    elif param_lower in ['offset']:
        return "Starting offset"
    else:
        return f"{param.replace('_', ' ').capitalize()} parameter"

def get_param_type(param: str, func_name: str) -> str:
    """Infer parameter type from name."""
    param_lower = param.lower()

    if 'id' in param_lower:
        return 'string|number'
    elif param_lower in ['event', 'e']:
        return 'Event'
    elif param_lower in ['callback', 'cb']:
        return 'Function'
    elif param_lower in ['data', 'payload', 'options', 'opts', 'config']:
        return 'Object'
    elif param_lower in ['index', 'idx', 'count', 'limit', 'offset']:
        return 'number'
    elif param_lower in ['flag', 'enabled', 'disabled', 'active']:
        return 'boolean'
    elif param_lower in ['items', 'list', 'array']:
        return 'Array'
    else:
        return '*'

def should_have_return(func_name: str, signature: str) -> bool:
    """Determine if function should have return doc."""
    # Async functions always return promises
    if 'async' in signature:
        return True

    # Functions that typically return values
    return_prefixes = ['get', 'fetch', 'load', 'calculate', 'compute', 'generate',
                       'create', 'format', 'validate', 'is', 'has', 'should', 'can',
                       'find', 'filter', 'map', 'reduce', 'parse']

    return any(func_name.startswith(prefix) for prefix in return_prefixes)

def get_return_info(func_name: str, signature: str) -> Tuple[str, str]:
    """Get return type and description."""
    if 'async' in signature:
        if func_name.startswith('get') or func_name.startswith('fetch'):
            return 'Promise<Object>', 'Promise resolving to requested data'
        elif func_name.startswith('load'):
            return 'Promise<void>', 'Promise resolving when loading completes'
        else:
            return 'Promise', 'Promise resolving when operation completes'

    if func_name.startswith('get'):
        return 'Object|null', 'Retrieved data or null if not found'
    elif func_name.startswith('is') or func_name.startswith('has') or func_name.startswith('should') or func_name.startswith('can'):
        return 'boolean', 'True if condition is met, false otherwise'
    elif func_name.startswith('format'):
        return 'string', 'Formatted string'
    elif func_name.startswith('validate'):
        return 'boolean', 'True if validation passes, false otherwise'
    elif func_name.startswith('create'):
        return 'Object', 'Newly created instance'
    elif func_name.startswith('generate'):
        return 'string|Object', 'Generated content'
    elif func_name.startswith('calculate') or func_name.startswith('compute'):
        return 'number', 'Calculated value'
    elif func_name.startswith('find'):
        return 'Object|null', 'Found item or null'
    elif func_name.startswith('filter'):
        return 'Array', 'Filtered array'
    else:
        return '*', 'Operation result'

def might_throw_errors(func_name: str, signature: str) -> bool:
    """Determine if function might throw errors."""
    error_indicators = ['async', 'fetch', 'load', 'save', 'delete', 'create',
                       'update', 'validate', 'parse', 'api']
    return any(indicator in signature.lower() or indicator in func_name.lower()
               for indicator in error_indicators)

def process_file(filepath: Path) -> int:
    """
    Process a single JavaScript file and add JSDoc comments.

    Args:
        filepath: Path to JavaScript file

    Returns:
        Number of functions documented
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    modified = False
    documented_count = 0
    new_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Check if this line is a function declaration
        is_function = False
        func_name = None
        func_type = None

        # Patterns to match various function declarations
        patterns = [
            (r'^\s*function\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\([^)]*\)', 'function'),
            (r'^\s*(?:const|let|var)\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>', 'arrow'),
            (r'^\s*(?:async\s+)?([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\([^)]*\)\s*\{', 'method'),
            (r'^\s*([a-zA-Z_$][a-zA-Z0-9_$]*)\s*:\s*(?:async\s*)?\([^)]*\)\s*=>', 'arrow_method'),
        ]

        for pattern, ftype in patterns:
            match = re.match(pattern, line)
            if match:
                func_name = match.group(1)
                func_type = ftype
                is_function = True
                break

        if is_function and func_name:
            # Skip common non-function patterns
            if func_name in ['if', 'for', 'while', 'switch', 'catch']:
                new_lines.append(line)
                i += 1
                continue

            # Check if already documented
            if has_jsdoc_comment(lines, i):
                new_lines.append(line)
                i += 1
                continue

            # Generate and add JSDoc
            jsdoc = generate_jsdoc(func_name, line.strip(), func_type)
            new_lines.append(jsdoc + '\n')
            new_lines.append(line)
            modified = True
            documented_count += 1
        else:
            new_lines.append(line)

        i += 1

    # Write back if modified
    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print(f"✅ {filepath}: Added {documented_count} JSDoc comments")

    return documented_count

def main():
    """Main execution function."""
    base_path = Path('/home/bbrelin/course-creator')

    # Directories to process
    directories = [
        base_path / 'frontend' / 'js' / 'modules',
        base_path / 'frontend' / 'js'
    ]

    total_documented = 0
    files_processed = 0

    for directory in directories:
        if not directory.exists():
            continue

        for js_file in directory.rglob('*.js'):
            try:
                count = process_file(js_file)
                if count > 0:
                    total_documented += count
                    files_processed += 1
            except Exception as e:
                print(f"❌ Error processing {js_file}: {e}")

    print(f"\n{'='*60}")
    print(f"✨ Documentation Complete!")
    print(f"{'='*60}")
    print(f"Files Modified: {files_processed}")
    print(f"Total JSDoc Comments Added: {total_documented}")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()
