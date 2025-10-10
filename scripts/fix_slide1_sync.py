#!/usr/bin/env python3
"""
Fix Slide 1 Video/Audio Sync Issue
Ensures video and audio start together by waiting for page load before recording
"""
import asyncio
import subprocess
from pathlib import Path
from playwright.async_api import async_playwright
import logging

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
            logger.info(f"   🗑️  Removed {removed} privacy elements")
        await asyncio.sleep(0.5)
    except:
        pass

async def smooth_scroll(page, target_y, duration_ms=1500):
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

async def generate_slide1():
    """Generate slide 1 with proper video/audio sync"""
    logger.info("📺 Slide 1: Introduction (SYNC FIX)")

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

        # Navigate to homepage
        await page.goto(f"{BASE_URL}/html/index.html", wait_until='networkidle', timeout=15000)

        # Remove privacy banners
        await remove_privacy_banners(page)
        await asyncio.sleep(1)

        # Wait for ALL images and resources to load
        await page.evaluate("""
            async () => {
                // Wait for all images
                const images = Array.from(document.images);
                await Promise.all(images.map(img => {
                    if (img.complete) return Promise.resolve();
                    return new Promise(resolve => {
                        img.onload = resolve;
                        img.onerror = resolve;
                    });
                }));

                // Give extra time for animations and fonts
                await new Promise(resolve => setTimeout(resolve, 2000));
            }
        """)

        logger.info("   ✅ Page fully loaded and rendered")

        # Start recording NOW (page is fully visible)
        recorder = FFmpegRecorder()
        output_file = VIDEOS_DIR / "slide_01_introduction.mp4"
        recorder.start_recording(output_file)

        # Wait for FFmpeg to initialize
        await asyncio.sleep(3)

        # Smooth scroll through homepage content (20 seconds to match audio)
        await smooth_scroll(page, 400, duration_ms=6000)
        await asyncio.sleep(3)
        await smooth_scroll(page, 800, duration_ms=6000)
        await asyncio.sleep(3)
        await smooth_scroll(page, 0, duration_ms=2000)
        await asyncio.sleep(2)

        # Stop recording
        recorder.stop_recording()

        await browser.close()

    logger.info("✅ Slide 1 complete (SYNCED)")

async def main():
    print("="*80)
    print("🔧 Fixing Slide 1 Video/Audio Sync")
    print("="*80)

    await generate_slide1()

    # Verify duration
    import subprocess
    result = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
         '-of', 'default=noprint_wrappers=1:nokey=1',
         str(VIDEOS_DIR / "slide_01_introduction.mp4")],
        capture_output=True, text=True
    )
    duration = float(result.stdout.strip())

    print(f"\n✅ New video duration: {duration:.1f}s (target: ~20s)")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(main())
