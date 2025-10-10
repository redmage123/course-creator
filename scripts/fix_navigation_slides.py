#!/usr/bin/env python3
"""
Fix Navigation for Demo Slides
Regenerate slides 3-13 with robust navigation
"""
import asyncio
import subprocess
import sys
import os
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

async def navigate_and_wait(page, url, description="page"):
    """Robust navigation with multiple fallbacks"""
    logger.info(f"📍 Navigating to {description}: {url}")
    try:
        # Try networkidle first (2s timeout for idle)
        await page.goto(url, wait_until='networkidle', timeout=10000)
        logger.info(f"✅ Loaded ({description})")
    except Exception as e1:
        logger.warning(f"⚠️  networkidle failed: {e1}, trying domcontentloaded...")
        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=10000)
            await asyncio.sleep(2)  # Extra wait for JS
            logger.info(f"✅ Loaded ({description}) via domcontentloaded")
        except Exception as e2:
            logger.error(f"❌ Navigation failed completely: {e2}")
            raise
    
    # Always remove privacy banners after nav
    await remove_privacy_banners(page)
    await asyncio.sleep(1)

async def remove_privacy_banners(page):
    """Aggressively remove privacy UI"""
    try:
        removed = await page.evaluate("""
            () => {
                let count = 0;
                // Remove by class/id patterns
                const patterns = ['privacy', 'cookie', 'consent', 'gdpr', 'banner', 'modal'];
                patterns.forEach(pattern => {
                    document.querySelectorAll(`[class*="${pattern}"], [id*="${pattern}"]`).forEach(el => {
                        el.remove();
                        count++;
                    });
                });
                // Remove overlays
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
    except Exception as e:
        logger.warning(f"Privacy banner removal failed: {e}")

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

# Fixed Slide 3 with robust navigation
async def slide_03_fixed(page, recorder):
    logger.info("📊 Slide 3: Projects & Tracks (FIXED)")
    
    # Navigate with fallback
    await navigate_and_wait(page, f"{BASE_URL}/html/org-admin-dashboard-modular.html", "org admin dashboard")
    await asyncio.sleep(2)
    
    recorder.start_recording(VIDEOS_DIR / "slide_03_projects_and_tracks.mp4")
    await asyncio.sleep(1)
    
    # Show dashboard overview
    await asyncio.sleep(3)
    
    # Click projects tab
    try:
        projects_tab = await page.wait_for_selector('a[data-tab="projects"], a[href="#projects"], .projects-tab', timeout=5000)
        await projects_tab.click()
        await asyncio.sleep(2)
        await smooth_scroll(page, 400, 1000)
        await asyncio.sleep(7)
    except:
        logger.warning("Projects tab not found, scrolling instead")
        await smooth_scroll(page, 400, 1000)
        await asyncio.sleep(10)
    
    # Click tracks tab
    try:
        tracks_tab = await page.wait_for_selector('a[data-tab="tracks"], a[href="#tracks"], .tracks-tab', timeout=5000)
        await tracks_tab.click()
        await asyncio.sleep(2)
        await smooth_scroll(page, 800, 1000)
        await asyncio.sleep(10)
    except:
        logger.warning("Tracks tab not found, scrolling instead")
        await smooth_scroll(page, 800, 1000)
        await asyncio.sleep(10)
    
    # Back to top
    await smooth_scroll(page, 200, 1000)
    await asyncio.sleep(3)
    
    recorder.stop_recording()
    logger.info("✅ Slide 3 complete")

async def main():
    print("🔧 Fixing Navigation for Slide 3")
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
        
        # Test slide 3 fix
        await slide_03_fixed(page, recorder)
        
        await asyncio.sleep(2)
        await browser.close()
    
    print("✅ Slide 3 regenerated!")

if __name__ == "__main__":
    asyncio.run(main())
