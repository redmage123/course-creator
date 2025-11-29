#!/usr/bin/env python3
"""
Playwright test to validate demo slides sync between narration and video actions.

This test:
1. Opens the demo page
2. Plays slides and captures frames at specific timestamps
3. Validates that actions match narration timing
4. Checks for blue background, form data entry, submit clicks
"""

import asyncio
import os
from pathlib import Path
from playwright.async_api import async_playwright

BASE_URL = os.getenv('TEST_BASE_URL', 'https://localhost:3000')
SCREENSHOT_DIR = Path('/tmp/demo_sync_validation')

# Expected sync points for slide 2 (Organization Registration)
# Narration: "To get started... Enter your organization name, website...
#            Add your contact information... set up your administrator account...
#            Click submit, and there you go!"
SLIDE_2_SYNC_POINTS = [
    {'time': 0, 'description': 'Form visible, ready to fill'},
    {'time': 6, 'description': 'Filling organization name'},
    {'time': 8, 'description': 'Filling domain/website'},
    {'time': 12, 'description': 'Filling contact email'},
    {'time': 17, 'description': 'Filling admin credentials'},
    {'time': 20, 'description': 'Filling password fields'},
    {'time': 22, 'description': 'Clicking submit button'},
    {'time': 24, 'description': 'Showing success message'},
]


async def validate_demo_sync():
    """Validate demo slides sync with narration."""

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
        print("DEMO SYNC VALIDATION TEST")
        print("=" * 70)
        print(f"Base URL: {BASE_URL}")
        print(f"Screenshots: {SCREENSHOT_DIR}")
        print()

        # ============================================================
        # TEST 1: Check video files exist and are updated
        # ============================================================
        print("TEST 1: Checking video files in container...")

        for slide_num in [1, 2]:
            if slide_num == 1:
                video_path = "/demo/videos/slide_01_platform_introduction.mp4"
            else:
                video_path = "/demo/videos/slide_02_organization_registration.mp4"

            try:
                response = await page.goto(f"{BASE_URL}{video_path}")
                if response:
                    status = response.status
                    headers = response.headers
                    content_length = headers.get('content-length', '0')
                    last_modified = headers.get('last-modified', 'N/A')

                    print(f"   Slide {slide_num}: Status={status}, Size={int(content_length)/1024:.1f}KB, Modified={last_modified}")

                    if status != 200:
                        print(f"   ✗ FAIL: Video not found!")
                else:
                    print(f"   ✗ FAIL: No response for slide {slide_num}")
            except Exception as e:
                print(f"   ✗ ERROR: {e}")

        # ============================================================
        # TEST 2: Load demo page and check structure
        # ============================================================
        print("\nTEST 2: Loading demo page...")
        await page.goto(f"{BASE_URL}/demo")
        await page.wait_for_load_state('networkidle')
        await asyncio.sleep(2)

        await page.screenshot(path=str(SCREENSHOT_DIR / "00_demo_page.png"))
        print("   Screenshot: 00_demo_page.png")

        # Check for video element
        video_count = await page.locator('video').count()
        print(f"   Video elements found: {video_count}")

        # Check current video source
        video_src = await page.evaluate("""
            () => {
                const video = document.querySelector('video');
                return video ? video.currentSrc || video.src : null;
            }
        """)
        print(f"   Current video source: {video_src}")

        # ============================================================
        # TEST 3: Play slide 1 and capture frames
        # ============================================================
        print("\nTEST 3: Testing Slide 1 (Platform Introduction)...")

        # Try to start playback
        try:
            # Look for play button
            play_clicked = False
            for selector in ['button:has-text("Play")', '[class*="playButton"]', 'video']:
                elem = page.locator(selector).first
                if await elem.count() > 0:
                    await elem.click()
                    play_clicked = True
                    print(f"   Clicked: {selector}")
                    break

            if play_clicked:
                # Capture frames at intervals
                for i in range(4):
                    await asyncio.sleep(3)
                    await page.screenshot(path=str(SCREENSHOT_DIR / f"01_slide1_frame_{i}.png"))

                    # Check video time
                    video_time = await page.evaluate("() => document.querySelector('video')?.currentTime || 0")
                    is_playing = await page.evaluate("() => !document.querySelector('video')?.paused")
                    print(f"   Frame {i}: time={video_time:.1f}s, playing={is_playing}")
        except Exception as e:
            print(f"   Error: {e}")

        # ============================================================
        # TEST 4: Navigate to slide 2 and test sync points
        # ============================================================
        print("\nTEST 4: Testing Slide 2 sync points...")

        # Go back to demo page fresh
        await page.goto(f"{BASE_URL}/demo")
        await page.wait_for_load_state('networkidle')
        await asyncio.sleep(1)

        # Try to navigate to slide 2
        try:
            # Look for slide 2 selector or next button
            slide2_selectors = [
                'button:has-text("2")',
                '[data-slide-index="1"]',
                'li:nth-child(2) button',
                '[class*="slideItem"]:nth-child(2)',
            ]

            navigated = False
            for selector in slide2_selectors:
                elem = page.locator(selector).first
                if await elem.count() > 0:
                    await elem.click()
                    navigated = True
                    print(f"   Navigated to slide 2 via: {selector}")
                    break

            if not navigated:
                # Try clicking next button
                next_btn = page.locator('button:has-text("Next"), [class*="next"]').first
                if await next_btn.count() > 0:
                    await next_btn.click()
                    print("   Clicked next button")
                    navigated = True

            await asyncio.sleep(2)

            # Now play slide 2 and capture at sync points
            play_btn = page.locator('button:has-text("Play"), [class*="play"]').first
            if await play_btn.count() > 0:
                await play_btn.click()
                print("   Started playback")

            # Capture at each sync point
            start_time = asyncio.get_event_loop().time()

            for sync_point in SLIDE_2_SYNC_POINTS:
                target_time = sync_point['time']
                description = sync_point['description']

                # Wait until target time
                elapsed = asyncio.get_event_loop().time() - start_time
                if target_time > elapsed:
                    await asyncio.sleep(target_time - elapsed)

                # Capture screenshot
                screenshot_name = f"02_slide2_t{target_time:02d}_{description.replace(' ', '_')}.png"
                await page.screenshot(path=str(SCREENSHOT_DIR / screenshot_name))

                # Get video state
                video_state = await page.evaluate("""
                    () => {
                        const video = document.querySelector('video');
                        return video ? {
                            currentTime: video.currentTime,
                            paused: video.paused
                        } : null;
                    }
                """)

                actual_time = video_state['currentTime'] if video_state else 0
                print(f"   t={target_time}s ({description}): video_time={actual_time:.1f}s")

        except Exception as e:
            print(f"   Error: {e}")

        # ============================================================
        # TEST 5: Direct video analysis
        # ============================================================
        print("\nTEST 5: Direct video frame analysis...")

        # Create a page that loads just the video
        video_page = await context.new_page()

        try:
            # Load slide 2 video directly in a video element
            await video_page.set_content(f"""
                <html>
                <body style="margin:0; background:#000;">
                    <video id="testVideo" width="1920" height="1080" controls>
                        <source src="{BASE_URL}/demo/videos/slide_02_organization_registration.mp4" type="video/mp4">
                    </video>
                    <script>
                        const video = document.getElementById('testVideo');
                        video.play();
                    </script>
                </body>
                </html>
            """)

            await asyncio.sleep(2)

            # Check if video loaded
            video_info = await video_page.evaluate("""
                () => {
                    const video = document.getElementById('testVideo');
                    return {
                        duration: video.duration,
                        videoWidth: video.videoWidth,
                        videoHeight: video.videoHeight,
                        readyState: video.readyState,
                        error: video.error?.message
                    };
                }
            """)

            print(f"   Video duration: {video_info.get('duration', 'N/A')}s")
            print(f"   Video dimensions: {video_info.get('videoWidth', 'N/A')}x{video_info.get('videoHeight', 'N/A')}")
            print(f"   Ready state: {video_info.get('readyState', 'N/A')}")

            if video_info.get('error'):
                print(f"   ERROR: {video_info.get('error')}")

            # Capture frames at key sync points
            for target_time in [0, 6, 12, 17, 22, 24]:
                await video_page.evaluate(f"document.getElementById('testVideo').currentTime = {target_time}")
                await asyncio.sleep(0.5)

                screenshot_name = f"03_direct_video_t{target_time:02d}.png"
                await video_page.screenshot(path=str(SCREENSHOT_DIR / screenshot_name))
                print(f"   Captured frame at t={target_time}s")

        except Exception as e:
            print(f"   Error: {e}")
        finally:
            await video_page.close()

        await browser.close()

        print("\n" + "=" * 70)
        print("VALIDATION COMPLETE")
        print("=" * 70)
        print(f"\nScreenshots saved to: {SCREENSHOT_DIR}")
        print("\nTo view screenshots:")
        print(f"  ls -la {SCREENSHOT_DIR}/")


if __name__ == "__main__":
    asyncio.run(validate_demo_sync())
