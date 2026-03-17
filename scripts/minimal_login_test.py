#!/usr/bin/env python3
"""
Minimal login test - exactly replicating what worked in debug script
"""
import asyncio
from playwright.async_api import async_playwright

async def main():
    print("Minimal login test...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--ignore-certificate-errors',
                '--allow-insecure-localhost'
            ]
        )

        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            ignore_https_errors=True
        )

        page = await context.new_page()

        print("1. Loading login page...")
        await page.goto('https://localhost:3000/html/student-login.html',
                       wait_until='networkidle',
                       timeout=30000)
        await asyncio.sleep(2)

        print("2. Filling credentials...")
        await page.fill('#email', 'orgadmin@e2etest.com')
        await page.fill('#password', 'org_admin_password')

        print("3. Clicking submit...")
        submit_btn = await page.query_selector('button[type="submit"]')
        await submit_btn.click()

        print("4. Waiting for URL to change...")
        try:
            await page.wait_for_url(lambda url: 'dashboard' in url, timeout=10000)
            print(f"✅ SUCCESS! Redirected to: {page.url}")
        except Exception as e:
            print(f"❌ FAILED: {e}")
            print(f"   Current URL: {page.url}")

        await asyncio.sleep(5)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
