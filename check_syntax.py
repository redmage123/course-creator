#!/usr/bin/env python3
"""
Comprehensive Syntax Checker for Course Creator Platform

Checks all Python, JavaScript, JSON, and YAML files for syntax errors.
"""

import os
import sys
import py_compile
import json
import yaml
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple

# Directories to skip
SKIP_DIRS = {'.venv', 'node_modules', '.pytest_cache', '__pycache__', '.git', 'venv'}

# File extensions to check
EXTENSIONS = {
    'python': ['.py'],
    'javascript': ['.js'],
    'json': ['.json'],
    'yaml': ['.yaml', '.yml']
}

class SyntaxChecker:
    def __init__(self, root_dir: str = '.'):
        self.root_dir = Path(root_dir)
        self.errors = []
        self.checked_files = 0

    def should_skip_path(self, path: Path) -> bool:
        """Check if path should be skipped."""
        parts = path.parts
        return any(skip_dir in parts for skip_dir in SKIP_DIRS)

    def check_python_file(self, filepath: Path) -> Tuple[bool, str]:
        """Check Python file for syntax errors."""
        try:
            py_compile.compile(str(filepath), doraise=True)
            return True, ""
        except py_compile.PyCompileError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Error: {str(e)}"

    def check_javascript_file(self, filepath: Path) -> Tuple[bool, str]:
        """Check JavaScript file for syntax errors using Node.js."""
        try:
            # Try to parse with node
            result = subprocess.run(
                ['node', '--check', str(filepath)],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return True, ""
            else:
                return False, result.stderr
        except FileNotFoundError:
            # Node not available, skip
            return True, "Node.js not available for validation"
        except subprocess.TimeoutExpired:
            return False, "Timeout during validation"
        except Exception as e:
            return False, f"Error: {str(e)}"

    def check_json_file(self, filepath: Path) -> Tuple[bool, str]:
        """Check JSON file for syntax errors."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                json.load(f)
            return True, ""
        except json.JSONDecodeError as e:
            return False, f"JSON syntax error at line {e.lineno}: {e.msg}"
        except Exception as e:
            return False, f"Error: {str(e)}"

    def check_yaml_file(self, filepath: Path) -> Tuple[bool, str]:
        """Check YAML file for syntax errors."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                # Use safe_load_all for multi-document YAML (like Kubernetes files)
                list(yaml.safe_load_all(f))
            return True, ""
        except yaml.YAMLError as e:
            return False, f"YAML syntax error: {str(e)}"
        except Exception as e:
            return False, f"Error: {str(e)}"

    def check_file(self, filepath: Path) -> None:
        """Check a single file for syntax errors."""
        extension = filepath.suffix.lower()

        # Determine file type and check
        if extension in EXTENSIONS['python']:
            success, error = self.check_python_file(filepath)
            file_type = 'Python'
        elif extension in EXTENSIONS['javascript']:
            success, error = self.check_javascript_file(filepath)
            file_type = 'JavaScript'
        elif extension in EXTENSIONS['json']:
            success, error = self.check_json_file(filepath)
            file_type = 'JSON'
        elif extension in EXTENSIONS['yaml']:
            success, error = self.check_yaml_file(filepath)
            file_type = 'YAML'
        else:
            return

        self.checked_files += 1

        if not success and error and "not available" not in error:
            self.errors.append({
                'file': str(filepath),
                'type': file_type,
                'error': error
            })
            print(f"❌ {file_type} Error: {filepath}")
            print(f"   {error}\n")

    def scan_directory(self) -> None:
        """Scan directory for all files to check."""
        print("=" * 80)
        print("Course Creator Platform - Syntax Validation")
        print("=" * 80)
        print()

        # Collect all files
        all_extensions = []
        for exts in EXTENSIONS.values():
            all_extensions.extend(exts)

        for ext in all_extensions:
            pattern = f"**/*{ext}"
            for filepath in self.root_dir.glob(pattern):
                if not self.should_skip_path(filepath):
                    self.check_file(filepath)

        # Print summary
        print()
        print("=" * 80)
        print("Validation Summary")
        print("=" * 80)
        print(f"Total files checked: {self.checked_files}")
        print(f"Files with errors: {len(self.errors)}")
        print(f"Files passed: {self.checked_files - len(self.errors)}")
        print()

        if self.errors:
            print("❌ SYNTAX ERRORS FOUND:")
            print()
            for i, error in enumerate(self.errors, 1):
                print(f"{i}. {error['type']}: {error['file']}")
                print(f"   {error['error']}")
                print()
            return False
        else:
            print("✅ NO SYNTAX ERRORS FOUND!")
            print()
            return True

if __name__ == '__main__':
    checker = SyntaxChecker()
    success = checker.scan_directory()
    sys.exit(0 if success else 1)
