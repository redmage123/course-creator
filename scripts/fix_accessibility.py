#!/usr/bin/env python3
"""
Phase 1 Critical Accessibility Fixes Automation Script
Systematically applies P0 accessibility fixes to all HTML files
"""

import re
import os
from pathlib import Path

# Files to process
HTML_FILES = [
    "admin.html",
    "instructor-dashboard.html",
    "lab.html",
    "lab-multi-ide.html",
    "org-admin-dashboard.html",
    "organization-registration.html",
    "password-change.html",
    "project-dashboard.html",
    "quiz.html",
    "site-admin-dashboard.html",
    "student-dashboard.html",
]

BASE_DIR = Path("/home/bbrelin/course-creator/frontend/html")

def fix_skip_link(content):
    """Add skip navigation link after <body> tag if not present"""
    if 'skip-link' in content:
        return content, False

    # Pattern to match <body> with optional attributes
    pattern = r'(<body[^>]*>)'
    replacement = r'\1\n    <a href="#main-content" class="skip-link">Skip to main content</a>'

    new_content = re.sub(pattern, replacement, content, count=1)
    return new_content, (new_content != content)

def fix_aria_live_region(content):
    """Add ARIA live region for form announcements after <body> tag"""
    if 'form-announcements' in content:
        return content, False

    # Add after skip-link if present, otherwise after body
    if 'skip-link' in content:
        pattern = r'(class="skip-link">Skip to main content</a>)'
        replacement = r'\1\n    <div aria-live="polite" aria-atomic="true" class="sr-only" id="form-announcements"></div>'
    else:
        pattern = r'(<body[^>]*>)'
        replacement = r'\1\n    <div aria-live="polite" aria-atomic="true" class="sr-only" id="form-announcements"></div>'

    new_content = re.sub(pattern, replacement, content, count=1)
    return new_content, (new_content != content)

def fix_header_semantics(content):
    """Add role="banner" to <header> tags"""
    # Match <header> without role attribute
    pattern = r'<header(?!\s+role)([^>]*)>'
    replacement = r'<header role="banner"\1>'

    new_content = re.sub(pattern, replacement, content)
    return new_content, (new_content != content)

def fix_nav_semantics(content):
    """Add role="navigation" and aria-label to <nav> tags"""
    # Match <nav> without proper ARIA attributes
    pattern = r'<nav\s+class="([^"]*)"(?!\s+role)([^>]*)>'
    replacement = r'<nav class="\1" role="navigation" aria-label="Main navigation"\2>'

    new_content = re.sub(pattern, replacement, content)

    # Also fix standalone nav tags
    pattern2 = r'<nav(?!\s+role)(?!\s+class)>'
    replacement2 = r'<nav role="navigation" aria-label="Main navigation">'
    new_content = re.sub(pattern2, replacement2, new_content)

    return new_content, (new_content != content)

def fix_main_semantics(content):
    """Add role="main" to <main> tags or wrap content in <main> if needed"""
    # If <main> exists but lacks role
    if '<main' in content and 'role="main"' not in content:
        pattern = r'<main\s+id="([^"]*)"([^>]*)>'
        replacement = r'<main id="\1" role="main"\2>'
        content = re.sub(pattern, replacement, content)

        # Also fix <main> without id
        pattern2 = r'<main(?!\s+role)([^>]*)>'
        replacement2 = r'<main role="main"\1>'
        content = re.sub(pattern2, replacement2, content)
        return content, True

    return content, False

def fix_sidebar_button_keyboard(content):
    """Add keyboard support to sidebar toggle buttons"""
    # Look for sidebar-toggle buttons without proper keyboard attributes
    pattern = r'<button\s+class="sidebar-toggle"\s+onclick="([^"]*)"([^>]*)>'
    replacement = r'<button class="sidebar-toggle" type="button" onclick="\1" onkeypress="if(event.key===\'Enter\'||event.key===\' \')\1"\2>'

    new_content = re.sub(pattern, replacement, content)
    return new_content, (new_content != content)

def fix_error_message_aria(content):
    """Add ARIA roles to error/success message divs"""
    # Fix error messages
    pattern = r'<div\s+id="errorMessage"([^>]*)(?!role)>'
    replacement = r'<div id="errorMessage"\1 role="alert" aria-live="assertive">'
    content = re.sub(pattern, replacement, content)

    # Fix success messages
    pattern = r'<div\s+id="successMessage"([^>]*)(?!role)>'
    replacement = r'<div id="successMessage"\1 role="alert" aria-live="assertive">'
    content = re.sub(pattern, replacement, content)

    return content, True

def apply_fixes(filepath):
    """Apply all accessibility fixes to a file"""
    print(f"\n{'='*60}")
    print(f"Processing: {filepath.name}")
    print(f"{'='*60}")

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content
    fixes_applied = []

    # Apply each fix
    content, changed = fix_skip_link(content)
    if changed:
        fixes_applied.append("✓ Added skip navigation link")

    content, changed = fix_aria_live_region(content)
    if changed:
        fixes_applied.append("✓ Added ARIA live region for form announcements")

    content, changed = fix_header_semantics(content)
    if changed:
        fixes_applied.append("✓ Fixed header semantic role")

    content, changed = fix_nav_semantics(content)
    if changed:
        fixes_applied.append("✓ Fixed nav semantic roles and ARIA labels")

    content, changed = fix_main_semantics(content)
    if changed:
        fixes_applied.append("✓ Fixed main semantic role")

    content, changed = fix_sidebar_button_keyboard(content)
    if changed:
        fixes_applied.append("✓ Added keyboard support to sidebar toggle")

    content, changed = fix_error_message_aria(content)
    if changed:
        fixes_applied.append("✓ Added ARIA roles to error/success messages")

    # Write back if changes were made
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"\n{len(fixes_applied)} fixes applied:")
        for fix in fixes_applied:
            print(f"  {fix}")
    else:
        print("  No changes needed (already compliant)")

    return len(fixes_applied)

def main():
    """Main execution"""
    print("="*60)
    print("Phase 1 Critical Accessibility Fixes")
    print("="*60)

    total_fixes = 0
    files_modified = 0

    for filename in HTML_FILES:
        filepath = BASE_DIR / filename
        if filepath.exists():
            fixes_count = apply_fixes(filepath)
            if fixes_count > 0:
                files_modified += 1
                total_fixes += fixes_count
        else:
            print(f"\n⚠ File not found: {filepath}")

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Files processed: {len(HTML_FILES)}")
    print(f"Files modified: {files_modified}")
    print(f"Total fixes applied: {total_fixes}")
    print("="*60)

if __name__ == "__main__":
    main()
