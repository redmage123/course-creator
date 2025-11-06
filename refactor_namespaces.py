#!/usr/bin/env python3
"""
Namespace Refactoring Script for Course Creator Microservices

This script automates the refactoring of 13 microservices to use unique namespaces
instead of colliding "domain"/"application"/"infrastructure" names.

Business Context:
-----------------
The current architecture has all services using the same top-level package names
(domain, application, infrastructure), which causes namespace collisions when
services need to interact or when running in the same Python environment.

Technical Approach:
------------------
1. Restructure directories: Move domain/application/infrastructure under service-specific package
2. Rewrite imports: Update all Python files to use the new namespace
3. Validate: Ensure all imports are syntactically correct after refactoring
4. Safety: Create backups and support dry-run mode

Usage:
------
    python refactor_namespaces.py --dry-run              # Preview changes
    python refactor_namespaces.py                        # Execute refactoring
    python refactor_namespaces.py --service analytics    # Refactor single service
    python refactor_namespaces.py --validate             # Validate imports only

Author: Claude Code
Version: 1.0.0
"""

import os
import re
import ast
import shutil
import argparse
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Set
from dataclasses import dataclass
from datetime import datetime
import subprocess


@dataclass
class RefactoringChange:
    """Represents a single refactoring change"""
    file_path: str
    line_number: int
    old_import: str
    new_import: str
    change_type: str  # 'import' or 'directory'


@dataclass
class ServiceRefactoringReport:
    """Report for a single service refactoring"""
    service_name: str
    success: bool
    directories_moved: List[Tuple[str, str]]
    imports_changed: List[RefactoringChange]
    errors: List[str]
    warnings: List[str]


class NamespaceRefactorer:
    """
    Main refactoring engine for namespace migration.

    This class handles the complete refactoring process including:
    - Directory restructuring
    - Import statement rewriting
    - Validation and safety checks
    - Backup creation
    """

    SERVICES_DIR = Path("/home/bbrelin/course-creator/services")
    BACKUP_DIR = Path("/home/bbrelin/course-creator/.backups/namespace_refactoring")

    # Services to refactor (exclude special directories)
    EXCLUDE_DIRS = {'__pycache__', '__init__.py'}

    # Directories to move under service namespace
    NAMESPACE_DIRS = ['domain', 'application', 'infrastructure']

    def __init__(self, dry_run: bool = False, verbose: bool = False):
        """
        Initialize the refactoring engine.

        Args:
            dry_run: If True, only preview changes without executing
            verbose: If True, print detailed progress information
        """
        self.dry_run = dry_run
        self.verbose = verbose
        self.reports: List[ServiceRefactoringReport] = []

    def get_services(self) -> List[str]:
        """
        Get list of all services to refactor.

        Returns:
            List of service directory names
        """
        services = []
        for item in self.SERVICES_DIR.iterdir():
            if item.is_dir() and item.name not in self.EXCLUDE_DIRS:
                services.append(item.name)
        return sorted(services)

    def create_backup(self, service_name: str) -> bool:
        """
        Create backup of service before refactoring.

        Args:
            service_name: Name of the service to backup

        Returns:
            True if backup successful, False otherwise
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            service_path = self.SERVICES_DIR / service_name
            backup_path = self.BACKUP_DIR / f"{service_name}_{timestamp}"

            if not self.dry_run:
                self.BACKUP_DIR.mkdir(parents=True, exist_ok=True)
                shutil.copytree(service_path, backup_path)

            self.log(f"✓ Created backup: {backup_path}", verbose_only=True)
            return True

        except Exception as e:
            self.log(f"✗ Backup failed for {service_name}: {e}", error=True)
            return False

    def find_python_files(self, service_path: Path) -> List[Path]:
        """
        Find all Python files in service directory.

        Args:
            service_path: Path to service directory

        Returns:
            List of Python file paths
        """
        python_files = []
        for root, dirs, files in os.walk(service_path):
            # Skip __pycache__ and backup directories
            dirs[:] = [d for d in dirs if d not in {'__pycache__', '.backup', 'venv', '.venv'}]

            for file in files:
                if file.endswith('.py'):
                    python_files.append(Path(root) / file)

        return python_files

    def analyze_imports(self, file_path: Path, service_name: str) -> List[RefactoringChange]:
        """
        Analyze Python file for imports that need refactoring.

        Args:
            file_path: Path to Python file
            service_name: Name of the service (for new namespace)

        Returns:
            List of RefactoringChange objects
        """
        changes = []

        # Convert hyphenated service name to Python package name
        python_package_name = service_name.replace('-', '_')

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for line_num, line in enumerate(lines, 1):
                # Match import patterns for domain/application/infrastructure
                patterns = [
                    (r'^from (domain|application|infrastructure)\.', 'from_import'),
                    (r'^import (domain|application|infrastructure)(?:\.|$)', 'direct_import')
                ]

                for pattern, import_type in patterns:
                    match = re.search(pattern, line)
                    if match:
                        namespace = match.group(1)

                        if import_type == 'from_import':
                            old_import = line.strip()
                            new_import = line.replace(
                                f'from {namespace}.',
                                f'from {python_package_name}.{namespace}.'
                            ).strip()
                        else:  # direct_import
                            old_import = line.strip()
                            new_import = re.sub(
                                rf'import {namespace}(?=\.|\s|$)',
                                f'import {python_package_name}.{namespace}',
                                line
                            ).strip()

                        changes.append(RefactoringChange(
                            file_path=str(file_path),
                            line_number=line_num,
                            old_import=old_import,
                            new_import=new_import,
                            change_type='import'
                        ))
                        break  # Only one match per line

        except Exception as e:
            self.log(f"✗ Error analyzing {file_path}: {e}", error=True)

        return changes

    def apply_import_changes(self, file_path: Path, changes: List[RefactoringChange]) -> bool:
        """
        Apply import changes to a Python file.

        Args:
            file_path: Path to Python file
            changes: List of changes to apply

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.splitlines(keepends=True)

            # Apply changes in reverse order to preserve line numbers
            for change in sorted(changes, key=lambda c: c.line_number, reverse=True):
                line_idx = change.line_number - 1
                if line_idx < len(lines):
                    lines[line_idx] = lines[line_idx].replace(
                        change.old_import,
                        change.new_import
                    )

            if not self.dry_run:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)

            return True

        except Exception as e:
            self.log(f"✗ Error applying changes to {file_path}: {e}", error=True)
            return False

    def restructure_directories(self, service_name: str) -> Tuple[bool, List[Tuple[str, str]], List[str]]:
        """
        Restructure service directories to create service-specific namespace.

        This moves domain/application/infrastructure under a SERVICE_NAME/ directory.

        Args:
            service_name: Name of the service

        Returns:
            Tuple of (success, list of (old_path, new_path) moves, errors)
        """
        service_path = self.SERVICES_DIR / service_name
        moves = []
        errors = []

        # Create service namespace directory - convert hyphenated name to Python package name
        python_package_name = service_name.replace('-', '_')
        namespace_dir = service_path / python_package_name

        if not self.dry_run:
            try:
                namespace_dir.mkdir(exist_ok=True)
                # Create __init__.py for the namespace package
                (namespace_dir / '__init__.py').touch()
            except Exception as e:
                errors.append(f"Failed to create namespace directory: {e}")
                return False, moves, errors

        # Move each namespace directory
        for dir_name in self.NAMESPACE_DIRS:
            old_dir = service_path / dir_name
            new_dir = namespace_dir / dir_name

            if old_dir.exists() and old_dir.is_dir():
                try:
                    if not self.dry_run:
                        shutil.move(str(old_dir), str(new_dir))
                    moves.append((str(old_dir), str(new_dir)))
                    self.log(f"  ✓ Moved {old_dir.name}/ → {service_name}/{dir_name}/", verbose_only=True)
                except Exception as e:
                    errors.append(f"Failed to move {dir_name}: {e}")
                    return False, moves, errors

        return True, moves, errors

    def validate_python_syntax(self, file_path: Path) -> Tuple[bool, str]:
        """
        Validate Python file syntax.

        Args:
            file_path: Path to Python file

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                ast.parse(f.read())
            return True, ""
        except SyntaxError as e:
            return False, f"Syntax error at line {e.lineno}: {e.msg}"
        except Exception as e:
            return False, str(e)

    def validate_service_imports(self, service_name: str) -> Tuple[bool, List[str]]:
        """
        Validate all Python imports in a service.

        Args:
            service_name: Name of the service

        Returns:
            Tuple of (all_valid, list of errors)
        """
        service_path = self.SERVICES_DIR / service_name
        python_files = self.find_python_files(service_path)
        errors = []

        for file_path in python_files:
            is_valid, error_msg = self.validate_python_syntax(file_path)
            if not is_valid:
                errors.append(f"{file_path}: {error_msg}")

        return len(errors) == 0, errors

    def refactor_service(self, service_name: str) -> ServiceRefactoringReport:
        """
        Refactor a single service.

        Args:
            service_name: Name of the service to refactor

        Returns:
            ServiceRefactoringReport with results
        """
        self.log(f"\n{'='*80}")
        self.log(f"Refactoring service: {service_name}")
        self.log(f"{'='*80}")

        report = ServiceRefactoringReport(
            service_name=service_name,
            success=False,
            directories_moved=[],
            imports_changed=[],
            errors=[],
            warnings=[]
        )

        # Step 1: Create backup
        if not self.create_backup(service_name):
            report.errors.append("Backup creation failed")
            return report

        # Step 2: Analyze imports BEFORE restructuring
        service_path = self.SERVICES_DIR / service_name
        python_files = self.find_python_files(service_path)

        self.log(f"\nStep 1: Analyzing {len(python_files)} Python files...")
        all_import_changes = []

        for file_path in python_files:
            changes = self.analyze_imports(file_path, service_name)
            all_import_changes.extend(changes)
            if changes:
                self.log(f"  ✓ Found {len(changes)} imports to update in {file_path.name}", verbose_only=True)

        report.imports_changed = all_import_changes
        self.log(f"Total imports to refactor: {len(all_import_changes)}")

        # Step 3: Restructure directories
        self.log(f"\nStep 2: Restructuring directories...")
        success, moves, errors = self.restructure_directories(service_name)

        if not success:
            report.errors.extend(errors)
            return report

        report.directories_moved = moves

        # Step 4: Update imports
        self.log(f"\nStep 3: Updating imports in {len(python_files)} files...")

        # Re-find Python files after restructuring (paths have changed)
        python_files = self.find_python_files(service_path)

        for file_path in python_files:
            # Find changes for this file
            file_changes = [c for c in all_import_changes if Path(c.file_path).name == file_path.name]

            if file_changes:
                # Re-analyze with current file locations
                current_changes = self.analyze_imports(file_path, service_name)
                if current_changes:
                    if not self.apply_import_changes(file_path, current_changes):
                        report.errors.append(f"Failed to update imports in {file_path}")
                    else:
                        self.log(f"  ✓ Updated {len(current_changes)} imports in {file_path.name}", verbose_only=True)

        # Step 5: Validate
        self.log(f"\nStep 4: Validating Python syntax...")
        is_valid, validation_errors = self.validate_service_imports(service_name)

        if not is_valid:
            report.errors.extend(validation_errors)
            report.warnings.append(f"Validation found {len(validation_errors)} syntax errors")
            self.log(f"  ✗ Validation failed with {len(validation_errors)} errors", error=True)
        else:
            self.log(f"  ✓ All Python files have valid syntax")

        # Mark as successful if no critical errors
        report.success = len(report.errors) == 0

        return report

    def refactor_all_services(self, service_filter: str = None) -> List[ServiceRefactoringReport]:
        """
        Refactor all services or a filtered subset.

        Args:
            service_filter: Optional service name to refactor only that service

        Returns:
            List of ServiceRefactoringReport objects
        """
        services = self.get_services()

        if service_filter:
            if service_filter in services:
                services = [service_filter]
            else:
                self.log(f"✗ Service '{service_filter}' not found", error=True)
                self.log(f"Available services: {', '.join(services)}")
                return []

        self.log(f"\n🔧 Namespace Refactoring Tool")
        self.log(f"{'='*80}")
        self.log(f"Mode: {'DRY RUN (no changes will be made)' if self.dry_run else 'LIVE EXECUTION'}")
        self.log(f"Services to refactor: {len(services)}")
        self.log(f"Services: {', '.join(services)}")

        if not self.dry_run:
            response = input("\nProceed with refactoring? (yes/no): ")
            if response.lower() != 'yes':
                self.log("Refactoring cancelled by user")
                return []

        reports = []
        for service_name in services:
            report = self.refactor_service(service_name)
            reports.append(report)

        self.reports = reports
        return reports

    def print_summary(self):
        """Print summary report of all refactoring operations"""
        if not self.reports:
            return

        self.log(f"\n\n{'='*80}")
        self.log(f"REFACTORING SUMMARY")
        self.log(f"{'='*80}\n")

        successful = [r for r in self.reports if r.success]
        failed = [r for r in self.reports if not r.success]

        # Overall statistics
        total_imports = sum(len(r.imports_changed) for r in self.reports)
        total_dirs = sum(len(r.directories_moved) for r in self.reports)

        self.log(f"Services processed: {len(self.reports)}")
        self.log(f"  ✓ Successful: {len(successful)}")
        self.log(f"  ✗ Failed: {len(failed)}")
        self.log(f"\nTotal changes:")
        self.log(f"  • Directories moved: {total_dirs}")
        self.log(f"  • Imports updated: {total_imports}")

        # Detailed results per service
        self.log(f"\n{'─'*80}")
        self.log(f"DETAILED RESULTS")
        self.log(f"{'─'*80}\n")

        for report in self.reports:
            status = "✓ SUCCESS" if report.success else "✗ FAILED"
            self.log(f"{status} - {report.service_name}")
            self.log(f"  Directories moved: {len(report.directories_moved)}")
            self.log(f"  Imports updated: {len(report.imports_changed)}")

            if report.errors:
                self.log(f"  Errors:")
                for error in report.errors:
                    self.log(f"    • {error}")

            if report.warnings:
                self.log(f"  Warnings:")
                for warning in report.warnings:
                    self.log(f"    • {warning}")

            self.log("")

        # Failed services
        if failed:
            self.log(f"\n{'!'*80}")
            self.log(f"FAILED SERVICES - MANUAL INTERVENTION REQUIRED")
            self.log(f"{'!'*80}\n")

            for report in failed:
                self.log(f"Service: {report.service_name}")
                for error in report.errors:
                    self.log(f"  • {error}")
                self.log("")

        # Next steps
        self.log(f"\n{'='*80}")
        self.log(f"NEXT STEPS")
        self.log(f"{'='*80}\n")

        if self.dry_run:
            self.log("This was a DRY RUN. No changes were made.")
            self.log("To apply changes, run without --dry-run flag")
        else:
            self.log("Refactoring complete. Recommended next steps:")
            self.log("1. Run tests to ensure functionality: pytest")
            self.log("2. Check for any runtime import errors")
            self.log("3. Update any deployment scripts that reference old paths")
            self.log("4. Commit changes: git add . && git commit -m 'refactor: namespace refactoring'")
            self.log(f"\nBackups saved to: {self.BACKUP_DIR}")

    def log(self, message: str, verbose_only: bool = False, error: bool = False):
        """
        Log a message to console.

        Args:
            message: Message to log
            verbose_only: Only log if verbose mode is enabled
            error: Whether this is an error message
        """
        if verbose_only and not self.verbose:
            return

        if error:
            print(f"ERROR: {message}", file=sys.stderr)
        else:
            print(message)


def main():
    """Main entry point for the refactoring script"""
    parser = argparse.ArgumentParser(
        description="Refactor microservices to use unique namespaces",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --dry-run                    Preview all changes
  %(prog)s --service analytics          Refactor only analytics service
  %(prog)s --verbose                    Show detailed progress
  %(prog)s --validate                   Only validate current imports
        """
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without executing them'
    )

    parser.add_argument(
        '--service',
        type=str,
        help='Refactor only the specified service'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed progress information'
    )

    parser.add_argument(
        '--validate',
        action='store_true',
        help='Only validate Python syntax, do not refactor'
    )

    args = parser.parse_args()

    refactorer = NamespaceRefactorer(
        dry_run=args.dry_run or args.validate,
        verbose=args.verbose
    )

    if args.validate:
        # Validation mode
        services = refactorer.get_services()
        if args.service:
            services = [args.service] if args.service in services else []

        print(f"\n🔍 Validating Python imports for {len(services)} services...\n")

        all_valid = True
        for service_name in services:
            is_valid, errors = refactorer.validate_service_imports(service_name)
            status = "✓" if is_valid else "✗"
            print(f"{status} {service_name}")

            if not is_valid:
                all_valid = False
                for error in errors:
                    print(f"  • {error}")

        sys.exit(0 if all_valid else 1)

    # Refactoring mode
    reports = refactorer.refactor_all_services(service_filter=args.service)
    refactorer.print_summary()

    # Exit with error code if any service failed
    if any(not r.success for r in reports):
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
