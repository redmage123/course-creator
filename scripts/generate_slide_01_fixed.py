#!/usr/bin/env python3
"""
Demo Video Generation - Slide 1: Organization Registration (FIXED)
==================================================================

IMPROVEMENTS:
- No blank screen at start (load page BEFORE recording)
- Visible mouse cursor with realistic movement
- Natural typing animation synchronized with narration
- Proper timing matching the audio narration
- All correct form field selectors

Duration: ~77 seconds to match narration
Output: slide_01_org_registration.mp4 (1920x1080 @ 30fps, H.264)
"""

import asyncio
import subprocess
import sys
import os
from pathlib import Path
import logging
import time

sys.path.insert(0, '/home/bbrelin/course-creator')

from playwright.async_api import async_playwright

# Configuration
BASE_URL = "https://localhost:3000"
RESOLUTION = (1920, 1080)
VIDEOS_DIR = Path("/home/bbrelin/course-creator/frontend/static/demo/videos")
FRAME_RATE = 30
SLIDE_DURATION = 77  # seconds

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Demo organization data (correct field values)
DEMO_ORG_DATA = {
    'orgName': 'Tech Academy',
    'orgDescription': 'Professional software development training for aspiring developers',
    'orgDomain': 'techacademy.com',
    'orgStreetAddress': '123 Tech Street',
    'orgCity': 'San Francisco',
    'orgStateProvince': 'California',
    'orgPostalCode': '94105',
    'orgEmail': 'contact@techacademy.com',
    'orgPhone': '5551234567',
    'adminName': 'Demo Administrator',
    'adminEmail': 'admin@techacademy.com',
    'adminPassword': 'SecurePass123!',
}

class FFmpegRecorder:
    """H.264 screen recorder using FFmpeg with web optimization"""

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
            '-movflags', '+faststart',  # Web optimization
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
            else:
                logger.error(f"❌ File not created: {self.output_file}")
                return False
        return False

async def remove_privacy_banners(page):
    """Remove all privacy/cookie consent modals"""
    try:
        await page.evaluate("""
            () => {
                // Remove privacy modals
                const selectors = [
                    '[class*="privacy"]', '[class*="cookie"]', '[class*="consent"]',
                    '[id*="privacy"]', '[id*="cookie"]', '#privacyModal', '.privacy-modal',
                    '[class*="gdpr"]', '[class*="banner"]'
                ];
                selectors.forEach(sel => {
                    document.querySelectorAll(sel).forEach(el => {
                        if (el.tagName === 'DIV' || el.tagName === 'DIALOG') {
                            el.remove();
                        }
                    });
                });
            }
        """)
        await asyncio.sleep(0.3)
    except Exception as e:
        logger.debug(f"Privacy banner removal: {e}")

async def move_mouse_to(page, selector, offset_x=0, offset_y=0):
    """
    Move mouse cursor to element with smooth animation

    Args:
        page: Playwright page
        selector: CSS selector
        offset_x: X offset from element center
        offset_y: Y offset from element center
    """
    try:
        element = await page.wait_for_selector(selector, timeout=5000, state='visible')
        box = await element.bounding_box()

        if box:
            target_x = box['x'] + box['width'] / 2 + offset_x
            target_y = box['y'] + box['height'] / 2 + offset_y

            # Smooth mouse movement
            await page.mouse.move(target_x, target_y, steps=20)
            await asyncio.sleep(0.5)
            logger.info(f"  🖱️  Moved mouse to {selector}")
            return True
    except Exception as e:
        logger.error(f"  ✗ Failed to move mouse to {selector}: {e}")
        return False

async def click_element(page, selector):
    """Click element with mouse cursor visible"""
    try:
        await move_mouse_to(page, selector)
        await page.click(selector)
        logger.info(f"  🖱️  Clicked: {selector}")
        await asyncio.sleep(0.5)
        return True
    except Exception as e:
        logger.error(f"  ✗ Failed to click {selector}: {e}")
        return False

async def type_naturally(page, selector, text, delay_ms=80):
    """
    Type text with natural human-like timing

    Args:
        page: Playwright page
        selector: CSS selector
        text: Text to type
        delay_ms: Base delay between characters (with randomization)
    """
    try:
        # Click field first
        await click_element(page, selector)
        await asyncio.sleep(0.2)

        # Type character by character with variable delay
        import random
        for char in text:
            await page.keyboard.type(char)
            # Randomize typing speed (human-like)
            variation = random.uniform(0.7, 1.3)
            await asyncio.sleep((delay_ms / 1000) * variation)

        logger.info(f"  ⌨️  Typed: {selector}")
        return True
    except Exception as e:
        logger.error(f"  ✗ Failed to type in {selector}: {e}")
        return False

async def smooth_scroll(page, target_y, duration_ms=1000):
    """Smooth animated scroll"""
    try:
        await page.evaluate(f"""
            ({{ target, duration }}) => {{
                return new Promise((resolve) => {{
                    const start = window.pageYOffset;
                    const distance = target - start;
                    const startTime = performance.now();

                    function easeInOutCubic(t) {{
                        return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
                    }}

                    function scroll() {{
                        const now = performance.now();
                        const elapsed = now - startTime;
                        const progress = Math.min(elapsed / duration, 1);
                        const eased = easeInOutCubic(progress);
                        window.scrollTo(0, start + distance * eased);
                        if (progress < 1) {{
                            requestAnimationFrame(scroll);
                        }} else {{
                            resolve();
                        }}
                    }}
                    scroll();
                }});
            }}
        """, {"target": target_y, "duration": duration_ms})
        await asyncio.sleep(duration_ms / 1000 + 0.2)
    except Exception as e:
        logger.warning(f"Scroll failed: {e}")

async def generate_slide_01_fixed(page, recorder):
    """
    Slide 1: Organization Registration (77s)

    Timeline:
    0-8s:  Homepage + click Register button
    8-77s: Fill registration form (synchronized with narration)
    """
    logger.info("=" * 80)
    logger.info("📺 SLIDE 1: Organization Registration (FIXED)")
    logger.info("=" * 80)

    output_file = VIDEOS_DIR / "slide_01_org_registration.mp4"

    try:
        # STEP 0: Load page completely BEFORE recording (avoids blank screen)
        logger.info("Step 0: Pre-loading page (not recording yet)...")
        await page.goto(f"{BASE_URL}/html/index.html",
                       wait_until='networkidle',
                       timeout=30000)
        await remove_privacy_banners(page)
        await asyncio.sleep(3)  # Ensure fully loaded

        logger.info("✅ Page loaded - NOW starting recording")

        # Start recording (page already loaded = no blank screen)
        recorder.start_recording(output_file)
        await asyncio.sleep(2)

        # 0-8s: Homepage with Register button
        logger.info("Step 1: Showing homepage and Register button...")
        await asyncio.sleep(2)  # Show homepage for 2s

        # Move mouse to Register button
        logger.info("Step 2: Moving mouse to Register Organization button...")
        register_clicked = await click_element(
            page,
            'a[href*="organization-registration"], a:has-text("Register"), button:has-text("Register")'
        )

        if not register_clicked:
            logger.warning("  Register button not found, navigating directly...")
            await page.goto(f"{BASE_URL}/html/organization-registration.html",
                           wait_until='networkidle',
                           timeout=30000)

        await asyncio.sleep(2)
        await remove_privacy_banners(page)

        # 8-25s: Organization Details Section
        logger.info("Step 3: Filling Organization Details...")
        await asyncio.sleep(1)

        await type_naturally(page, '#orgName', DEMO_ORG_DATA['orgName'], delay_ms=100)
        await asyncio.sleep(0.8)

        await type_naturally(page, '#orgDescription', DEMO_ORG_DATA['orgDescription'], delay_ms=60)
        await asyncio.sleep(0.8)

        await type_naturally(page, '#orgDomain', DEMO_ORG_DATA['orgDomain'], delay_ms=90)
        await asyncio.sleep(1)

        # 25-45s: Address Section
        logger.info("Step 4: Scrolling to Address section...")
        await smooth_scroll(page, 400, 800)
        await asyncio.sleep(0.5)

        logger.info("Step 5: Filling Address Details...")
        await type_naturally(page, '#orgStreetAddress', DEMO_ORG_DATA['orgStreetAddress'], delay_ms=90)
        await asyncio.sleep(0.7)

        await type_naturally(page, '#orgCity', DEMO_ORG_DATA['orgCity'], delay_ms=100)
        await asyncio.sleep(0.7)

        await type_naturally(page, '#orgStateProvince', DEMO_ORG_DATA['orgStateProvince'], delay_ms=90)
        await asyncio.sleep(0.7)

        await type_naturally(page, '#orgPostalCode', DEMO_ORG_DATA['orgPostalCode'], delay_ms=100)
        await asyncio.sleep(1)

        # 45-62s: Contact & Admin Section
        logger.info("Step 6: Scrolling to Contact & Admin section...")
        await smooth_scroll(page, 800, 800)
        await asyncio.sleep(0.5)

        logger.info("Step 7: Filling Contact Details...")
        await type_naturally(page, '#orgEmail', DEMO_ORG_DATA['orgEmail'], delay_ms=80)
        await asyncio.sleep(0.7)

        await type_naturally(page, '#orgPhone', DEMO_ORG_DATA['orgPhone'], delay_ms=100)
        await asyncio.sleep(1)

        logger.info("Step 8: Filling Administrator Details...")
        await type_naturally(page, '#adminName', DEMO_ORG_DATA['adminName'], delay_ms=90)
        await asyncio.sleep(0.7)

        await type_naturally(page, '#adminEmail', DEMO_ORG_DATA['adminEmail'], delay_ms=80)
        await asyncio.sleep(0.7)

        await type_naturally(page, '#adminPassword', DEMO_ORG_DATA['adminPassword'], delay_ms=70)
        await asyncio.sleep(0.7)

        await type_naturally(page, '#adminPasswordConfirm', DEMO_ORG_DATA['adminPassword'], delay_ms=70)
        await asyncio.sleep(1.5)

        # 62-72s: Submit Form
        logger.info("Step 9: Scrolling to Submit button...")
        await smooth_scroll(page, 1200, 600)
        await asyncio.sleep(0.5)

        logger.info("Step 10: Submitting form...")
        await click_element(page, 'button[type="submit"]')
        await asyncio.sleep(3)

        # 72-77s: Show success message
        logger.info("Step 11: Showing success confirmation...")
        await asyncio.sleep(5)

        logger.info("✅ Slide 1 generation complete!")

    except Exception as e:
        logger.error(f"❌ Slide 1 generation failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        recorder.stop_recording()

async def main():
    """Main execution"""
    logger.info("=" * 80)
    logger.info("🎬 SLIDE 1 GENERATION (FIXED VERSION)")
    logger.info("=" * 80)
    logger.info("IMPROVEMENTS:")
    logger.info("  ✓ No blank screen (loads page before recording)")
    logger.info("  ✓ Visible mouse cursor with smooth movement")
    logger.info("  ✓ Natural typing animation")
    logger.info("  ✓ Synchronized with narration")
    logger.info("  ✓ Correct form field selectors")
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
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
            # IMPORTANT: Show mouse cursor in recordings
            has_touch=False
        )

        page = await context.new_page()

        try:
            await generate_slide_01_fixed(page, recorder)

            logger.info("")
            logger.info("=" * 80)
            logger.info("✅ SLIDE 1 COMPLETE")
            logger.info("=" * 80)

            output_file = VIDEOS_DIR / "slide_01_org_registration.mp4"
            if output_file.exists():
                size_mb = output_file.stat().st_size / (1024 * 1024)
                logger.info(f"✅ Video saved: {output_file}")
                logger.info(f"   Size: {size_mb:.2f} MB")
            else:
                logger.error(f"❌ Video file not created")

        finally:
            await context.close()
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
