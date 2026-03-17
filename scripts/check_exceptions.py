#!/usr/bin/env python3
"""
Pre-Commit Hook: Generic Exception Handler Checker

This script enforces the CLAUDE.md requirement that all code must use
specific custom exceptions instead of generic 'except Exception' handlers.

Exit Codes:
    0: All files pass (no generic exception handlers)
    1: One or more files have generic exception handlers

Usage:
    python scripts/check_exceptions.py <file1.py> [file2.py] ...

    # Check all Python files in repository
    python scripts/check_exceptions.py $(find . -name "*.py" -not -path "./.venv/*")

    # Check specific file
    python scripts/check_exceptions.py services/course-management/data_access/course_dao.py
"""

import re
import sys
import os
from pathlib import Path
from typing import List, Tuple, Dict


# Patterns to detect generic exception handlers
GENERIC_EXCEPTION_PATTERNS = [
    # Matches: except Exception as e:
    (r'except\s+Exception\s+as\s+\w+\s*:', 'except Exception as e:'),

    # Matches: except Exception:
    (r'except\s+Exception\s*:', 'except Exception:'),

    # Matches: except BaseException as e:
    (r'except\s+BaseException\s+as\s+\w+\s*:', 'except BaseException as e:'),

    # Matches: except BaseException:
    (r'except\s+BaseException\s*:', 'except BaseException:'),
]

# Files/directories to exclude from checking
EXCLUDE_PATTERNS = [
    # Test files that test exception handling itself
    'tests/unit/test_exception_handling.py',
    'tests/unit/shared/test_exceptions.py',

    # Exception definition files
    'shared/exceptions.py',
    'shared/exceptions/__init__.py',

    # This checker script itself
    'scripts/check_exceptions.py',

    # Virtual environments
    '.venv/',
    'venv/',
    'env/',

    # Build artifacts
    '__pycache__/',
    '.pytest_cache/',
    'build/',
    'dist/',
    '*.egg-info/',

    # Version control
    '.git/',

    # Node modules
    'node_modules/',

    # Frontend (JavaScript/TypeScript)
    'frontend/',
    'frontend-react/',
]

# Suggestions for common patterns
SUGGESTIONS = {
    'except Exception as e:': '''
┌─────────────────────────────────────────────────────────────────┐
│ SUGGESTED FIX: Use specific exception types                     │
└─────────────────────────────────────────────────────────────────┘

Import specific exceptions:
    from shared.exceptions import (
        DatabaseException,
        ValidationException,
        ServiceException,
        ConflictException,
        NotFoundException
    )

For database operations (asyncpg):
    try:
        await conn.execute(...)
    except asyncpg.UniqueViolationError as e:
        raise ConflictException(...)
    except asyncpg.ForeignKeyViolationError as e:
        raise ValidationException(...)
    except asyncpg.PostgresError as e:
        raise DatabaseException(...)

For HTTP calls (httpx):
    try:
        response = await client.get(url)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise NotFoundException(...)
        elif e.response.status_code == 401:
            raise AuthenticationException(...)
    except httpx.NetworkError as e:
        raise ServiceException(...)

See: docs/EXCEPTION_MAPPING_GUIDE.md for complete mappings
''',

    'except BaseException as e:': '''
┌─────────────────────────────────────────────────────────────────┐
│ WARNING: BaseException catches system exits!                    │
└─────────────────────────────────────────────────────────────────┘

BaseException catches KeyboardInterrupt and SystemExit.
Use Exception or more specific exceptions instead.

Replace:
    except BaseException as e:  # BAD

With:
    except Exception as e:  # Still generic - make it specific!
    # Or better:
    except SpecificException as e:  # GOOD
''',

    'decorator': '''
┌─────────────────────────────────────────────────────────────────┐
│ TIP: Use decorator pattern for repetitive exception handling    │
└─────────────────────────────────────────────────────────────────┘

For DAO methods:
    @handle_database_exceptions("create_course", "courses")
    async def create_course(self, course: Course) -> Course:
        # No try/except needed - decorator handles it!
        async with self.db_pool.acquire() as conn:
            return await conn.execute(...)

For HTTP calls:
    @handle_http_exceptions("course-generator", "POST /generate")
    async def call_service(self, data: dict) -> dict:
        # No try/except needed - decorator handles it!
        response = await client.post(url, json=data)
        return response.json()

See: docs/EXCEPTION_MAPPING_GUIDE.md (Decorator Pattern section)
'''
}


def is_excluded(filepath: str) -> bool:
    """
    Check if file should be excluded from checking.

    Args:
        filepath: Path to the file to check

    Returns:
        True if file should be excluded, False otherwise
    """
    # Normalize path separators
    filepath = filepath.replace('\\', '/')

    for pattern in EXCLUDE_PATTERNS:
        if pattern in filepath:
            return True

    return False


def find_generic_exceptions(filepath: str) -> List[Tuple[int, str, str]]:
    """
    Find all generic exception handlers in a Python file.

    Args:
        filepath: Path to Python file to check

    Returns:
        List of tuples: (line_number, line_content, pattern_name)
    """
    matches = []

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for line_num, line in enumerate(lines, start=1):
            # Skip comments
            stripped = line.strip()
            if stripped.startswith('#'):
                continue

            # Skip docstrings (simple heuristic)
            if stripped.startswith('"""') or stripped.startswith("'''"):
                continue

            # Check each pattern
            for pattern, pattern_name in GENERIC_EXCEPTION_PATTERNS:
                if re.search(pattern, line):
                    matches.append((line_num, line.rstrip(), pattern_name))
                    break  # Only report first match per line

    except Exception as e:
        print(f"⚠️  ERROR: Failed to read {filepath}: {e}", file=sys.stderr)

    return matches


def print_file_violations(filepath: str, matches: List[Tuple[int, str, str]]) -> None:
    """
    Print violation details for a file.

    Args:
        filepath: Path to the file with violations
        matches: List of violations found
    """
    print(f"\n❌ {filepath}")
    print(f"   Found {len(matches)} generic exception handler(s):\n")

    for line_num, line, pattern_name in matches:
        print(f"   Line {line_num}:")
        print(f"      {line}")
        print()

    # Print relevant suggestion
    if matches:
        pattern_name = matches[0][2]  # Get first pattern name
        if pattern_name in SUGGESTIONS:
            print(SUGGESTIONS[pattern_name])
        else:
            print(SUGGESTIONS['except Exception as e:'])


def check_file(filepath: str, verbose: bool = False) -> bool:
    """
    Check a single file for generic exception handlers.

    Args:
        filepath: Path to Python file to check
        verbose: Whether to print detailed output

    Returns:
        True if file passes (no generic handlers), False otherwise
    """
    if is_excluded(filepath):
        if verbose:
            print(f"⏭️  Skipping excluded file: {filepath}")
        return True

    if not os.path.exists(filepath):
        print(f"⚠️  File not found: {filepath}", file=sys.stderr)
        return True  # Don't fail for missing files

    matches = find_generic_exceptions(filepath)

    if matches:
        print_file_violations(filepath, matches)
        return False

    if verbose:
        print(f"✅ {filepath}")

    return True


def print_summary(total_files: int, failed_files: List[str], total_violations: int) -> None:
    """
    Print summary of check results.

    Args:
        total_files: Total number of files checked
        failed_files: List of files that failed
        total_violations: Total number of violations found
    """
    print("\n" + "=" * 80)

    if not failed_files:
        print(f"✅ SUCCESS: All {total_files} file(s) passed")
        print("   No generic exception handlers found")
    else:
        print(f"❌ FAILURE: {len(failed_files)} of {total_files} file(s) failed")
        print(f"   Total violations: {total_violations}")
        print("\n   Failed files:")
        for filepath in failed_files:
            print(f"      • {filepath}")

        print("\n📖 REMEDIATION STEPS:")
        print("   1. Read: docs/EXCEPTION_MAPPING_GUIDE.md")
        print("   2. Replace generic 'except Exception' with specific exceptions")
        print("   3. Import from shared.exceptions module")
        print("   4. Run this checker again to verify")
        print("   5. Re-run git commit (if using pre-commit hook)")
        print()


def main():
    """Main entry point for exception checker."""
    # Parse arguments
    verbose = '-v' in sys.argv or '--verbose' in sys.argv
    help_requested = '-h' in sys.argv or '--help' in sys.argv

    if help_requested:
        print(__doc__)
        sys.exit(0)

    # Filter out flags from file list
    files_to_check = [arg for arg in sys.argv[1:] if not arg.startswith('-')]

    if not files_to_check:
        print("Usage: check_exceptions.py <file1.py> [file2.py] ...", file=sys.stderr)
        print("       check_exceptions.py --help", file=sys.stderr)
        sys.exit(1)

    # Filter to only Python files
    python_files = [f for f in files_to_check if f.endswith('.py')]

    if not python_files:
        print("✅ No Python files to check")
        sys.exit(0)

    # Print header
    print("\n" + "=" * 80)
    print(f"🔍 Checking {len(python_files)} Python file(s) for generic exception handlers")
    print("=" * 80)

    # Check each file
    all_passed = True
    failed_files = []
    total_violations = 0

    for filepath in python_files:
        passed = check_file(filepath, verbose=verbose)

        if not passed:
            all_passed = False
            failed_files.append(filepath)

            # Count violations for this file
            matches = find_generic_exceptions(filepath)
            total_violations += len(matches)

    # Print summary
    print_summary(len(python_files), failed_files, total_violations)

    # Exit with appropriate code
    sys.exit(0 if all_passed else 1)


if __name__ == '__main__':
    main()
