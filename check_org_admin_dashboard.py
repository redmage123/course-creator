#!/usr/bin/env python3
"""Check org admin dashboard content"""

import asyncio
from playwright.async_api import async_playwright


async def check_dashboard():
    """Check what's on org admin dashboard"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--ignore-certificate-errors']
        )
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()

        await page.goto('https://localhost:3000/html/org-admin-dashboard.html')
        await page.wait_for_load_state('networkidle')

        title = await page.title()
        print(f"Page title: {title}")

        # Get all buttons
        buttons = await page.locator('button').all_text_contents()
        print(f"\nAll buttons ({len(buttons)}):")
        for i, btn in enumerate(buttons[:30], 1):
            print(f"  {i}. '{btn.strip()}'")

        # Get all links
        links = await page.locator('a').all_text_contents()
        print(f"\nAll links ({len(links)}):")
        for i, link in enumerate(links[:30], 1):
            print(f"  {i}. '{link.strip()}'")

        # Get all tabs
        tabs = await page.locator('[role="tab"], [data-tab], .tab').all_text_contents()
        print(f"\nAll tabs ({len(tabs)}):")
        for i, tab in enumerate(tabs[:20], 1):
            print(f"  {i}. '{tab.strip()}'")

        await page.screenshot(path='/tmp/org_admin_dashboard.png')
        print(f"\nScreenshot: /tmp/org_admin_dashboard.png")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(check_dashboard())
