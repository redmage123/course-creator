#!/usr/bin/env python3
"""Quick script to check what's on the homepage"""

import asyncio
from playwright.async_api import async_playwright


async def check_homepage():
    """Check homepage content"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--ignore-certificate-errors']
        )
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()

        await page.goto('https://localhost:3000')
        await page.wait_for_load_state('networkidle')

        # Get page title
        title = await page.title()
        print(f"Page title: {title}")

        # Get all links
        links = await page.locator('a').all_text_contents()
        print(f"\nAll links text ({len(links)}):")
        for i, link in enumerate(links[:20], 1):  # First 20 links
            print(f"  {i}. '{link}'")

        # Get all buttons
        buttons = await page.locator('button').all_text_contents()
        print(f"\nAll buttons text ({len(buttons)}):")
        for i, btn in enumerate(buttons[:20], 1):  # First 20 buttons
            print(f"  {i}. '{btn}'")

        # Get page HTML (first 2000 chars)
        html = await page.content()
        print(f"\nHTML (first 2000 chars):")
        print(html[:2000])

        await browser.close()


if __name__ == "__main__":
    asyncio.run(check_homepage())
