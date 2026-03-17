#!/usr/bin/env python3
"""Check what happens when clicking Register"""

import asyncio
from playwright.async_api import async_playwright


async def check_register_flow():
    """Check register button flow"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--ignore-certificate-errors']
        )
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()

        await page.goto('https://localhost:3000')
        await page.wait_for_load_state('networkidle')
        print("✓ Navigated to homepage")

        # Click Register button
        print("\nClicking Register button...")
        await page.click('button:has-text("Register")')
        await page.wait_for_timeout(2000)  # Wait 2 seconds

        # Get current URL
        url = page.url
        print(f"Current URL after clicking: {url}")

        # Get page title
        title = await page.title()
        print(f"Page title: {title}")

        # Look for any input fields
        inputs = await page.locator('input').all()
        print(f"\nFound {len(inputs)} input fields:")
        for i, inp in enumerate(inputs[:10], 1):
            input_type = await inp.get_attribute('type')
            input_name = await inp.get_attribute('name')
            input_id = await inp.get_attribute('id')
            input_placeholder = await inp.get_attribute('placeholder')
            is_visible = await inp.is_visible()
            print(f"  {i}. type={input_type}, name={input_name}, id={input_id}, placeholder={input_placeholder}, visible={is_visible}")

        # Check for modals
        modals = await page.locator('[role="dialog"], .modal, #registerModal').all()
        print(f"\nFound {len(modals)} modal elements:")
        for i, modal in enumerate(modals, 1):
            is_visible = await modal.is_visible()
            modal_id = await modal.get_attribute('id')
            modal_class = await modal.get_attribute('class')
            print(f"  {i}. id={modal_id}, class={modal_class}, visible={is_visible}")

        # Get all visible text on page
        body_text = await page.locator('body').text_content()
        print(f"\nBody text (first 500 chars):")
        print(body_text[:500])

        # Save screenshot
        await page.screenshot(path='/tmp/after_register_click.png')
        print(f"\nScreenshot saved to: /tmp/after_register_click.png")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(check_register_flow())
