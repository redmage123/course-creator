#!/usr/bin/env python3
"""
Update test file imports to use new service-specific namespaces.

This script updates test files that import from the old domain/application/infrastructure
namespaces to use the new service-specific namespaces.
"""

import re
from pathlib import Path
from typing import Dict, List

# Mapping of test directories to their corresponding service namespaces
TEST_SERVICE_MAPPING = {
    'tests/unit/analytics': 'analytics',
    'tests/unit/content_management': 'content_management',
    'tests/unit/course_management': 'course_management',
    'tests/unit/knowledge_graph': 'knowledge_graph_service',
    'tests/unit/metadata': 'metadata_service',
    'tests/unit/nlp_preprocessing': 'nlp_preprocessing',
    'tests/unit/organization_management': 'organization_management',
    'tests/unit/user_management': 'user_management',
}

# For integration/e2e tests, we need to determine the service from import context
INTEGRATION_SERVICE_HINTS = {
    'test_metadata_service_e2e.py': 'metadata_service',
    'test_knowledge_graph_e2e.py': 'knowledge_graph_service',
    'test_track_system': 'organization_management',
    'test_course_management': 'course_management',
    'test_rbac_validation.py': 'user_management',  # Uses User entity
}


def determine_service_namespace(file_path: Path) -> str:
    """
    Determine which service namespace to use for a test file.

    Args:
        file_path: Path to test file

    Returns:
        Service namespace to use, or None if cannot be determined
    """
    file_str = str(file_path)

    # Check unit test mappings
    for test_dir, service_name in TEST_SERVICE_MAPPING.items():
        if test_dir in file_str:
            return service_name

    # Check integration/e2e hints
    for hint, service_name in INTEGRATION_SERVICE_HINTS.items():
        if hint in file_path.name:
            return service_name

    return None


def update_imports_in_file(file_path: Path, dry_run: bool = False) -> tuple:
    """
    Update imports in a single test file.

    Args:
        file_path: Path to test file
        dry_run: If True, only preview changes

    Returns:
        Tuple of (success, changes_made, error_message)
    """
    service_namespace = determine_service_namespace(file_path)

    if not service_namespace:
        return False, 0, f"Cannot determine service namespace for {file_path}"

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.splitlines(keepends=True)

        changes_made = 0
        new_lines = []

        for line in lines:
            # Match imports from domain/application/infrastructure
            if re.match(r'^from (domain|application|infrastructure)\.', line):
                # Replace with service-specific namespace
                new_line = re.sub(
                    r'^from (domain|application|infrastructure)\.',
                    f'from {service_namespace}.\\1.',
                    line
                )
                new_lines.append(new_line)
                changes_made += 1
            elif re.match(r'^import (domain|application|infrastructure)(?:\.|$)', line):
                # Replace direct imports
                new_line = re.sub(
                    r'^import (domain|application|infrastructure)(?=\.|\s|$)',
                    f'import {service_namespace}.\\1',
                    line
                )
                new_lines.append(new_line)
                changes_made += 1
            else:
                new_lines.append(line)

        if changes_made > 0 and not dry_run:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)

        return True, changes_made, None

    except Exception as e:
        return False, 0, str(e)


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(description='Update test imports to new namespaces')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without applying')
    args = parser.parse_args()

    # Find all test files with old imports
    test_files = []
    tests_dir = Path('tests')

    for pattern in ['domain', 'application', 'infrastructure']:
        for test_file in tests_dir.rglob('*.py'):
            if test_file in test_files:
                continue

            try:
                with open(test_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if re.search(rf'^from {pattern}\.', content, re.MULTILINE) or \
                       re.search(rf'^import {pattern}(?:\.|$)', content, re.MULTILINE):
                        test_files.append(test_file)
            except:
                pass

    print(f"{'DRY RUN - ' if args.dry_run else ''}Updating {len(test_files)} test files...")
    print()

    total_changes = 0
    successes = 0
    failures = []

    for test_file in sorted(test_files):
        success, changes, error = update_imports_in_file(test_file, args.dry_run)

        if success:
            if changes > 0:
                successes += 1
                total_changes += changes
                print(f"✓ {test_file}: {changes} imports updated")
        else:
            failures.append((test_file, error))
            print(f"✗ {test_file}: {error}")

    print()
    print(f"Summary: {successes} files updated, {total_changes} imports changed")

    if failures:
        print(f"\nFailed: {len(failures)} files")
        for file_path, error in failures:
            print(f"  - {file_path}: {error}")


if __name__ == '__main__':
    main()
