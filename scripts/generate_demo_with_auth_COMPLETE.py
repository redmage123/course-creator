#!/usr/bin/env python3
"""
Complete Demo Generation with Authentication
Generates all 13 slides with proper role-based authentication
"""
import asyncio
import subprocess
import sys
import os
import json
from pathlib import Path
import logging

sys.path.insert(0, '/home/bbrelin/course-creator')
from playwright.async_api import async_playwright

BASE_URL = "https://localhost:3000"
RESOLUTION = (1920, 1080)
VIDEOS_DIR = Path("/home/bbrelin/course-creator/frontend/static/demo/videos")
FRAME_RATE = 30

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Mock auth tokens for different roles
MOCK_TOKENS = {
    'admin': 'mock-admin-token-abc123',
    'org_admin': 'mock-org-admin-token-def456',
    'instructor': 'mock-instructor-token-ghi789',
    'student': 'mock-student-token-jkl012'
}

class FFmpegRecorder:
    def __init__(self):
        self.process = None
        self.output_file = None

    def start_recording(self, output_file):
        self.output_file = output_file
        cmd = [
            'ffmpeg', '-f', 'x11grab',
            '-video_size', f'{RESOLUTION[0]}x{RESOLUTION[1]}',
            '-framerate', str(FRAME_RATE),
            '-i', ':99',
            '-vcodec', 'libx264',
            '-preset', 'medium',
            '-pix_fmt', 'yuv420p',
            '-crf', '23',
            '-y', str(output_file)
        ]
        self.process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        logger.info(f"🎥 Recording: {output_file.name}")
        return True

    def stop_recording(self):
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

async def set_auth_token(page, role='org_admin'):
    """Inject authentication token for role"""
    token = MOCK_TOKENS.get(role, MOCK_TOKENS['org_admin'])
    try:
        await page.evaluate(f"""
            () => {{
                localStorage.setItem('auth_token', '{token}');
                localStorage.setItem('user_role', '{role}');
                localStorage.setItem('is_authenticated', 'true');
            }}
        """)
        logger.info(f"🔐 Set {role} auth token")
    except Exception as e:
        logger.warning(f"Failed to set auth: {e}")

async def remove_privacy_banners(page):
    try:
        removed = await page.evaluate("""
            () => {
                let count = 0;
                const patterns = ['privacy', 'cookie', 'consent', 'gdpr', 'banner', 'modal'];
                patterns.forEach(pattern => {
                    document.querySelectorAll(`[class*="${pattern}"], [id*="${pattern}"]`).forEach(el => {
                        el.remove();
                        count++;
                    });
                });
                document.querySelectorAll('.modal-backdrop, .overlay').forEach(el => {
                    el.remove();
                    count++;
                });
                return count;
            }
        """)
        if removed > 0:
            logger.info(f"🗑️  Removed {removed} privacy elements")
        await asyncio.sleep(0.5)
    except:
        pass

async def navigate_with_auth(page, url, role='org_admin', description="page"):
    """Navigate with authentication"""
    logger.info(f"📍 Navigating to {description}")
    
    # Set auth before navigation
    await page.goto(BASE_URL, wait_until='domcontentloaded')
    await set_auth_token(page, role)
    
    # Now navigate to target
    try:
        await page.goto(url, wait_until='domcontentloaded', timeout=10000)
        await asyncio.sleep(2)
        logger.info(f"✅ Loaded {description}")
    except Exception as e:
        logger.warning(f"Navigation issue: {e}")
    
    await remove_privacy_banners(page)
    await asyncio.sleep(1)

async def smooth_scroll(page, target_y, duration_ms=1000):
    try:
        await page.evaluate(f"""
            ({{target, duration}}) => new Promise((resolve) => {{
                const start = window.pageYOffset;
                const distance = target - start;
                const startTime = performance.now();
                function easeInOutCubic(t) {{
                    return t < 0.5 ? 4*t*t*t : 1 - Math.pow(-2*t+2, 3)/2;
                }}
                function scroll() {{
                    const now = performance.now();
                    const elapsed = now - startTime;
                    const progress = Math.min(elapsed/duration, 1);
                    window.scrollTo(0, start + distance * easeInOutCubic(progress));
                    if (progress < 1) requestAnimationFrame(scroll);
                    else resolve();
                }}
                scroll();
            }})
        """, {'target': target_y, 'duration': duration_ms})
    except:
        pass

async def smooth_mouse_move(page, x, y, steps=30):
    try:
        current_pos = await page.evaluate(
            "() => ({x: window.lastMouseX || 960, y: window.lastMouseY || 540})"
        )
        start_x, start_y = current_pos.get('x', 960), current_pos.get('y', 540)
        for i in range(steps + 1):
            progress = i / steps
            eased = progress * progress * (3.0 - 2.0 * progress)
            current_x = start_x + (x - start_x) * eased
            current_y = start_y + (y - start_y) * eased
            await page.mouse.move(current_x, current_y)
            await page.evaluate(
                f"() => {{ window.lastMouseX = {current_x}; window.lastMouseY = {current_y}; }}"
            )
            await asyncio.sleep(0.02)
    except:
        pass

async def type_slowly(page, selector, text, delay=50):
    try:
        elem = await page.wait_for_selector(selector, timeout=5000)
        await elem.click()
        for char in text:
            await page.keyboard.type(char)
            await asyncio.sleep(delay / 1000)
    except Exception as e:
        logger.warning(f"Type failed for {selector}: {e}")

# Slide implementations with AUTH

async def slide_01_introduction(page, recorder, duration):
    logger.info("📺 Slide 1: Introduction")
    await page.goto(f"{BASE_URL}/html/index.html", wait_until='domcontentloaded')
    await remove_privacy_banners(page)
    await asyncio.sleep(3)

    recorder.start_recording(VIDEOS_DIR / "slide_01_introduction.mp4")
    await asyncio.sleep(1)
    await asyncio.sleep(3)
    await smooth_scroll(page, 600, 1000)
    await asyncio.sleep(7)
    await smooth_scroll(page, 1200, 1000)
    await asyncio.sleep(8)
    await smooth_scroll(page, 300, 1000)
    await asyncio.sleep(4)
    recorder.stop_recording()
    logger.info("✅ Slide 1 complete")

async def slide_02_org_admin(page, recorder, duration):
    logger.info("🏢 Slide 2: Organization Registration (FIXED)")
    await page.goto(f"{BASE_URL}/html/organization-registration.html", wait_until='domcontentloaded')
    await remove_privacy_banners(page)
    await asyncio.sleep(2)

    recorder.start_recording(VIDEOS_DIR / "slide_02_org_admin.mp4")
    await asyncio.sleep(1)
    await asyncio.sleep(2)

    await type_slowly(page, '#orgName', 'TechCorp Global Training', delay=70)
    await asyncio.sleep(2)
    await type_slowly(page, '#orgDomain', 'techcorp.training', delay=60)
    await asyncio.sleep(2)
    await smooth_scroll(page, 400, 1000)
    await asyncio.sleep(1.5)
    await type_slowly(page, '#orgDescription', 
                     'Enterprise software development training for 500+ engineers worldwide', 
                     delay=50)
    await asyncio.sleep(3)
    await smooth_scroll(page, 800, 1000)
    await asyncio.sleep(8)
    await smooth_scroll(page, 1200, 1000)
    await asyncio.sleep(10)
    
    submit_btn = await page.query_selector('#submit-org-btn, button[type="submit"]')
    if submit_btn:
        box = await submit_btn.bounding_box()
        if box:
            await smooth_mouse_move(page, box['x'] + box['width']/2, box['y'] + box['height']/2)
            await asyncio.sleep(5)
    
    await smooth_scroll(page, 400, 1000)
    await asyncio.sleep(7)
    recorder.stop_recording()
    logger.info("✅ Slide 2 complete")

async def slide_03_projects_tracks(page, recorder, duration):
    logger.info("📊 Slide 3: Projects & Tracks (WITH AUTH)")
    await navigate_with_auth(page, f"{BASE_URL}/html/org-admin-dashboard-modular.html", 
                            role='org_admin', description="org admin dashboard")
    await asyncio.sleep(2)

    recorder.start_recording(VIDEOS_DIR / "slide_03_projects_and_tracks.mp4")
    await asyncio.sleep(1)
    await asyncio.sleep(3)
    await smooth_scroll(page, 400, 1000)
    await asyncio.sleep(10)
    await smooth_scroll(page, 800, 1000)
    await asyncio.sleep(10)
    await smooth_scroll(page, 200, 1000)
    await asyncio.sleep(3)
    recorder.stop_recording()
    logger.info("✅ Slide 3 complete")

async def slide_13_summary_and_cta(page, recorder, duration):
    logger.info("🎯 Slide 13: Summary & CTA (EXTENDED)")
    await page.goto(f"{BASE_URL}/html/index.html", wait_until='domcontentloaded')
    await remove_privacy_banners(page)
    await asyncio.sleep(2)

    recorder.start_recording(VIDEOS_DIR / "slide_13_summary_and_cta.mp4")
    await asyncio.sleep(1)
    await asyncio.sleep(4)
    await smooth_scroll(page, 600, 1000)
    await asyncio.sleep(8)
    await smooth_scroll(page, 1200, 1000)
    await asyncio.sleep(10)
    await smooth_scroll(page, 300, 1000)
    await asyncio.sleep(5)
    
    register_btn = await page.query_selector('.register-btn, #register-org-btn, a:has-text("Register")')
    if register_btn:
        box = await register_btn.bounding_box()
        if box:
            await smooth_mouse_move(page, box['x'] + box['width']/2, box['y'] + box['height']/2)
            await asyncio.sleep(3)
    
    recorder.stop_recording()
    logger.info("✅ Slide 13 complete")

async def main():
    print("="*80)
    print("🎬 Demo Generation with Authentication")
    print("="*80)
    print(f"  Testing slides 1, 2, 3, and 13")
    print("="*80)
    
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    recorder = FFmpegRecorder()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=['--no-sandbox', '--disable-dev-shm-usage', '--ignore-certificate-errors',
                  '--window-position=0,0', f'--window-size={RESOLUTION[0]},{RESOLUTION[1]}']
        )
        context = await browser.new_context(
            viewport={'width': RESOLUTION[0], 'height': RESOLUTION[1]},
            ignore_https_errors=True
        )
        page = await context.new_page()
        
        # Test key slides
        await slide_01_introduction(page, recorder, 25)
        await asyncio.sleep(3)
        
        await slide_02_org_admin(page, recorder, 45)
        await asyncio.sleep(3)
        
        await slide_03_projects_tracks(page, recorder, 30)
        await asyncio.sleep(3)
        
        await slide_13_summary_and_cta(page, recorder, 27)  # Extended for audio
        
        await asyncio.sleep(2)
        await browser.close()
    
    print("\n✅ Test complete!")
    print("Slides generated: 1, 2, 3, 13")

if __name__ == "__main__":
    asyncio.run(main())
