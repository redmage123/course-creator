#!/usr/bin/env python3
"""
Regenerate Failed Demo Slides (4, 6, 7, 8) with Improved Navigation Handling
"""

import asyncio
import subprocess
import sys
import os
import json
from pathlib import Path

sys.path.insert(0, '/home/bbrelin/course-creator')

from playwright.async_api import async_playwright

BASE_URL = "https://localhost:3000"
RESOLUTION = (1920, 1080)
VIDEOS_DIR = Path("/home/bbrelin/course-creator/frontend/static/demo/videos")

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FFmpegRecorder:
    """Simple FFmpeg-based recorder"""

    def __init__(self):
        self.process = None

    def start_recording(self, output_file):
        """Start FFmpeg recording"""
        cmd = [
            'ffmpeg', '-f', 'x11grab',
            '-video_size', f'{RESOLUTION[0]}x{RESOLUTION[1]}',
            '-framerate', '30',
            '-i', ':99',
            '-vcodec', 'libx264',
            '-preset', 'medium',
            '-pix_fmt', 'yuv420p',
            '-y', str(output_file)
        ]
        self.process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"  🎥 Recording started: {os.path.basename(output_file)}")
        return True

    def stop_recording(self):
        """Stop FFmpeg recording"""
        if self.process:
            self.process.terminate()
            self.process.wait()
            print(f"  ⏹️  Recording stopped")
            return True
        return False

async def remove_privacy_banners(page):
    """Remove any privacy consent banners"""
    try:
        await page.evaluate("""
            () => {
                const banners = document.querySelectorAll('[class*="privacy"], [class*="cookie"], [class*="consent"], [class*="gdpr"]');
                banners.forEach(b => {
                    if (b && b.parentElement) {
                        b.remove();
                    }
                });
            }
        """)
        await asyncio.sleep(0.5)
    except Exception as e:
        logger.warning(f"Privacy banner removal error: {e}")

async def smooth_scroll(page, target_y, duration_ms=1000):
    """Smooth scroll with easing"""
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

                    requestAnimationFrame(scroll);
                }});
            }}
        """, {"target": target_y, "duration": duration_ms})
    except Exception as e:
        logger.warning(f"Smooth scroll error: {e}")

async def smooth_mouse_move(page, x, y, steps=30):
    """Move mouse smoothly with easing"""
    try:
        current_pos = await page.evaluate("() => ({ x: window.lastMouseX || 960, y: window.lastMouseY || 540 })")
        start_x = current_pos.get('x', 960)
        start_y = current_pos.get('y', 540)

        for i in range(steps + 1):
            progress = i / steps
            eased = progress * progress * (3.0 - 2.0 * progress)  # Ease in-out
            current_x = start_x + (x - start_x) * eased
            current_y = start_y + (y - start_y) * eased
            await page.mouse.move(current_x, current_y)

            # Save position
            await page.evaluate(f"() => {{ window.lastMouseX = {current_x}; window.lastMouseY = {current_y}; }}")
            await asyncio.sleep(0.02)
    except Exception as e:
        logger.warning(f"Mouse move error: {e}")

async def slide_04_projects_tracks(page, recorder, duration):
    """Slide 4: Projects and tracks - FIXED"""
    logger.info("📄 Loading org admin dashboard...")

    # Use networkidle and longer timeout
    try:
        await page.goto(f"{BASE_URL}/html/org-admin-dashboard-modular.html",
                       wait_until='networkidle',
                       timeout=60000)
    except Exception as e:
        logger.warning(f"Navigation warning: {e}, continuing anyway...")
        await asyncio.sleep(5)

    await remove_privacy_banners(page)
    await asyncio.sleep(5)  # Extra wait for page stability

    recorder.start_recording(VIDEOS_DIR / "slide_04_projects_and_tracks.mp4")
    await asyncio.sleep(2)

    await asyncio.sleep(3)
    await smooth_scroll(page, 400, 1000)
    await asyncio.sleep(10)

    await smooth_scroll(page, 800, 1000)
    await asyncio.sleep(10)

    await smooth_scroll(page, 1100, 1000)
    await asyncio.sleep(8)

    await smooth_scroll(page, 600, 1000)
    await asyncio.sleep(8)

    recorder.stop_recording()
    logger.info("✅ Slide 4 complete")

async def slide_06_create_course_ai(page, recorder, duration):
    """Slide 6: Create course with AI assistance - FIXED"""
    logger.info("📄 Loading instructor dashboard...")

    try:
        await page.goto(f"{BASE_URL}/html/instructor-dashboard-modular.html",
                       wait_until='networkidle',
                       timeout=60000)
    except Exception as e:
        logger.warning(f"Navigation warning: {e}, continuing anyway...")
        await asyncio.sleep(5)

    await remove_privacy_banners(page)
    await asyncio.sleep(5)

    recorder.start_recording(VIDEOS_DIR / "slide_06_create_course_with_ai.mp4")
    await asyncio.sleep(2)

    await asyncio.sleep(4)
    await smooth_scroll(page, 300, 1000)
    await asyncio.sleep(12)

    await smooth_scroll(page, 700, 1000)
    await asyncio.sleep(14)

    await smooth_scroll(page, 1100, 1000)
    await asyncio.sleep(14)

    await smooth_scroll(page, 500, 1000)
    await asyncio.sleep(10)

    await smooth_scroll(page, 0, 1000)
    await asyncio.sleep(6)

    recorder.stop_recording()
    logger.info("✅ Slide 6 complete")

async def slide_07_enroll_employees(page, recorder, duration):
    """Slide 7: Enroll employees in tracks - FIXED"""
    logger.info("📄 Loading org admin for enrollment...")

    try:
        await page.goto(f"{BASE_URL}/html/org-admin-dashboard-modular.html",
                       wait_until='networkidle',
                       timeout=60000)
    except Exception as e:
        logger.warning(f"Navigation warning: {e}, continuing anyway...")
        await asyncio.sleep(5)

    await remove_privacy_banners(page)
    await asyncio.sleep(5)

    recorder.start_recording(VIDEOS_DIR / "slide_07_enroll_employees.mp4")
    await asyncio.sleep(2)

    await asyncio.sleep(4)
    await smooth_scroll(page, 500, 1000)
    await asyncio.sleep(14)

    await smooth_scroll(page, 1000, 1000)
    await asyncio.sleep(14)

    await smooth_scroll(page, 200, 1000)
    await asyncio.sleep(7)

    recorder.stop_recording()
    logger.info("✅ Slide 7 complete")

async def slide_08_student_experience(page, recorder, duration):
    """Slide 8: Student dashboard and learning experience - FIXED"""
    logger.info("📄 Loading student dashboard...")

    try:
        await page.goto(f"{BASE_URL}/html/student-dashboard-modular.html",
                       wait_until='networkidle',
                       timeout=60000)
    except Exception as e:
        logger.warning(f"Navigation warning: {e}, continuing anyway...")
        await asyncio.sleep(5)

    await remove_privacy_banners(page)
    await asyncio.sleep(5)

    recorder.start_recording(VIDEOS_DIR / "slide_08_student_experience.mp4")
    await asyncio.sleep(2)

    await asyncio.sleep(4)
    await smooth_scroll(page, 300, 1000)
    await asyncio.sleep(10)

    await smooth_scroll(page, 700, 1000)
    await asyncio.sleep(12)

    await smooth_scroll(page, 1000, 1000)
    await asyncio.sleep(10)

    await smooth_scroll(page, 400, 1000)
    await asyncio.sleep(8)

    recorder.stop_recording()
    logger.info("✅ Slide 8 complete")

async def main():
    print("="*70)
    print("🎬 REGENERATING FAILED DEMO SLIDES (4, 6, 7, 8)")
    print("  Using Playwright + FFmpeg with improved navigation")
    print("  H.264 encoding, 1920x1080, 30fps")
    print("="*70)
    print()

    # Load slide definitions
    with open('/home/bbrelin/course-creator/scripts/demo_narration_scripts.json', 'r') as f:
        data = json.load(f)

    slides = [
        (4, "Projects & Tracks", slide_04_projects_tracks, data['slides'][3]['duration']),
        (6, "Create Course with AI", slide_06_create_course_ai, data['slides'][5]['duration']),
        (7, "Enroll Employees", slide_07_enroll_employees, data['slides'][6]['duration']),
        (8, "Student Experience", slide_08_student_experience, data['slides'][7]['duration']),
    ]

    recorder = FFmpegRecorder()

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

        for slide_num, slide_title, slide_func, duration in slides:
            print(f"\n🎥 Slide {slide_num}/10: {slide_title}")
            print(f"   Duration: {duration}s")

            try:
                await slide_func(page, recorder, duration)

                # Verify file was created
                await asyncio.sleep(2)
                output_file = list(VIDEOS_DIR.glob(f"slide_{str(slide_num).zfill(2)}*.mp4"))[0]
                if output_file.exists():
                    size_mb = output_file.stat().st_size / (1024 * 1024)
                    print(f"  ✅ Created: {output_file.name} ({size_mb:.2f} MB)")
                else:
                    print(f"  ❌ Failed: {slide_title}")
            except Exception as e:
                print(f"  ⚠️  Error: {e}")

            # Pause between slides
            if slide_num < 8:
                await asyncio.sleep(3)

        await context.close()
        await browser.close()

    print("\n" + "="*70)
    print("✅ FAILED SLIDES REGENERATED")
    print("="*70)
    print(f"\nVideos saved to: {VIDEOS_DIR}")
    print("\nVerify all slides at: https://localhost:3000/html/demo-player.html")

if __name__ == "__main__":
    asyncio.run(main())
