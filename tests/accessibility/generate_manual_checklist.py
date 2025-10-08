#!/usr/bin/env python3
"""
Generate Interactive Manual Test Checklist
Creates a markdown checklist for manual accessibility testing
"""

import os
from datetime import datetime

pages = [
    "index.html",
    "register.html",
    "student-login.html",
    "student-dashboard.html",
    "instructor-dashboard.html",
    "org-admin-dashboard.html",
    "site-admin-dashboard.html",
    "admin.html",
    "quiz.html",
    "lab.html",
    "lab-multi-ide.html",
    "password-change.html",
    "organization-registration.html",
    "project-dashboard.html",
]

test_categories = {
    "Skip Link": ["Appears on Tab", "Has Focus", "Works Correctly"],
    "Focus Indicators": ["All Links", "All Buttons", "All Inputs", "Custom Controls"],
    "Keyboard Navigation": ["Tab Order Logical", "No Focus Traps", "Modal Focus Trap Works"],
}

output_file = "tests/accessibility/results/MANUAL_TEST_CHECKLIST.md"

# Ensure directory exists
os.makedirs(os.path.dirname(output_file), exist_ok=True)

with open(output_file, 'w') as f:
    f.write(f"# Manual Accessibility Test Checklist\n\n")
    f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"**Tester:** _____________________\n\n")
    f.write(f"---\n\n")

    f.write(f"## Instructions\n\n")
    f.write(f"- Check the box when test passes: ✅\n")
    f.write(f"- Mark with ❌ if test fails\n")
    f.write(f"- Add notes in the Notes column\n\n")
    f.write(f"---\n\n")

    for category, tests in test_categories.items():
        f.write(f"## {category} Testing\n\n")

        # Create table header
        f.write(f"| Page | ")
        for test in tests:
            f.write(f"{test} | ")
        f.write(f"Notes |\n")

        # Table separator
        f.write(f"|------|")
        for _ in tests:
            f.write(f"--------|")
        f.write(f"-------|\n")

        # Table rows for each page
        for page in pages:
            f.write(f"| {page} | ")
            for _ in tests:
                f.write(f"☐ | ")
            f.write(f" |\n")

        f.write(f"\n")

    f.write(f"---\n\n")
    f.write(f"## Summary\n\n")
    f.write(f"**Total Pages Tested:** _____ / {len(pages)}\n")
    f.write(f"**Tests Passed:** _____\n")
    f.write(f"**Tests Failed:** _____\n")
    f.write(f"**Issues Found:** _____\n\n")
    f.write(f"**Overall Status:** [ ] PASS  [ ] FAIL\n\n")

print(f"✅ Manual test checklist generated: {output_file}")
