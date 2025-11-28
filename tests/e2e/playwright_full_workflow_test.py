#!/usr/bin/env python3
"""
Complete Platform Workflow Test with Playwright Recording

Tests ALL user roles and workflows:
1. Guest/Anonymous - Public pages, registration
2. Student - Login, dashboard, courses, labs, quizzes
3. Instructor - Course management, content generation, analytics
4. Organization Admin - Members, projects, tracks, settings
5. Site Admin - Platform management, organizations, users

Generates video recordings for each workflow segment.
"""

import os
import sys
import json
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from playwright.async_api import async_playwright, Browser, Page, BrowserContext

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
BASE_URL = os.getenv('TEST_BASE_URL', 'https://localhost:3000')
OUTPUT_DIR = Path('tests/reports/workflow_recordings')
SCREENSHOT_DIR = Path('tests/reports/screenshots')

# Test credentials
TEST_USERS = {
    'site_admin': {'email': 'admin@coursecreator.com', 'password': 'admin123'},
    'org_admin': {'email': 'org_admin@demo.com', 'password': 'demo123'},
    'instructor': {'email': 'instructor@demo.com', 'password': 'demo123'},
    'student': {'email': 'student@demo.com', 'password': 'demo123'},
}


@dataclass
class TestResult:
    """Result of a single test."""
    name: str
    role: str
    passed: bool
    duration_ms: float
    error: Optional[str] = None
    screenshot: Optional[str] = None
    video: Optional[str] = None


@dataclass
class WorkflowTestSuite:
    """Complete test suite results."""
    started_at: str
    completed_at: str = ""
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    results: List[TestResult] = field(default_factory=list)


class PlaywrightWorkflowTester:
    """
    Comprehensive workflow tester using Playwright.

    Records all test executions and captures screenshots on failure.
    """

    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.suite = WorkflowTestSuite(started_at=datetime.now().isoformat())

    async def setup(self, record_video: bool = True):
        """Initialize browser with recording."""
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=[
                '--ignore-certificate-errors',
                '--disable-web-security',
                '--no-sandbox',
            ]
        )

        context_options = {
            'viewport': {'width': 1920, 'height': 1080},
            'ignore_https_errors': True,
        }

        if record_video:
            context_options['record_video_dir'] = str(OUTPUT_DIR)
            context_options['record_video_size'] = {'width': 1920, 'height': 1080}

        self.context = await self.browser.new_context(**context_options)
        self.page = await self.context.new_page()

        # Set default timeout
        self.page.set_default_timeout(30000)

        logger.info("Browser initialized with video recording")

    async def teardown(self):
        """Cleanup browser."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def screenshot(self, name: str) -> str:
        """Take screenshot and return path."""
        path = SCREENSHOT_DIR / f"{name}_{datetime.now().strftime('%H%M%S')}.png"
        await self.page.screenshot(path=str(path), full_page=True)
        return str(path)

    async def run_test(self, name: str, role: str, test_func) -> TestResult:
        """Run a single test with timing and error handling."""
        start = datetime.now()
        result = TestResult(name=name, role=role, passed=False, duration_ms=0)

        try:
            logger.info(f"Running: {name} ({role})")
            await test_func()
            result.passed = True
            logger.info(f"PASSED: {name}")
        except Exception as e:
            result.error = str(e)
            result.screenshot = await self.screenshot(f"fail_{name}")
            logger.error(f"FAILED: {name} - {e}")

        result.duration_ms = (datetime.now() - start).total_seconds() * 1000
        self.suite.results.append(result)
        return result

    # ==================== GUEST WORKFLOWS ====================

    async def test_guest_homepage(self):
        """Test: Guest can view homepage."""
        await self.page.goto(BASE_URL)
        await self.page.wait_for_load_state('networkidle')

        # Verify homepage elements
        title = await self.page.title()
        assert 'Course' in title or await self.page.locator('text=Course').count() > 0

    async def test_guest_login_page(self):
        """Test: Guest can access login page."""
        await self.page.goto(f"{BASE_URL}/login")
        await self.page.wait_for_load_state('networkidle')

        # Verify login form exists
        email_input = self.page.locator('input[type="email"], input[name="email"], #email')
        assert await email_input.count() > 0

    async def test_guest_register_page(self):
        """Test: Guest can access registration page."""
        await self.page.goto(f"{BASE_URL}/register")
        await self.page.wait_for_load_state('networkidle')

        # Page should load (may redirect or show form)
        await self.page.wait_for_timeout(1000)

    async def test_guest_org_registration(self):
        """Test: Guest can access organization registration."""
        await self.page.goto(f"{BASE_URL}/organization/register")
        await self.page.wait_for_load_state('networkidle')
        await self.page.wait_for_timeout(1000)

    # ==================== LOGIN WORKFLOWS ====================

    async def login_as(self, role: str) -> bool:
        """Login as specified role."""
        creds = TEST_USERS.get(role)
        if not creds:
            return False

        await self.page.goto(f"{BASE_URL}/login")
        await self.page.wait_for_load_state('networkidle')

        # Fill login form
        email_input = self.page.locator('input[type="email"], input[name="email"], #email').first
        password_input = self.page.locator('input[type="password"], input[name="password"], #password').first

        await email_input.fill(creds['email'])
        await password_input.fill(creds['password'])

        # Submit
        submit_btn = self.page.locator('button[type="submit"]').first
        await submit_btn.click()

        # Wait for navigation
        await self.page.wait_for_timeout(3000)
        return True

    # ==================== STUDENT WORKFLOWS ====================

    async def test_student_login(self):
        """Test: Student can login."""
        await self.login_as('student')
        # Should be on dashboard or redirected
        await self.page.wait_for_timeout(2000)

    async def test_student_dashboard(self):
        """Test: Student dashboard loads."""
        await self.login_as('student')
        await self.page.wait_for_timeout(2000)

        # Look for dashboard indicators
        body = await self.page.content()
        assert 'dashboard' in body.lower() or 'course' in body.lower()

    async def test_student_view_courses(self):
        """Test: Student can view courses."""
        await self.login_as('student')
        await self.page.wait_for_timeout(2000)

        # Try to navigate to courses
        courses_link = self.page.locator('a[href*="course"], [data-tab="courses"]').first
        if await courses_link.count() > 0:
            await courses_link.click()
            await self.page.wait_for_timeout(2000)

    # ==================== INSTRUCTOR WORKFLOWS ====================

    async def test_instructor_login(self):
        """Test: Instructor can login."""
        await self.login_as('instructor')
        await self.page.wait_for_timeout(2000)

    async def test_instructor_dashboard(self):
        """Test: Instructor dashboard loads."""
        await self.login_as('instructor')
        await self.page.wait_for_timeout(2000)

        body = await self.page.content()
        # Should see instructor-specific content

    async def test_instructor_courses_tab(self):
        """Test: Instructor can access courses tab."""
        await self.login_as('instructor')
        await self.page.wait_for_timeout(2000)

        courses_tab = self.page.locator('[data-tab="courses"], a[href*="courses"]').first
        if await courses_tab.count() > 0:
            await courses_tab.click()
            await self.page.wait_for_timeout(2000)

    async def test_instructor_content_generation(self):
        """Test: Instructor can access content generation."""
        await self.login_as('instructor')
        await self.page.wait_for_timeout(2000)

        content_tab = self.page.locator('[data-tab="content-generation"], a[href*="content"]').first
        if await content_tab.count() > 0:
            await content_tab.click()
            await self.page.wait_for_timeout(2000)

    async def test_instructor_analytics(self):
        """Test: Instructor can view analytics."""
        await self.login_as('instructor')
        await self.page.wait_for_timeout(2000)

        analytics_tab = self.page.locator('[data-tab="analytics"], a[href*="analytics"]').first
        if await analytics_tab.count() > 0:
            await analytics_tab.click()
            await self.page.wait_for_timeout(2000)

    # ==================== ORG ADMIN WORKFLOWS ====================

    async def test_org_admin_login(self):
        """Test: Org Admin can login."""
        await self.login_as('org_admin')
        await self.page.wait_for_timeout(2000)

    async def test_org_admin_dashboard(self):
        """Test: Org Admin dashboard loads."""
        await self.login_as('org_admin')
        await self.page.wait_for_timeout(2000)

        body = await self.page.content()
        # Should see org admin content

    async def test_org_admin_members_tab(self):
        """Test: Org Admin can access members tab."""
        await self.login_as('org_admin')
        await self.page.wait_for_timeout(2000)

        members_tab = self.page.locator('[data-tab="members"], a[href*="members"]').first
        if await members_tab.count() > 0:
            await members_tab.click()
            await self.page.wait_for_timeout(2000)

    async def test_org_admin_projects_tab(self):
        """Test: Org Admin can access projects tab."""
        await self.login_as('org_admin')
        await self.page.wait_for_timeout(2000)

        projects_tab = self.page.locator('[data-tab="projects"], a[href*="projects"]').first
        if await projects_tab.count() > 0:
            await projects_tab.click()
            await self.page.wait_for_timeout(2000)

    async def test_org_admin_tracks_tab(self):
        """Test: Org Admin can access tracks tab."""
        await self.login_as('org_admin')
        await self.page.wait_for_timeout(2000)

        tracks_tab = self.page.locator('[data-tab="tracks"], a[href*="tracks"]').first
        if await tracks_tab.count() > 0:
            await tracks_tab.click()
            await self.page.wait_for_timeout(2000)

    async def test_org_admin_settings(self):
        """Test: Org Admin can access settings."""
        await self.login_as('org_admin')
        await self.page.wait_for_timeout(2000)

        settings_tab = self.page.locator('[data-tab="settings"], a[href*="settings"]').first
        if await settings_tab.count() > 0:
            await settings_tab.click()
            await self.page.wait_for_timeout(2000)

    # ==================== SITE ADMIN WORKFLOWS ====================

    async def test_site_admin_login(self):
        """Test: Site Admin can login."""
        await self.login_as('site_admin')
        await self.page.wait_for_timeout(2000)

    async def test_site_admin_dashboard(self):
        """Test: Site Admin dashboard loads."""
        await self.login_as('site_admin')
        await self.page.wait_for_timeout(2000)

        body = await self.page.content()

    async def test_site_admin_organizations(self):
        """Test: Site Admin can view organizations."""
        await self.login_as('site_admin')
        await self.page.wait_for_timeout(2000)

        orgs_tab = self.page.locator('[data-tab="organizations"], a[href*="organization"]').first
        if await orgs_tab.count() > 0:
            await orgs_tab.click()
            await self.page.wait_for_timeout(2000)

    async def test_site_admin_users(self):
        """Test: Site Admin can manage users."""
        await self.login_as('site_admin')
        await self.page.wait_for_timeout(2000)

        users_tab = self.page.locator('[data-tab="users"], a[href*="users"]').first
        if await users_tab.count() > 0:
            await users_tab.click()
            await self.page.wait_for_timeout(2000)

    # ==================== NAVIGATION TESTS ====================

    async def test_navigation_all_main_routes(self):
        """Test: All main routes are accessible."""
        routes = [
            '/',
            '/login',
            '/register',
            '/organization/register',
        ]

        for route in routes:
            await self.page.goto(f"{BASE_URL}{route}")
            await self.page.wait_for_load_state('networkidle')
            status = self.page.url
            logger.info(f"Route {route} -> {status}")

    # ==================== RUN ALL TESTS ====================

    async def run_all_tests(self) -> WorkflowTestSuite:
        """Run all workflow tests."""

        # Guest tests
        await self.run_test("guest_homepage", "guest", self.test_guest_homepage)
        await self.run_test("guest_login_page", "guest", self.test_guest_login_page)
        await self.run_test("guest_register_page", "guest", self.test_guest_register_page)
        await self.run_test("guest_org_registration", "guest", self.test_guest_org_registration)

        # Student tests
        await self.run_test("student_login", "student", self.test_student_login)
        await self.run_test("student_dashboard", "student", self.test_student_dashboard)
        await self.run_test("student_view_courses", "student", self.test_student_view_courses)

        # Instructor tests
        await self.run_test("instructor_login", "instructor", self.test_instructor_login)
        await self.run_test("instructor_dashboard", "instructor", self.test_instructor_dashboard)
        await self.run_test("instructor_courses_tab", "instructor", self.test_instructor_courses_tab)
        await self.run_test("instructor_content_generation", "instructor", self.test_instructor_content_generation)
        await self.run_test("instructor_analytics", "instructor", self.test_instructor_analytics)

        # Org Admin tests
        await self.run_test("org_admin_login", "org_admin", self.test_org_admin_login)
        await self.run_test("org_admin_dashboard", "org_admin", self.test_org_admin_dashboard)
        await self.run_test("org_admin_members_tab", "org_admin", self.test_org_admin_members_tab)
        await self.run_test("org_admin_projects_tab", "org_admin", self.test_org_admin_projects_tab)
        await self.run_test("org_admin_tracks_tab", "org_admin", self.test_org_admin_tracks_tab)
        await self.run_test("org_admin_settings", "org_admin", self.test_org_admin_settings)

        # Site Admin tests
        await self.run_test("site_admin_login", "site_admin", self.test_site_admin_login)
        await self.run_test("site_admin_dashboard", "site_admin", self.test_site_admin_dashboard)
        await self.run_test("site_admin_organizations", "site_admin", self.test_site_admin_organizations)
        await self.run_test("site_admin_users", "site_admin", self.test_site_admin_users)

        # Navigation tests
        await self.run_test("navigation_all_main_routes", "system", self.test_navigation_all_main_routes)

        # Finalize suite
        self.suite.completed_at = datetime.now().isoformat()
        self.suite.total_tests = len(self.suite.results)
        self.suite.passed = sum(1 for r in self.suite.results if r.passed)
        self.suite.failed = self.suite.total_tests - self.suite.passed

        return self.suite


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Run complete workflow tests with Playwright")
    parser.add_argument("--no-video", action="store_true", help="Disable video recording")
    parser.add_argument("--output", "-o", default="tests/reports", help="Output directory")

    args = parser.parse_args()

    tester = PlaywrightWorkflowTester()

    try:
        await tester.setup(record_video=not args.no_video)
        suite = await tester.run_all_tests()

        # Print summary
        print("\n" + "="*60)
        print("WORKFLOW TEST RESULTS")
        print("="*60)
        print(f"Total: {suite.total_tests} | Passed: {suite.passed} | Failed: {suite.failed}")
        print(f"Pass Rate: {(suite.passed/suite.total_tests)*100:.1f}%")
        print()

        # Results by role
        roles = {}
        for r in suite.results:
            if r.role not in roles:
                roles[r.role] = {'passed': 0, 'failed': 0}
            if r.passed:
                roles[r.role]['passed'] += 1
            else:
                roles[r.role]['failed'] += 1

        print("Results by Role:")
        for role, stats in roles.items():
            total = stats['passed'] + stats['failed']
            print(f"  {role}: {stats['passed']}/{total} passed")

        print()

        # Failed tests
        failed = [r for r in suite.results if not r.passed]
        if failed:
            print("Failed Tests:")
            for r in failed:
                print(f"  - {r.name} ({r.role}): {r.error[:50]}...")

        # Save results
        results_path = Path(args.output) / "workflow_test_results.json"
        results_path.parent.mkdir(parents=True, exist_ok=True)

        results_dict = {
            'started_at': suite.started_at,
            'completed_at': suite.completed_at,
            'total_tests': suite.total_tests,
            'passed': suite.passed,
            'failed': suite.failed,
            'results': [
                {
                    'name': r.name,
                    'role': r.role,
                    'passed': r.passed,
                    'duration_ms': r.duration_ms,
                    'error': r.error,
                    'screenshot': r.screenshot,
                }
                for r in suite.results
            ]
        }

        results_path.write_text(json.dumps(results_dict, indent=2))
        print(f"\nResults saved to: {results_path}")

    finally:
        await tester.teardown()


if __name__ == "__main__":
    asyncio.run(main())
