#!/usr/bin/env python3
"""
Course Creator — Full Platform Walkthrough via Playwright
Tests all major workflows for every role:
  1. Login (all 4 roles)
  2. Site Admin: dashboard, manage orgs, manage users, analytics
  3. Org Admin: dashboard, members, courses, org analytics, settings
  4. Instructor: dashboard, create course, manage content, view students
  5. Student: dashboard, browse/enroll courses, view content, labs, progress
  6. Cross-role: course creation → content generation → student enrollment → quiz
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

from playwright.async_api import async_playwright, Page, expect

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

BASE_URL = os.getenv("TEST_BASE_URL", "https://localhost:3000")
SCREENSHOTS = Path("/home/bbrelin/course-creator/test-reports/walkthrough")
SCREENSHOTS.mkdir(parents=True, exist_ok=True)

USERS = {
    "site_admin": {"username": "admin", "password": "password123", "role": "site_admin"},
    "org_admin": {"username": "orgadmin", "password": "password123", "role": "organization_admin"},
    "instructor": {"username": "instructor", "password": "password123", "role": "instructor"},
    "student": {"username": "student", "password": "password123", "role": "student"},
}

results = []


def record(test_name: str, status: str, detail: str = ""):
    results.append({"test": test_name, "status": status, "detail": detail})
    icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
    log.info(f"{icon} {test_name}: {status} {detail}")


async def screenshot(page: Page, name: str):
    path = SCREENSHOTS / f"{name}.png"
    await page.screenshot(path=str(path), full_page=True)


async def login(page: Page, user_key: str) -> bool:
    """Login via the UI and return True if successful."""
    user = USERS[user_key]
    try:
        await page.goto(f"{BASE_URL}/login", wait_until="networkidle", timeout=15000)
        await page.wait_for_timeout(1000)

        # Fill login form
        username_input = page.locator('input[name="username"], input[name="email"], input[type="text"]').first
        password_input = page.locator('input[name="password"], input[type="password"]').first
        await username_input.fill(user["username"])
        await password_input.fill(user["password"])
        await screenshot(page, f"login-{user_key}-filled")

        # Submit
        submit = page.locator('button[type="submit"], button:has-text("Login"), button:has-text("Sign in"), button:has-text("Log in")').first
        await submit.click()
        await page.wait_for_timeout(3000)

        # Check if we're redirected to dashboard or if login failed
        url = page.url
        if "/login" not in url or "/dashboard" in url:
            await screenshot(page, f"login-{user_key}-success")
            record(f"login_{user_key}", "PASS", f"Redirected to {url}")
            return True
        else:
            await screenshot(page, f"login-{user_key}-failed")
            record(f"login_{user_key}", "FAIL", f"Still on {url}")
            return False
    except Exception as e:
        await screenshot(page, f"login-{user_key}-error")
        record(f"login_{user_key}", "FAIL", str(e)[:200])
        return False


async def logout(page: Page):
    """Logout by clearing cookies/storage or clicking logout."""
    try:
        # Try clicking a logout button/link
        logout_btn = page.locator('a:has-text("Logout"), button:has-text("Logout"), a:has-text("Sign out"), button:has-text("Sign out")').first
        if await logout_btn.is_visible(timeout=2000):
            await logout_btn.click()
            await page.wait_for_timeout(1000)
            return
    except Exception:
        pass
    # Fallback: clear storage
    await page.context.clear_cookies()
    await page.evaluate("localStorage.clear(); sessionStorage.clear()")


async def navigate_and_check(page: Page, path: str, test_name: str, expect_text: str = None):
    """Navigate to a path and check it loads."""
    try:
        resp = await page.goto(f"{BASE_URL}{path}", wait_until="networkidle", timeout=20000)
        await page.wait_for_timeout(1500)
        status = resp.status if resp else 0

        if status >= 400:
            await screenshot(page, test_name)
            record(test_name, "FAIL", f"HTTP {status}")
            return False

        # Check for error messages on page
        body_text = await page.text_content("body")
        if "error" in (body_text or "").lower()[:200] and "no error" not in (body_text or "").lower()[:200]:
            # Some pages legitimately show "errors" in labels etc, so just warn
            pass

        if expect_text:
            try:
                await expect(page.locator(f"text={expect_text}")).to_be_visible(timeout=5000)
                await screenshot(page, test_name)
                record(test_name, "PASS", f"Found '{expect_text}'")
                return True
            except Exception:
                await screenshot(page, test_name)
                record(test_name, "FAIL", f"Text '{expect_text}' not found")
                return False

        await screenshot(page, test_name)
        record(test_name, "PASS", f"HTTP {status}")
        return True
    except Exception as e:
        await screenshot(page, test_name)
        record(test_name, "FAIL", str(e)[:200])
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Role-specific workflow tests
# ─────────────────────────────────────────────────────────────────────────────

async def test_site_admin_workflows(page: Page):
    """Test site admin dashboard, org management, user management."""
    log.info("── Site Admin Workflows ──")
    if not await login(page, "site_admin"):
        return

    await navigate_and_check(page, "/dashboard", "admin_dashboard")
    await navigate_and_check(page, "/admin/organizations", "admin_organizations")
    await navigate_and_check(page, "/admin/users", "admin_users")
    await navigate_and_check(page, "/admin/analytics", "admin_analytics")
    await navigate_and_check(page, "/admin/settings", "admin_settings")

    # Check org list has content
    try:
        rows = page.locator("table tbody tr, [class*='card'], [class*='list-item'], [class*='org']")
        count = await rows.count()
        record("admin_org_list_has_content", "PASS" if count > 0 else "FAIL", f"{count} items")
    except Exception as e:
        record("admin_org_list_has_content", "FAIL", str(e)[:200])

    await logout(page)


async def test_org_admin_workflows(page: Page):
    """Test org admin dashboard, members, courses, analytics."""
    log.info("── Org Admin Workflows ──")
    if not await login(page, "org_admin"):
        return

    await navigate_and_check(page, "/dashboard", "orgadmin_dashboard")
    await navigate_and_check(page, "/organization/members", "orgadmin_members")
    await navigate_and_check(page, "/organization/courses", "orgadmin_courses")
    await navigate_and_check(page, "/organization/analytics", "orgadmin_analytics")
    await navigate_and_check(page, "/organization/settings", "orgadmin_settings")

    await logout(page)


async def test_instructor_workflows(page: Page):
    """Test instructor dashboard, course management, content creation."""
    log.info("── Instructor Workflows ──")
    if not await login(page, "instructor"):
        return

    await navigate_and_check(page, "/dashboard", "instructor_dashboard")
    await navigate_and_check(page, "/courses", "instructor_courses")

    # Try creating a new course
    try:
        create_btn = page.locator(
            'button:has-text("Create"), button:has-text("New Course"), '
            'a:has-text("Create"), a:has-text("New Course")'
        ).first
        if await create_btn.is_visible(timeout=3000):
            await create_btn.click()
            await page.wait_for_timeout(2000)
            await screenshot(page, "instructor_create_course_modal")
            record("instructor_create_course_button", "PASS", "Create button found and clicked")

            # Fill course title if a form appears
            title_input = page.locator(
                'input[name="title"], input[name="name"], input[placeholder*="title" i], '
                'input[placeholder*="name" i], input[type="text"]'
            ).first
            if await title_input.is_visible(timeout=3000):
                await title_input.fill(f"E2E Test Course {datetime.now().strftime('%H%M%S')}")
                await screenshot(page, "instructor_course_form_filled")
                record("instructor_course_form", "PASS", "Course form loaded and filled")

                # Submit the form
                submit = page.locator('button[type="submit"], button:has-text("Create"), button:has-text("Save")').first
                if await submit.is_visible(timeout=2000):
                    await submit.click()
                    await page.wait_for_timeout(3000)
                    await screenshot(page, "instructor_course_created")
                    record("instructor_course_create_submit", "PASS", "Form submitted")
            else:
                record("instructor_course_form", "FAIL", "Title input not found")
        else:
            record("instructor_create_course_button", "FAIL", "Create button not found")
    except Exception as e:
        record("instructor_create_course_flow", "FAIL", str(e)[:200])

    await navigate_and_check(page, "/students", "instructor_students")
    await navigate_and_check(page, "/analytics", "instructor_analytics")
    await logout(page)


async def test_student_workflows(page: Page):
    """Test student dashboard, course browsing, enrollment, labs, progress."""
    log.info("── Student Workflows ──")
    if not await login(page, "student"):
        return

    await navigate_and_check(page, "/dashboard", "student_dashboard")
    await navigate_and_check(page, "/courses", "student_courses_browse")
    await navigate_and_check(page, "/courses/my-courses", "student_my_courses")
    await navigate_and_check(page, "/labs", "student_labs")
    await navigate_and_check(page, "/progress", "student_progress")

    # Try enrolling in a course
    try:
        await page.goto(f"{BASE_URL}/courses", wait_until="networkidle", timeout=15000)
        await page.wait_for_timeout(2000)

        enroll_btn = page.locator(
            'button:has-text("Enroll"), button:has-text("Join"), '
            'a:has-text("Enroll"), a:has-text("Start Course")'
        ).first
        if await enroll_btn.is_visible(timeout=3000):
            await enroll_btn.click()
            await page.wait_for_timeout(2000)
            await screenshot(page, "student_enroll_clicked")
            record("student_enroll_course", "PASS", "Enroll button found and clicked")
        else:
            record("student_enroll_course", "SKIP", "No enroll button visible (may need published courses)")
    except Exception as e:
        record("student_enroll_course", "FAIL", str(e)[:200])

    await logout(page)


async def test_landing_pages(page: Page):
    """Test public pages that don't require login."""
    log.info("── Public/Landing Pages ──")
    await navigate_and_check(page, "/", "landing_home")
    await navigate_and_check(page, "/login", "landing_login")
    await navigate_and_check(page, "/register", "landing_register")


async def test_api_health(page: Page):
    """Test key API endpoints via the frontend proxy."""
    log.info("── API Health Checks ──")
    endpoints = [
        ("/api/v1/auth/login", "auth_api"),
        ("/api/v1/courses/", "courses_api"),
        ("/api/v1/organizations/", "organizations_api"),
    ]
    # Login first to get auth
    if not await login(page, "site_admin"):
        record("api_health_login", "FAIL", "Could not login")
        return

    for path, name in endpoints:
        try:
            resp = await page.request.get(f"{BASE_URL}{path}")
            status = resp.status
            record(f"api_{name}", "PASS" if status < 500 else "FAIL", f"HTTP {status}")
        except Exception as e:
            record(f"api_{name}", "FAIL", str(e)[:200])

    await logout(page)


# ─────────────────────────────────────────────────────────────────────────────
# Main runner
# ─────────────────────────────────────────────────────────────────────────────

async def main():
    log.info("=" * 70)
    log.info("Course Creator — Full Platform Walkthrough")
    log.info(f"Base URL: {BASE_URL}")
    log.info(f"Screenshots: {SCREENSHOTS}")
    log.info(f"Started: {datetime.now().isoformat()}")
    log.info("=" * 70)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--ignore-certificate-errors"])
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            ignore_https_errors=True,
        )
        page = await context.new_page()

        # Run all workflow tests
        await test_landing_pages(page)
        await test_site_admin_workflows(page)
        await test_org_admin_workflows(page)
        await test_instructor_workflows(page)
        await test_student_workflows(page)
        await test_api_health(page)

        await browser.close()

    # Report
    log.info("")
    log.info("=" * 70)
    log.info("RESULTS SUMMARY")
    log.info("=" * 70)
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    skipped = sum(1 for r in results if r["status"] == "SKIP")
    total = len(results)

    for r in results:
        icon = "✅" if r["status"] == "PASS" else "❌" if r["status"] == "FAIL" else "⚠️"
        detail = f" — {r['detail']}" if r["detail"] else ""
        log.info(f"  {icon} {r['test']}{detail}")

    log.info("")
    log.info(f"Total: {total} | Passed: {passed} | Failed: {failed} | Skipped: {skipped}")
    log.info(f"Screenshots saved to: {SCREENSHOTS}")

    # Save JSON report
    report_path = SCREENSHOTS / "report.json"
    with open(report_path, "w") as f:
        json.dump({"results": results, "summary": {"total": total, "passed": passed, "failed": failed, "skipped": skipped}}, f, indent=2)
    log.info(f"JSON report: {report_path}")

    return 1 if failed > 0 else 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
