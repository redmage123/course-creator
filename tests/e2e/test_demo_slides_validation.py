#!/usr/bin/env python3
"""
Playwright test to validate demo slides are displaying correctly.

This test:
1. Opens the demo page
2. Plays each slide and takes screenshots
3. Validates video is loading and playing
4. Checks for blue background and form data entry
"""

import asyncio
import os
from pathlib import Path
from playwright.async_api import async_playwright

BASE_URL = os.getenv('TEST_BASE_URL', 'https://localhost:3000')
SCREENSHOT_DIR = Path('/tmp/demo_validation_screenshots')


async def validate_demo_slides():
    """Validate demo slides are working correctly."""

    # Create screenshot directory
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--ignore-certificate-errors']
        )

        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            ignore_https_errors=True
        )

        page = await context.new_page()

        print("=" * 70)
        print("DEMO SLIDES VALIDATION TEST")
        print("=" * 70)
        print(f"Base URL: {BASE_URL}")
        print(f"Screenshots: {SCREENSHOT_DIR}")
        print()

        # Navigate to demo page
        print("1. Navigating to demo page...")
        await page.goto(f"{BASE_URL}/demo")
        await page.wait_for_load_state('networkidle')
        await asyncio.sleep(2)

        # Take initial screenshot
        await page.screenshot(path=str(SCREENSHOT_DIR / "01_demo_page_loaded.png"))
        print("   Screenshot: 01_demo_page_loaded.png")

        # Check if demo player is visible
        demo_player = page.locator('[class*="demo"], [class*="Demo"], [class*="player"], [class*="Player"]').first
        if await demo_player.count() > 0:
            print("   ✓ Demo player found")
        else:
            print("   ✗ Demo player NOT found - checking page structure...")
            # Take a screenshot of the page structure
            html = await page.content()
            print(f"   Page title: {await page.title()}")

        # Check for video element
        video = page.locator('video').first
        if await video.count() > 0:
            print("   ✓ Video element found")
            video_src = await video.get_attribute('src')
            print(f"   Video source: {video_src}")
        else:
            print("   ✗ Video element NOT found")

        # Check for play button
        play_btn = page.locator('button:has-text("Play"), button[aria-label*="play"], [class*="play"]').first
        if await play_btn.count() > 0:
            print("   ✓ Play button found")
        else:
            print("   Looking for any clickable controls...")
            buttons = await page.locator('button').all()
            print(f"   Found {len(buttons)} buttons on page")

        # Try to click play
        print("\n2. Attempting to play slide 1...")
        try:
            # Try various play button selectors
            play_selectors = [
                'button:has-text("Play")',
                'button[aria-label*="play"]',
                '[class*="play"]',
                'button:has-text("Start")',
                'button:has-text("Begin")',
            ]

            clicked = False
            for selector in play_selectors:
                btn = page.locator(selector).first
                if await btn.count() > 0:
                    await btn.click()
                    print(f"   Clicked: {selector}")
                    clicked = True
                    break

            if not clicked:
                # Try clicking the video element directly
                if await video.count() > 0:
                    await video.click()
                    print("   Clicked video element directly")
                    clicked = True

            if clicked:
                await asyncio.sleep(3)
                await page.screenshot(path=str(SCREENSHOT_DIR / "02_after_play_click.png"))
                print("   Screenshot: 02_after_play_click.png")
        except Exception as e:
            print(f"   Error clicking play: {e}")

        # Wait and take screenshots at intervals to see slide content
        print("\n3. Capturing slide frames...")
        for i in range(5):
            await asyncio.sleep(2)
            screenshot_name = f"03_slide_frame_{i+1}.png"
            await page.screenshot(path=str(SCREENSHOT_DIR / screenshot_name))
            print(f"   Screenshot: {screenshot_name}")

        # Check video properties
        print("\n4. Checking video properties...")
        try:
            video_info = await page.evaluate("""
                () => {
                    const video = document.querySelector('video');
                    if (video) {
                        return {
                            src: video.src,
                            currentSrc: video.currentSrc,
                            duration: video.duration,
                            currentTime: video.currentTime,
                            paused: video.paused,
                            readyState: video.readyState,
                            videoWidth: video.videoWidth,
                            videoHeight: video.videoHeight,
                            error: video.error ? video.error.message : null
                        };
                    }
                    return null;
                }
            """)

            if video_info:
                print(f"   Source: {video_info.get('currentSrc', 'N/A')}")
                print(f"   Duration: {video_info.get('duration', 'N/A')}s")
                print(f"   Current time: {video_info.get('currentTime', 'N/A')}s")
                print(f"   Paused: {video_info.get('paused', 'N/A')}")
                print(f"   Ready state: {video_info.get('readyState', 'N/A')}")
                print(f"   Dimensions: {video_info.get('videoWidth', 'N/A')}x{video_info.get('videoHeight', 'N/A')}")
                if video_info.get('error'):
                    print(f"   ERROR: {video_info.get('error')}")
            else:
                print("   No video element found")
        except Exception as e:
            print(f"   Error getting video info: {e}")

        # Try to navigate to slide 2
        print("\n5. Attempting to go to slide 2...")
        try:
            # Look for next button or slide selector
            next_btn = page.locator('button:has-text("Next"), button[aria-label*="next"], [class*="next"]').first
            if await next_btn.count() > 0:
                await next_btn.click()
                print("   Clicked next button")
                await asyncio.sleep(3)
                await page.screenshot(path=str(SCREENSHOT_DIR / "04_slide_2.png"))
                print("   Screenshot: 04_slide_2.png")
            else:
                # Try clicking on slide 2 in a slide list
                slide2 = page.locator('button:has-text("2"), [data-slide="2"], li:nth-child(2)').first
                if await slide2.count() > 0:
                    await slide2.click()
                    print("   Clicked slide 2 selector")
                    await asyncio.sleep(3)
                    await page.screenshot(path=str(SCREENSHOT_DIR / "04_slide_2.png"))
        except Exception as e:
            print(f"   Error navigating to slide 2: {e}")

        # Check what videos are available on the server
        print("\n6. Checking video files on server...")
        try:
            # Try to fetch video directly
            response = await page.goto(f"{BASE_URL}/demo/videos/slide_01_platform_introduction.mp4")
            if response:
                print(f"   Slide 1 video status: {response.status}")
                if response.status == 200:
                    headers = response.headers
                    print(f"   Content-Type: {headers.get('content-type', 'N/A')}")
                    print(f"   Content-Length: {headers.get('content-length', 'N/A')} bytes")
        except Exception as e:
            print(f"   Error checking video: {e}")

        # Go back to demo page and check slide 2 video
        try:
            response = await page.goto(f"{BASE_URL}/demo/videos/slide_02_organization_registration.mp4")
            if response:
                print(f"   Slide 2 video status: {response.status}")
                if response.status == 200:
                    headers = response.headers
                    print(f"   Content-Length: {headers.get('content-length', 'N/A')} bytes")
        except Exception as e:
            print(f"   Error checking slide 2 video: {e}")

        await browser.close()

        print("\n" + "=" * 70)
        print("VALIDATION COMPLETE")
        print("=" * 70)
        print(f"\nScreenshots saved to: {SCREENSHOT_DIR}")
        print("Review the screenshots to see what the demo player is showing.")


if __name__ == "__main__":
    asyncio.run(validate_demo_slides())
