#!/usr/bin/env python3
"""
Debug Playwright network issues with login
"""
import asyncio
from playwright.async_api import async_playwright

async def debug_network():
    """Debug network behavior in Playwright"""

    print("="*80)
    print("PLAYWRIGHT NETWORK DEBUG")
    print("="*80)

    async with async_playwright() as p:
        # Launch browser with debugging
        browser = await p.chromium.launch(
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--ignore-certificate-errors',  # CLI arg
                '--allow-insecure-localhost',
                '--window-position=0,0',
                '--window-size=1920,1080'
            ]
        )

        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            ignore_https_errors=True,  # Context setting
            accept_downloads=True
        )

        page = await context.new_page()

        # Enable detailed console logging
        page.on('console', lambda msg: print(f"[CONSOLE {msg.type}] {msg.text}"))

        # Log all network requests
        page.on('request', lambda request: print(f"[REQUEST] {request.method} {request.url}"))

        # Log all network responses
        page.on('response', lambda response: print(f"[RESPONSE] {response.status} {response.url}"))

        # Log network failures
        page.on('requestfailed', lambda request: print(f"[FAILED] {request.url} - {request.failure}"))

        print("\n1. Navigating to login page...")
        await page.goto('https://localhost:3000/html/student-login.html',
                       wait_until='networkidle',
                       timeout=30000)
        print("✓ Login page loaded")

        await asyncio.sleep(2)

        print("\n2. Filling in credentials...")
        await page.fill('#email', 'orgadmin@e2etest.com')
        await page.fill('#password', 'org_admin_password')
        print("✓ Credentials filled")

        print("\n3. Getting page state before submit...")
        # Check what the page sees
        origin = await page.evaluate("window.locations.origin")
        print(f"   window.locations.origin: {origin}")

        # Check if fetch is available
        has_fetch = await page.evaluate("typeof fetch === 'function'")
        print(f"   fetch available: {has_fetch}")

        # Try a simple fetch test
        print("\n4. Testing simple fetch to /health endpoint...")
        try:
            test_result = await page.evaluate("""
                async () => {
                    try {
                        const response = await fetch('https://localhost:3000/health', {
                            method: 'GET'
                        });
                        return {
                            ok: response.ok,
                            status: response.status,
                            statusText: response.statusText
                        };
                    } catch (error) {
                        return {
                            error: error.message,
                            name: error.name
                        };
                    }
                }
            """)
            print(f"   Fetch test result: {test_result}")
        except Exception as e:
            print(f"   Fetch test failed: {e}")

        print("\n5. Testing fetch to /auth/login endpoint...")
        try:
            login_test = await page.evaluate("""
                async () => {
                    try {
                        const response = await fetch('https://localhost:3000/auth/login', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                username: 'orgadmin@e2etest.com',
                                password: 'org_admin_password',
                                course_instance_id: null,
                                device_fingerprint: 'test',
                                consent_analytics: false,
                                consent_notifications: false
                            })
                        });
                        const data = await response.json();
                        return {
                            ok: response.ok,
                            status: response.status,
                            statusText: response.statusText,
                            data: data
                        };
                    } catch (error) {
                        return {
                            error: error.message,
                            name: error.name,
                            stack: error.stack
                        };
                    }
                }
            """)
            print(f"   Login fetch result: {login_test}")
        except Exception as e:
            print(f"   Login fetch failed: {e}")

        print("\n6. Checking browser console for errors...")
        await asyncio.sleep(1)

        print("\n7. Now clicking submit button...")
        submit_btn = await page.query_selector('button[type="submit"]')
        if submit_btn:
            await submit_btn.click()
            print("✓ Submit clicked, waiting 5 seconds to see what happens...")
            await asyncio.sleep(5)

            print(f"\n8. Current URL after submit: {page.url}")

            # Check for error messages
            try:
                error_msg = await page.query_selector('#errorMessage')
                if error_msg and await error_msg.is_visible():
                    error_text = await error_msg.inner_text()
                    print(f"   Error message visible: {error_text}")
            except:
                pass

        print("\n9. Waiting a bit longer for any network activity...")
        await asyncio.sleep(5)

        print("\n" + "="*80)
        print("DEBUG COMPLETE")
        print("="*80)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_network())
