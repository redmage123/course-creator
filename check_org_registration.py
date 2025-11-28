#!/usr/bin/env python3
"""Check organization registration page"""

import asyncio
from playwright.async_api import async_playwright


async def check_org_registration():
    """Check organization registration page"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--ignore-certificate-errors']
        )
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()

        # Try accessing organization registration directly
        print("Trying to access organization-registration.html...")
        await page.goto('https://localhost:3000/html/organization-registration.html')
        await page.wait_for_load_state('networkidle')

        url = page.url
        title = await page.title()
        print(f"URL: {url}")
        print(f"Title: {title}")

        # Check for redirect
        if 'organization-registration' not in url:
            print(f"REDIRECTED to: {url}")

        # Check for form fields (correct field name is id="orgName" and name="name")
        org_name_field = await page.locator('input#orgName, input[name="name"]').count()
        print(f"Organization name fields found: {org_name_field}")

        # Check if form exists
        form = await page.locator('#organizationRegistrationForm').count()
        print(f"Registration form found: {form}")

        if org_name_field > 0:
            print("\n✓ Organization registration form is accessible!")

            # Get all input fields
            inputs = await page.locator('input').all()
            print(f"\nFound {len(inputs)} input fields:")
            for i, inp in enumerate(inputs[:15], 1):
                input_type = await inp.get_attribute('type')
                input_name = await inp.get_attribute('name')
                input_id = await inp.get_attribute('id')
                is_visible = await inp.is_visible()
                print(f"  {i}. type={input_type}, name={input_name}, id={input_id}, visible={is_visible}")
        else:
            print("\n✗ No organization form found - may require authentication")
            body_text = await page.locator('body').text_content()
            print(f"\nPage content (first 500 chars):")
            print(body_text[:500])

        await page.screenshot(path='/tmp/org_registration_page.png')
        print(f"\nScreenshot: /tmp/org_registration_page.png")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(check_org_registration())
