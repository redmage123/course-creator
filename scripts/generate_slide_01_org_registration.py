#!/usr/bin/env python3
"""
Demo Video Generation - Slide 1: Organization Registration
===========================================================

Generates ONLY Slide 1: Organization Registration workflow

Shows:
- Navigating to organization registration page
- Filling out registration form with demo data
- Submitting registration
- Success confirmation

Duration: ~45 seconds
Output: slide_01_org_registration.mp4 (1920x1080 @ 30fps)
"""

import asyncio
import subprocess
import sys
import os
from pathlib import Path
import logging

sys.path.insert(0, '/home/bbrelin/course-creator')

from playwright.async_api import async_playwright

# Configuration
BASE_URL = "https://localhost:3000"
RESOLUTION = (1920, 1080)
VIDEOS_DIR = Path("/home/bbrelin/course-creator/frontend/static/demo/videos")
FRAME_RATE = 30
SLIDE_DURATION = 45  # seconds

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Demo organization data
DEMO_ORG_DATA = {
    'org_name': 'Tech Academy',
    'org_slug': 'tech-academy-demo',
    'contact_email': 'contact@techacademy.com',
    'contact_phone': '+1 (555) 123-4567',
    'address': '123 Tech Street',
    'city': 'San Francisco',
    'state': 'CA',
    'postal_code': '94105',
    'country': 'United States',
    'admin_name': 'Demo Admin',
    'admin_email': 'admin@techacademy.com',
    'admin_password': 'DemoAdmin123!'
}

class FFmpegRecorder:
    """H.264 screen recorder using FFmpeg"""

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
            '-i', ':99',  # DISPLAY :99
            '-vcodec', 'libx264',
            '-preset', 'fast',
            '-pix_fmt', 'yuv420p',
            '-crf', '23',
            '-movflags', '+faststart',  # CRITICAL: Web optimization
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
    """Remove privacy/cookie consent banners"""
    try:
        await page.evaluate("""
            () => {
                const selectors = [
                    '[class*="privacy"]',
                    '[class*="cookie"]',
                    '[class*="consent"]',
                    '[class*="gdpr"]',
                    '[id*="privacy"]',
                    '[id*="cookie"]',
                    '#privacyModal',
                    '.privacy-modal'
                ];
                selectors.forEach(sel => {
                    document.querySelectorAll(sel).forEach(el => el.remove());
                });
            }
        """)
        await asyncio.sleep(0.5)
    except Exception as e:
        logger.debug(f"Privacy banner removal: {e}")

async def smooth_scroll(page, target_y, duration_ms=1000):
    """Smooth animated scroll to position"""
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
        await page.evaluate(f"window.scrollTo(0, {target_y})")
        await asyncio.sleep(1)

async def fill_form_field(page, selector, value, delay_ms=50):
    """Fill form field with realistic typing animation"""
    try:
        element = await page.wait_for_selector(selector, timeout=5000, state='visible')
        await element.click()
        await asyncio.sleep(0.3)
        await element.type(value, delay=delay_ms)
        await asyncio.sleep(0.2)
        logger.info(f"  ✓ Filled: {selector}")
        return True
    except Exception as e:
        logger.error(f"  ✗ Failed to fill {selector}: {e}")
        return False

async def generate_slide_01_org_registration(page, recorder):
    """
    Slide 1: Organization Registration (45s)

    Workflow:
    1. Navigate to homepage
    2. Click "Register Organization" button
    3. Fill registration form with demo data
    4. Submit form
    5. Show success message
    """
    logger.info("=" * 80)
    logger.info("📺 SLIDE 1: Organization Registration")
    logger.info("=" * 80)

    output_file = VIDEOS_DIR / "slide_01_org_registration.mp4"

    try:
        # Start recording
        recorder.start_recording(output_file)
        await asyncio.sleep(2)  # Wait for recording to stabilize

        # Step 1: Navigate to homepage (0-5s)
        logger.info("Step 1: Navigating to homepage...")
        await page.goto(f"{BASE_URL}/html/index.html",
                       wait_until='networkidle',
                       timeout=30000)
        await remove_privacy_banners(page)
        await asyncio.sleep(2)

        # Step 2: Click "Register Organization" button (5-8s)
        logger.info("Step 2: Clicking 'Register Organization' button...")
        try:
            # Look for the register button
            register_btn = await page.wait_for_selector(
                'a[href*="organization-registration"], button:has-text("Register"), a:has-text("Register")',
                timeout=5000
            )
            await register_btn.click()
            logger.info("  ✓ Clicked register button")
        except Exception as e:
            logger.warning(f"  ⚠ Register button not found, navigating directly: {e}")
            await page.goto(f"{BASE_URL}/html/organization-registration.html",
                           wait_until='networkidle',
                           timeout=30000)

        await asyncio.sleep(2)
        await remove_privacy_banners(page)

        # Step 3: Fill out registration form (8-35s)
        logger.info("Step 3: Filling registration form...")

        # Organization details
        await fill_form_field(page, '#orgName', DEMO_ORG_DATA['org_name'])
        await asyncio.sleep(0.5)

        await fill_form_field(page, '#orgSlug', DEMO_ORG_DATA['org_slug'])
        await asyncio.sleep(0.5)

        await fill_form_field(page, '#contactEmail', DEMO_ORG_DATA['contact_email'])
        await asyncio.sleep(0.5)

        await fill_form_field(page, '#contactPhone', DEMO_ORG_DATA['contact_phone'])
        await asyncio.sleep(0.5)

        # Scroll to see more fields
        await smooth_scroll(page, 300, 800)

        await fill_form_field(page, '#address', DEMO_ORG_DATA['address'])
        await asyncio.sleep(0.5)

        await fill_form_field(page, '#city', DEMO_ORG_DATA['city'])
        await asyncio.sleep(0.5)

        await fill_form_field(page, '#state', DEMO_ORG_DATA['state'])
        await asyncio.sleep(0.5)

        await fill_form_field(page, '#postalCode', DEMO_ORG_DATA['postal_code'])
        await asyncio.sleep(0.5)

        # Scroll to admin section
        await smooth_scroll(page, 600, 800)

        # Admin details
        await fill_form_field(page, '#adminName', DEMO_ORG_DATA['admin_name'])
        await asyncio.sleep(0.5)

        await fill_form_field(page, '#adminEmail', DEMO_ORG_DATA['admin_email'])
        await asyncio.sleep(0.5)

        await fill_form_field(page, '#adminPassword', DEMO_ORG_DATA['admin_password'], delay_ms=30)
        await asyncio.sleep(0.5)

        await fill_form_field(page, '#confirmPassword', DEMO_ORG_DATA['admin_password'], delay_ms=30)
        await asyncio.sleep(1)

        # Step 4: Submit form (35-38s)
        logger.info("Step 4: Submitting registration form...")
        await smooth_scroll(page, 800, 600)

        try:
            submit_btn = await page.wait_for_selector(
                'button[type="submit"], button:has-text("Register"), button:has-text("Submit")',
                timeout=5000
            )
            await submit_btn.click()
            logger.info("  ✓ Clicked submit button")
            await asyncio.sleep(3)
        except Exception as e:
            logger.error(f"  ✗ Submit button not found: {e}")

        # Step 5: Show success/confirmation (38-45s)
        logger.info("Step 5: Showing confirmation...")

        # Wait for success message or redirect
        try:
            success_msg = await page.wait_for_selector(
                '.alert-success, .success-message, [class*="success"]',
                timeout=5000
            )
            logger.info("  ✓ Success message displayed")
        except Exception:
            logger.info("  ℹ No success message found (may have redirected)")

        # Hold on final frame
        await asyncio.sleep(4)

        logger.info("✅ Slide 1 generation complete!")

    except Exception as e:
        logger.error(f"❌ Slide 1 generation failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Stop recording
        recorder.stop_recording()

async def main():
    """Main execution"""
    logger.info("=" * 80)
    logger.info("🎬 DEMO SLIDE 1 GENERATION: Organization Registration")
    logger.info("=" * 80)
    logger.info(f"Output: {VIDEOS_DIR / 'slide_01_org_registration.mp4'}")
    logger.info(f"Duration: {SLIDE_DURATION} seconds")
    logger.info("=" * 80)

    # Ensure output directory exists
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

    # Initialize recorder
    recorder = FFmpegRecorder()

    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(
            headless=False,  # Show browser for DISPLAY :99
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled',
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
            # Generate Slide 1
            await generate_slide_01_org_registration(page, recorder)

            logger.info("")
            logger.info("=" * 80)
            logger.info("✅ SLIDE 1 GENERATION COMPLETE")
            logger.info("=" * 80)

            output_file = VIDEOS_DIR / "slide_01_org_registration.mp4"
            if output_file.exists():
                size_mb = output_file.stat().st_size / (1024 * 1024)
                logger.info(f"✅ Video saved: {output_file}")
                logger.info(f"   Size: {size_mb:.2f} MB")
            else:
                logger.error(f"❌ Video file not created: {output_file}")

        finally:
            await context.close()
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
