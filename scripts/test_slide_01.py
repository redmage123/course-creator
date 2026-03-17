#!/usr/bin/env python3
"""
Test Slide 1 Recording with OBS + Playwright
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, '/home/bbrelin/course-creator')

from scripts.generate_demo_with_obs import (
    OBSRecorder,
    slide_01_introduction,
    BASE_URL,
    RESOLUTION,
    remove_privacy_banners,
    smooth_scroll,
    smooth_mouse_move
)
from playwright.async_api import async_playwright

async def test_slide_1():
    """Test slide 1 recording"""
    print("="*70)
    print("🎬 TESTING SLIDE 1 - Introduction")
    print("="*70)
    print()

    # Initialize OBS recorder
    print("📡 Connecting to OBS...")
    recorder = OBSRecorder()
    recorder.connect()

    try:
        print("🌐 Launching browser...")
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--ignore-certificate-errors',
                    '--window-position=0,0',
                    f'--window-size={RESOLUTION[0]},{RESOLUTION[1]}'
                ]
            )

            context = await browser.new_context(
                viewport={'width': RESOLUTION[0], 'height': RESOLUTION[1]},
                ignore_https_errors=True
            )

            page = await context.new_page()

            print("🎥 Recording Slide 1...")
            print("   Duration: 25 seconds")
            print("   Output: frontend/static/demo/videos/slide_01_introduction.mp4")
            print()

            # Record slide 1
            await slide_01_introduction(page, recorder, 25)

            print()
            print("🔍 Checking output file...")

            import os
            output_file = "/home/bbrelin/course-creator/frontend/static/demo/videos/slide_01_introduction.mp4"

            # Wait a moment for file to be written
            await asyncio.sleep(3)

            if os.path.exists(output_file):
                size_mb = os.path.getsize(output_file) / (1024 * 1024)
                print(f"   ✅ File created: {output_file}")
                print(f"   📦 Size: {size_mb:.2f} MB")

                # Check with ffprobe
                import subprocess
                try:
                    result = subprocess.run(
                        ['ffprobe', '-v', 'error', '-show_entries',
                         'format=duration', '-of',
                         'default=noprint_wrappers=1:nokey=1',
                         output_file],
                        capture_output=True,
                        text=True
                    )
                    if result.stdout:
                        duration = float(result.stdout.strip())
                        print(f"   ⏱️  Duration: {duration:.1f} seconds")

                    # Get video info
                    result = subprocess.run(
                        ['ffprobe', '-v', 'error', '-select_streams', 'v:0',
                         '-show_entries', 'stream=width,height,codec_name',
                         '-of', 'default=noprint_wrappers=1', output_file],
                        capture_output=True,
                        text=True
                    )
                    if result.stdout:
                        print(f"   📹 Video info:")
                        for line in result.stdout.strip().split('\n'):
                            if '=' in line:
                                key, value = line.split('=')
                                print(f"      {key}: {value}")

                except Exception as e:
                    print(f"   ⚠️  Could not get file details: {e}")

            else:
                print(f"   ❌ File not found: {output_file}")
                print("   💡 Check OBS output directory settings")

            await context.close()
            await browser.close()

    finally:
        recorder.disconnect()

    print()
    print("="*70)
    print("✅ SLIDE 1 TEST COMPLETE")
    print("="*70)
    print()
    print("Next steps:")
    print("  1. Review the video: vlc frontend/static/demo/videos/slide_01_introduction.mp4")
    print("  2. Check audio sync with: frontend/static/demo/audio/slide_01_narration.mp3")
    print("  3. If good, run: python3 scripts/generate_demo_with_obs.py (to generate all slides)")

if __name__ == "__main__":
    asyncio.run(test_slide_1())
