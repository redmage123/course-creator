#!/usr/bin/env python3
"""Check what happens after registration submission"""

import asyncio
import uuid
from playwright.async_api import async_playwright


async def check_post_registration():
    """Check where registration redirects to"""
    unique_id = str(uuid.uuid4())[:8]

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--ignore-certificate-errors']
        )
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()

        # Navigate and register
        await page.goto('https://localhost:3000')
        await page.wait_for_load_state('networkidle')
        print("✓ Homepage loaded")

        # Click Register
        await page.click('button:has-text("Register")')
        await page.wait_for_url('**/html/register.html')
        print("✓ Registration page loaded")

        # Fill form
        await page.fill('input[name="fullName"]', f'orgadmin_{unique_id}')
        await page.fill('input[name="email"]', f'orgadmin_{unique_id}@test.com')
        await page.fill('input[name="password"]', 'TestPass123!')
        await page.fill('input[name="confirmPassword"]', 'TestPass123!')
        await page.check('input[name="gdprConsent"]')
        print("✓ Form filled")

        # Submit and track navigation
        print("\nSubmitting form...")
        await page.click('button[type="submit"]')

        # Wait a bit and check URL
        await page.wait_for_timeout(3000)

        url = page.url
        title = await page.title()
        print(f"URL after submission: {url}")
        print(f"Page title: {title}")

        # Check for error messages
        error_msgs = await page.locator('.error, .alert-danger, [role="alert"]').all_text_contents()
        if error_msgs:
            print(f"Error messages: {error_msgs}")

        # Check for success messages
        success_msgs = await page.locator('.success, .alert-success').all_text_contents()
        if success_msgs:
            print(f"Success messages: {success_msgs}")

        # Check page content
        body_text = await page.locator('body').text_content()
        print(f"\nPage content (first 800 chars):")
        print(body_text[:800])

        # Save screenshot
        await page.screenshot(path='/tmp/after_registration_submit.png')
        print(f"\nScreenshot: /tmp/after_registration_submit.png")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(check_post_registration())
