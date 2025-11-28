#!/usr/bin/env python3
"""
Script to fix common issues in course management E2E tests.

Fixes:
1. Database connection strings (port, credentials)
2. Page Object instantiations (missing config parameter)
3. Test method signatures (remove driver parameter)
4. Variable references (driver -> self.driver, config -> self.config, page -> self.page)
"""

import re
import sys
from pathlib import Path

def fix_test_file(filepath: Path):
    """Fix all common issues in a test file."""
    print(f"Processing {filepath.name}...")

    with open(filepath, 'r') as f:
        content = f.read()

    original_content = content
    changes = []

    # Fix 1: Database connection strings
    # Wrong: port=5432, database="course_management_db", user="admin", password="admin123"
    # Right: port=5433, database="course_creator", user="postgres", password="postgres_password"
    if 'port=5432' in content or 'port": 5432' in content:
        content = content.replace('port=5432', 'port=5433')
        content = content.replace('port": 5432', 'port": 5433')
        changes.append("Fixed database port 5432 -> 5433")

    if 'database="course_management_db"' in content or 'database": "course_management_db"' in content:
        content = content.replace('database="course_management_db"', 'database="course_creator"')
        content = content.replace('database": "course_management_db"', 'database": "course_creator"')
        changes.append("Fixed database name course_management_db -> course_creator")

    if 'user="admin"' in content or 'user": "admin"' in content:
        content = content.replace('user="admin"', 'user="postgres"')
        content = content.replace('user": "admin"', 'user": "postgres"')
        changes.append("Fixed database user admin -> postgres")

    if 'password="admin123"' in content or 'password": "admin123"' in content:
        content = content.replace('password="admin123"', 'password="postgres_password"')
        content = content.replace('password": "admin123"', 'password": "postgres_password"')
        changes.append("Fixed database password admin123 -> postgres_password")

    if 'password="postgres"' in content and 'postgres_password' not in content:
        content = content.replace('password="postgres"', 'password="postgres_password"')
        changes.append("Fixed database password postgres -> postgres_password")

    # Fix 2: Page Object instantiations missing config parameter
    # Pattern: SomePage(driver) or SomePage(self.driver)
    # Should be: SomePage(driver, config) or SomePage(self.driver, self.config)

    # Fix patterns like: SomePage(driver) -> SomePage(driver, config) or SomePage(self.driver, self.config)
    page_classes = [
        'InstructorLoginPage', 'CourseVersioningPage', 'VersionComparisonPage', 'VersionMigrationPage',
        'CourseCloningPage', 'CloneCustomizationPage', 'CloneValidationPage',
        'LoginPage', 'CourseDeletionPage', 'DeletionWarningModal', 'ArchiveVerificationPage',
        'CourseSearchPage', 'CourseFiltersPage', 'CourseListPage'
    ]

    for page_class in page_classes:
        # Pattern 1: PageClass(driver)  -> PageClass(driver, config)
        pattern1 = f'{page_class}\\(driver\\)'
        replacement1 = f'{page_class}(driver, config)'
        if pattern1 in content:
            content = re.sub(pattern1, replacement1, content)
            changes.append(f"Fixed {page_class}(driver) -> {page_class}(driver, config)")

        # Pattern 2: PageClass(self.driver) without self.config -> PageClass(self.driver, self.config)
        pattern2 = f'{page_class}\\(self\\.driver\\)(?!,)'
        replacement2 = f'{page_class}(self.driver, self.config)'
        count = len(re.findall(pattern2, content))
        if count > 0:
            content = re.sub(pattern2, replacement2, content)
            changes.append(f"Fixed {page_class}(self.driver) -> {page_class}(self.driver, self.config) ({count} occurrences)")

    # Fix 3: Test method signatures - remove driver parameter when inheriting from BaseTest
    # Pattern: def test_XX_something(self, driver): -> def test_XX_something(self):
    pattern = r'(def test_\w+)\(self, driver\):'
    count = len(re.findall(pattern, content))
    if count > 0:
        content = re.sub(pattern, r'\1(self):', content)
        changes.append(f"Removed driver parameter from {count} test methods")

    # Fix 4: Variable references when they should use self
    # This is trickier - we need to be careful not to break local variables
    # Only fix in specific contexts where we know it should be self.

    # Pattern: login_page = SomePage(...) at start of test method should become self.login_page
    # But this is complex - skip for now and handle in setup_pages fixture

    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"  ✅ Updated {filepath.name}")
        for change in changes:
            print(f"    - {change}")
        return True
    else:
        print(f"  ⏭️  No changes needed for {filepath.name}")
        return False

def main():
    test_dir = Path("/home/bbrelin/course-creator/tests/e2e/course_management")
    test_files = [
        "test_course_versioning.py",
        "test_course_cloning.py",
        "test_course_deletion_cascade.py",
        "test_course_search_filters.py"
    ]

    updated_count = 0
    for filename in test_files:
        filepath = test_dir / filename
        if filepath.exists():
            if fix_test_file(filepath):
                updated_count += 1
        else:
            print(f"❌ File not found: {filepath}")

    print(f"\n{'='*60}")
    print(f"Summary: Updated {updated_count}/{len(test_files)} files")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
