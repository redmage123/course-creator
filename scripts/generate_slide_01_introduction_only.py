#!/usr/bin/env python3
"""
Demo Video Generation - Slide 1: Introduction Only (20s)
=========================================================

Simple introduction showing the homepage.
No form filling - that moves to slide 2.

Duration: 20 seconds
Output: slide_01_introduction.mp4
"""

import asyncio
import subprocess
import sys
from pathlib import Path
import logging

sys.path.insert(0, '/home/bbrelin/course-creator')

from playwright.async_api import async_playwright

# Configuration
BASE_URL = "https://localhost:3000"
RESOLUTION = (1920, 1080)
VIDEOS_DIR = Path("/home/bbrelin/course-creator/frontend/static/demo/videos")
FRAME_RATE = 30
SLIDE_DURATION = 20

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FFmpegRecorder:
    """H.264 screen recorder"""

    def __init__(self):
        self.process = None
        self.output_file = None

    def start_recording(self, output_file):
        """Start FFmpeg screen recording"""
        self.output_file = output_file

        cmd = [
            'ffmpeg',
            '-f', 'x11grab',
            '-video_size', f'{RESOLUTION[0]}x{RESOLUTION[1]}',
            '-framerate', str(FRAME_RATE),
            '-i', ':99',
            '-vcodec', 'libx264',
            '-preset', 'fast',
            '-pix_fmt', 'yuv420p',
            '-crf', '23',
            '-movflags', '+faststart',
            '-y',
            str(output_file)
        ]

        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        logger.info(f"🎥 Recording: {output_file.name}")
        return True

    def stop_recording(self):
        """Stop FFmpeg recording"""
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()

            if self.output_file and self.output_file.exists():
                size_mb = self.output_file.stat().st_size / (1024 * 1024)
                logger.info(f"⏹️  Stopped: {self.output_file.name} ({size_mb:.2f} MB)")
                return True
        return False

async def remove_privacy_banners(page):
    """Remove privacy/cookie consent modals"""
    try:
        await page.evaluate("""
            () => {
                const selectors = [
                    '[class*="privacy"]', '[class*="cookie"]', '[class*="consent"]',
                    '[id*="privacy"]', '[id*="cookie"]', '#privacyModal', '.privacy-modal'
                ];
                selectors.forEach(sel => {
                    document.querySelectorAll(sel).forEach(el => el.remove());
                });
            }
        """)
        await asyncio.sleep(0.3)
    except Exception as e:
        logger.debug(f"Privacy banner removal: {e}")

async def generate_slide_01_introduction(page, recorder):
    """
    Slide 1: Introduction (20s)

    Simple homepage view with platform overview.
    Ends with transition: "In the next slide, we'll show you how to create an organization."
    """
    logger.info("=" * 80)
    logger.info("📺 SLIDE 1: Introduction (20s)")
    logger.info("=" * 80)

    output_file = VIDEOS_DIR / "slide_01_introduction.mp4"

    try:
        # Pre-load page BEFORE recording (avoids blank screen)
        logger.info("Loading homepage...")
        await page.goto(f"{BASE_URL}/html/index.html",
                       wait_until='networkidle',
                       timeout=30000)
        await remove_privacy_banners(page)
        await asyncio.sleep(3)

        logger.info("✅ Page loaded - starting recording")

        # Start recording
        recorder.start_recording(output_file)
        await asyncio.sleep(2)

        # Show homepage for 20 seconds
        logger.info("Displaying homepage for 20 seconds...")
        await asyncio.sleep(18)

        logger.info("✅ Slide 1 complete")

    except Exception as e:
        logger.error(f"❌ Slide 1 generation failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        recorder.stop_recording()

async def main():
    """Main execution"""
    logger.info("=" * 80)
    logger.info("🎬 SLIDE 1: INTRODUCTION ONLY")
    logger.info("=" * 80)
    logger.info("Duration: 20 seconds")
    logger.info("Content: Homepage with platform overview")
    logger.info("Narration: Introduction + transition to slide 2")
    logger.info("=" * 80)

    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    recorder = FFmpegRecorder()

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--window-size=1920,1080',
                '--window-position=0,0'
            ]
        )

        context = await browser.new_context(
            viewport={'width': RESOLUTION[0], 'height': RESOLUTION[1]},
            ignore_https_errors=True,
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        )

        page = await context.new_page()

        try:
            await generate_slide_01_introduction(page, recorder)

            logger.info("")
            logger.info("=" * 80)
            logger.info("✅ SLIDE 1 COMPLETE")
            logger.info("=" * 80)

            output_file = VIDEOS_DIR / "slide_01_introduction.mp4"
            if output_file.exists():
                size_mb = output_file.stat().st_size / (1024 * 1024)
                logger.info(f"✅ Video saved: {output_file}")
                logger.info(f"   Size: {size_mb:.2f} MB")

        finally:
            await context.close()
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
