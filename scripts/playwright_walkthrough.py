"""
Comprehensive Playwright Walkthrough - Course Creator Platform
Systematically visits every feature area across all user roles.
Takes screenshots and reports findings.
"""

import os
import sys
import json
import time
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

BASE_URL = "https://localhost:3000"
SCREENSHOT_DIR = "/home/bbrelin/course-creator/reports/walkthrough-screenshots"

# Test users (demo credentials - passwords reset to password123)
USERS = {
    "org_admin": {"email": "orgadmin@example.com", "password": "password123"},
    "instructor": {"email": "instructor@example.com", "password": "password123"},
    "student": {"email": "student@example.com", "password": "password123"},
    "site_admin": {"email": "admin@example.com", "password": "password123"},
}

# Results tracking
results = {
    "timestamp": datetime.now().isoformat(),
    "sections": [],
    "summary": {"total": 0, "passed": 0, "failed": 0, "errors": []}
}


def ensure_dirs():
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)


def screenshot(page, name):
    path = os.path.join(SCREENSHOT_DIR, f"{name}.png")
    page.screenshot(path=path, full_page=False)
    return path


# Current auth token for SPA navigation
_current_token = None
_current_user = None


def check_page(page, name, url, expected_elements=None, wait_for=None, is_public=False):
    """Navigate to a page and verify it loads.

    For authenticated pages: Uses SPA navigation to preserve in-memory auth tokens.
    For public pages: Uses standard page.goto().
    """
    result = {"name": name, "url": url, "status": "unknown", "details": ""}
    results["summary"]["total"] += 1

    try:
        if is_public or _current_token is None:
            # Public page - standard navigation
            page.goto(f"{BASE_URL}{url}", wait_until="domcontentloaded", timeout=15000)
        else:
            # Authenticated page - use SPA navigation to preserve in-memory token
            nav_result = page.evaluate("""(url) => {
                // Use React Router's navigate via window.history + popstate
                window.history.pushState({}, '', url);
                window.dispatchEvent(new PopStateEvent('popstate'));
                return {url: window.location.href};
            }""", url)

        time.sleep(1.5)

        # Wait for specific element if specified
        if wait_for:
            try:
                page.wait_for_selector(wait_for, timeout=5000)
            except PlaywrightTimeoutError:
                pass

        # Check page title and content
        title = page.title()
        page_url = page.url

        # Check for error indicators
        page_content = page.content()
        has_error = "Internal Server Error" in page_content or ">500<" in page_content
        has_not_found = (">404<" in page_content or "Page Not Found" in page_content) and "Not Found" not in name

        # Check for redirect to login (indicates auth required or token lost)
        if "/login" in page_url and "/login" not in url:
            result["status"] = "redirect_to_login"
            result["details"] = f"Redirected to login. Final URL: {page_url}"
        elif has_error:
            result["status"] = "error"
            result["details"] = "Page shows 500/Internal Server Error"
        elif has_not_found:
            result["status"] = "not_found"
            result["details"] = "Page shows 404/Not Found"
        else:
            result["status"] = "loaded"
            result["details"] = f"Title: {title}"

        # Take screenshot
        safe_name = name.replace(" ", "_").replace("/", "_").replace("[", "").replace("]", "").lower()
        screenshot(page, safe_name)

        if result["status"] == "loaded":
            results["summary"]["passed"] += 1
        else:
            results["summary"]["failed"] += 1

    except PlaywrightTimeoutError:
        result["status"] = "timeout"
        result["details"] = "Page load timed out (15s)"
        results["summary"]["failed"] += 1
    except Exception as e:
        result["status"] = "error"
        result["details"] = f"Exception: {str(e)[:200]}"
        results["summary"]["failed"] += 1
        results["summary"]["errors"].append(f"{name}: {str(e)[:100]}")

    status_icon = {"loaded": "OK", "redirect_to_login": "REDIRECT", "error": "ERROR",
                   "not_found": "404", "timeout": "TIMEOUT", "unknown": "??"}
    print(f"  [{status_icon.get(result['status'], '??')}] {name} ({url})")
    return result


def login(page, role):
    """Login as a specific role by submitting the login form directly in the SPA."""
    global _current_token, _current_user
    user = USERS.get(role)
    if not user:
        print(f"  [SKIP] No credentials for role: {role}")
        return False

    print(f"\n  Logging in as {role} ({user['email']})...")
    try:
        # Navigate to login page
        page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=15000)
        time.sleep(2)

        # Fill login form using the actual React form and submit it
        # This triggers the SPA's auth flow which sets the in-memory token
        login_result = page.evaluate("""async (creds) => {
            try {
                // Find and fill form fields via DOM
                const inputs = document.querySelectorAll('input');
                let emailInput = null, passwordInput = null;
                for (const inp of inputs) {
                    const type = inp.type || 'text';
                    const placeholder = (inp.placeholder || '').toLowerCase();
                    if (!emailInput && (type === 'text' || type === 'email') && (placeholder.includes('email') || placeholder.includes('username'))) {
                        emailInput = inp;
                    }
                    if (!passwordInput && type === 'password') {
                        passwordInput = inp;
                    }
                }
                if (!emailInput || !passwordInput) {
                    // Fallback: first text and first password
                    for (const inp of inputs) {
                        if (!emailInput && (inp.type === 'text' || inp.type === 'email')) emailInput = inp;
                        if (!passwordInput && inp.type === 'password') passwordInput = inp;
                    }
                }
                if (!emailInput || !passwordInput) return {success: false, error: 'Form fields not found'};

                // Set values using React's nativeInputValueSetter
                const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                    window.HTMLInputElement.prototype, 'value'
                ).set;
                nativeInputValueSetter.call(emailInput, creds.email);
                emailInput.dispatchEvent(new Event('input', { bubbles: true }));
                emailInput.dispatchEvent(new Event('change', { bubbles: true }));

                nativeInputValueSetter.call(passwordInput, creds.password);
                passwordInput.dispatchEvent(new Event('input', { bubbles: true }));
                passwordInput.dispatchEvent(new Event('change', { bubbles: true }));

                // Click submit
                const submitBtn = document.querySelector('button[type="submit"]') ||
                    [...document.querySelectorAll('button')].find(b => /sign in|login|log in/i.test(b.textContent));
                if (submitBtn) {
                    submitBtn.click();
                    return {success: true, submitted: true};
                }
                return {success: false, error: 'Submit button not found'};
            } catch(e) {
                return {success: false, error: e.message};
            }
        }""", {"email": user["email"], "password": user["password"]})

        if not login_result.get("success"):
            print(f"  [FAIL] Form submission failed: {login_result.get('error', 'unknown')}")
            screenshot(page, f"login_fail_{role}")
            return False

        # Wait for navigation after form submit
        time.sleep(4)
        screenshot(page, f"login_result_{role}")

        current_url = page.url
        if "/login" not in current_url:
            print(f"  [OK] Logged in as {role}. URL: {current_url}")
            _current_token = "active"
            return True

        # Check if there's an error message
        error_text = page.evaluate("document.body.innerText")
        if "invalid" in error_text.lower() or "error" in error_text.lower():
            print(f"  [FAIL] Login rejected. Page text contains error.")
            return False

        print(f"  [FAIL] Still on login page. URL: {current_url}")
        return False

    except Exception as e:
        print(f"  [FAIL] Login error: {str(e)[:200]}")
        return False


def logout(page):
    """Logout current user."""
    global _current_token, _current_user
    _current_token = None
    _current_user = None
    try:
        page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=10000)
        page.evaluate("localStorage.clear(); sessionStorage.clear();")
        time.sleep(1)
    except Exception:
        pass


def section(name):
    print(f"\n{'='*60}")
    print(f"  SECTION: {name}")
    print(f"{'='*60}")
    section_results = {"name": name, "pages": []}
    results["sections"].append(section_results)
    return section_results


def run_walkthrough():
    ensure_dirs()
    print(f"\nCourse Creator Platform - Comprehensive Walkthrough")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Base URL: {BASE_URL}")
    print(f"Screenshots: {SCREENSHOT_DIR}")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--ignore-certificate-errors", "--no-sandbox"]
        )
        context = browser.new_context(
            ignore_https_errors=True,
            viewport={"width": 1920, "height": 1080}
        )
        page = context.new_page()

        # ============================================================
        # 1. PUBLIC PAGES (No auth required)
        # ============================================================
        sec = section("PUBLIC PAGES (No Authentication)")

        pages = [
            ("Homepage", "/"),
            ("Login Page", "/login"),
            ("Registration Page", "/register"),
            ("Forgot Password", "/forgot-password"),
            ("Organization Registration", "/organization/register"),
            ("Terms of Service", "/terms"),
            ("Privacy Policy", "/privacy"),
            ("Demo Page", "/demo"),
        ]

        for name, url in pages:
            r = check_page(page, name, url, is_public=True)
            sec["pages"].append(r)

        # ============================================================
        # 2. STUDENT ROLE
        # ============================================================
        sec = section("STUDENT ROLE")

        if login(page, "student"):
            pages = [
                ("Student Dashboard", "/dashboard/student"),
                ("My Courses", "/courses/my-courses"),
                ("Labs List", "/labs"),
                ("Quizzes List", "/quizzes"),
                ("Resources", "/resources"),
                ("Certificates", "/certificates"),
                ("Learning Analytics", "/learning-analytics"),
                ("Progress", "/progress"),
                ("Password Change", "/settings/password"),
                ("Accessibility Settings", "/settings/accessibility"),
                ("Bug Submit", "/bugs/submit"),
                ("My Bugs", "/bugs/my"),
            ]

            for name, url in pages:
                r = check_page(page, f"[Student] {name}", url)
                sec["pages"].append(r)

            logout(page)
        else:
            sec["pages"].append({"name": "Student Login", "status": "login_failed", "details": "Could not login as student"})

        # ============================================================
        # 3. INSTRUCTOR ROLE
        # ============================================================
        sec = section("INSTRUCTOR ROLE")

        if login(page, "instructor"):
            pages = [
                ("Instructor Dashboard", "/dashboard/instructor"),
                ("Training Programs", "/instructor/programs"),
                ("Create Program", "/instructor/programs/create"),
                ("Manage Students", "/instructor/students"),
                ("Enroll Students", "/instructor/students/enroll"),
                ("Bulk Enroll", "/instructor/students/bulk-enroll"),
                ("Instructor Analytics", "/instructor/analytics"),
                ("Content Generator", "/instructor/content-generator"),
                ("Instructor Insights", "/instructor/insights"),
                ("Password Change", "/settings/password"),
                ("Accessibility Settings", "/settings/accessibility"),
                ("Bug Submit", "/bugs/submit"),
            ]

            for name, url in pages:
                r = check_page(page, f"[Instructor] {name}", url)
                sec["pages"].append(r)

            logout(page)
        else:
            sec["pages"].append({"name": "Instructor Login", "status": "login_failed", "details": "Could not login as instructor"})

        # ============================================================
        # 4. ORGANIZATION ADMIN ROLE
        # ============================================================
        sec = section("ORGANIZATION ADMIN ROLE")

        if login(page, "org_admin"):
            pages = [
                ("Org Admin Dashboard", "/dashboard/org-admin"),
                ("Manage Trainers", "/organization/trainers"),
                ("Manage Members", "/organization/members"),
                ("Training Programs", "/organization/programs"),
                ("Tracks", "/organization/tracks"),
                ("Course Create", "/organization/courses/create"),
                ("Org Analytics", "/organization/analytics"),
                ("Organization Settings", "/organization/settings"),
                ("Import Template", "/organization/import"),
                ("AI Create", "/organization/ai-create"),
                ("Integrations Settings", "/organization/integrations"),
                ("Password Change", "/settings/password"),
                ("Accessibility Settings", "/settings/accessibility"),
                ("Bug Submit", "/bugs/submit"),
            ]

            for name, url in pages:
                r = check_page(page, f"[OrgAdmin] {name}", url)
                sec["pages"].append(r)

            logout(page)
        else:
            sec["pages"].append({"name": "OrgAdmin Login", "status": "login_failed", "details": "Could not login as org_admin"})

        # ============================================================
        # 5. SITE ADMIN ROLE
        # ============================================================
        sec = section("SITE ADMIN ROLE")

        if login(page, "site_admin"):
            pages = [
                ("Admin Organizations", "/admin/organizations"),
                ("Create Organization", "/admin/organizations/create"),
                ("Admin Users", "/admin/users"),
                ("Admin Analytics", "/admin/analytics"),
                ("System Settings", "/admin/settings"),
            ]

            for name, url in pages:
                r = check_page(page, f"[SiteAdmin] {name}", url)
                sec["pages"].append(r)

            logout(page)
        else:
            sec["pages"].append({"name": "SiteAdmin Login", "status": "login_failed", "details": "Could not login"})

        # ============================================================
        # 6. API HEALTH CHECKS
        # ============================================================
        sec = section("API HEALTH CHECKS")

        api_endpoints = [
            ("User Management API", "/api/v1/auth/health"),
            ("Course Management API", "/api/v1/courses/health"),
            ("Organization Management API", "/api/v1/organizations/health"),
            ("Content Management API", "/api/v1/content/health"),
            ("Analytics API", "/api/v1/analytics/health"),
            ("RAG Service API", "/api/v1/rag/health"),
            ("Demo Service API", "/api/v1/demo/health"),
        ]

        for name, url in api_endpoints:
            r = check_page(page, name, url, is_public=True)
            sec["pages"].append(r)

        # ============================================================
        # CLEANUP & REPORT
        # ============================================================
        browser.close()

    # Print summary
    print(f"\n{'='*60}")
    print(f"  WALKTHROUGH SUMMARY")
    print(f"{'='*60}")
    print(f"  Total pages checked: {results['summary']['total']}")
    print(f"  Loaded OK:           {results['summary']['passed']}")
    print(f"  Issues:              {results['summary']['failed']}")

    if results["summary"]["errors"]:
        print(f"\n  Errors:")
        for err in results["summary"]["errors"]:
            print(f"    - {err}")

    # Save JSON report
    report_path = os.path.join(SCREENSHOT_DIR, "walkthrough_report.json")
    with open(report_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n  Full report: {report_path}")

    # Save readable report
    readable_path = os.path.join(SCREENSHOT_DIR, "walkthrough_report.txt")
    with open(readable_path, "w") as f:
        f.write(f"Course Creator Platform Walkthrough Report\n")
        f.write(f"{'='*60}\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        for sec_data in results["sections"]:
            f.write(f"\n## {sec_data['name']}\n")
            f.write(f"{'-'*40}\n")
            for pg in sec_data["pages"]:
                status = pg.get("status", "unknown").upper()
                f.write(f"  [{status}] {pg.get('name', 'unknown')} - {pg.get('url', '')}\n")
                if pg.get("details"):
                    for line in pg["details"].split("\n"):
                        f.write(f"           {line}\n")
        f.write(f"\n{'='*60}\n")
        f.write(f"SUMMARY: {results['summary']['passed']}/{results['summary']['total']} pages loaded OK\n")
        f.write(f"Issues: {results['summary']['failed']}\n")
    print(f"  Readable report: {readable_path}")

    # Return exit code
    return 0 if results["summary"]["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(run_walkthrough())
