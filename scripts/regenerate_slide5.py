#!/usr/bin/env python3
"""
Regenerate Slide 5 Only - Third Party Integrations
Quick test script for slide 5 video generation after fixes
"""
import asyncio
import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import from main generation script
from scripts.generate_demo_v3_with_integrations import (
    slide_05_third_party_integrations,
    login_as,
    FFmpegRecorder,
    VIDEOS_DIR,
    BASE_URL,
    RESOLUTION
)

from playwright.async_api import async_playwright

async def main():
    """Regenerate slide 5 only"""
    print("="*80)
    print("🎬 REGENERATING SLIDE 5: Third Party Integrations")
    print("="*80)
    print(f"  Output: {VIDEOS_DIR}/slide_05_third_party_integrations.mp4")
    print(f"  Duration: 60 seconds")
    print("="*80)
    print()

    # Create videos directory
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

    # Load narration data
    narrations_file = Path(__file__).parent / 'demo_player_narrations_v3.json'
    with open(narrations_file, 'r') as f:
        slides_data = json.load(f)

    # Get slide 5 data
    slide_5_data = [s for s in slides_data['slides'] if s['id'] == 5][0]
    duration = slide_5_data['duration']

    recorder = FFmpegRecorder()

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
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

        # Login as org admin first
        print("🔐 Logging in as org admin...")
        await login_as(page, 'org_admin')
        print("✅ Logged in")

        # Generate slide 5
        print(f"\n🎥 Generating Slide 5: {slide_5_data['title']} ({duration}s)")
        try:
            await slide_05_third_party_integrations(page, recorder, duration)
            print("✅ Slide 5 generation complete!")
        except Exception as e:
            print(f"❌ Error generating slide 5: {e}")
            import traceback
            traceback.print_exc()

        await browser.close()

    # Check file
    video_file = VIDEOS_DIR / "slide_05_third_party_integrations.mp4"
    if video_file.exists():
        size_mb = video_file.stat().st_size / (1024 * 1024)
        print(f"\n✅ Video saved: {video_file}")
        print(f"   Size: {size_mb:.2f} MB")
    else:
        print(f"\n❌ Video file not created: {video_file}")

if __name__ == "__main__":
    asyncio.run(main())
