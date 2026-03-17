#!/usr/bin/env python3
"""
Generate Demo Videos with Playwright + OBS Studio

Features:
- OBS Studio for high-quality recording
- Playwright for browser automation
- Visible mouse cursor with smooth movements
- Form interactions and animations
- No black screens
"""

import json
import os
import time
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright
from obswebsocket import obsws, requests as obs_requests
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = "https://localhost:3000"
VIDEOS_DIR = Path("/home/bbrelin/course-creator/frontend/static/demo/videos")
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

RESOLUTION = (1920, 1080)

# OBS WebSocket connection settings
OBS_HOST = "localhost"
OBS_PORT = 4455
OBS_PASSWORD = ""  # Set if you configured a password

class OBSRecorder:
    """OBS Studio recording controller"""

    def __init__(self):
        self.ws = None
        self.connected = False

    def connect(self):
        """Connect to OBS WebSocket server"""
        try:
            self.ws = obsws(OBS_HOST, OBS_PORT, OBS_PASSWORD)
            self.ws.connect()
            self.connected = True
            logger.info("✅ Connected to OBS WebSocket")

            # Get OBS version
            version = self.ws.call(obs_requests.GetVersion())
            logger.info(f"   OBS Version: {version.getObsVersion()}")

        except Exception as e:
            logger.error(f"❌ Failed to connect to OBS: {e}")
            logger.error("   Make sure OBS is running with WebSocket server enabled")
            logger.error("   In OBS: Tools > WebSocket Server Settings")
            raise

    def disconnect(self):
        """Disconnect from OBS"""
        if self.ws:
            self.ws.disconnect()
            logger.info("Disconnected from OBS")

    def start_recording(self, output_filename):
        """Start OBS recording"""
        if not self.connected:
            raise Exception("Not connected to OBS")

        try:
            # Set output filename
            self.ws.call(obs_requests.SetRecordingFolder(str(VIDEOS_DIR)))

            # Start recording
            self.ws.call(obs_requests.StartRecord())
            logger.info(f"🎥 Recording started: {output_filename}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to start recording: {e}")
            return False

    def stop_recording(self):
        """Stop OBS recording"""
        if not self.connected:
            return False

        try:
            self.ws.call(obs_requests.StopRecord())
            logger.info("⏹️  Recording stopped")

            # Wait for file to be written
            time.sleep(2)
            return True

        except Exception as e:
            logger.error(f"❌ Failed to stop recording: {e}")
            return False

    def get_recording_status(self):
        """Check if currently recording"""
        try:
            status = self.ws.call(obs_requests.GetRecordStatus())
            return status.getOutputActive()
        except:
            return False

async def remove_privacy_banners(page):
    """Remove all privacy/GDPR modals"""
    await page.evaluate("""
        () => {
            const modal = document.getElementById('privacyModal');
            if (modal) modal.remove();

            document.querySelectorAll('[class*="modal"], [class*="overlay"], [class*="backdrop"]').forEach(el => {
                if (el.style.display !== 'none' && el.id !== 'ai-tour-guide-panel') el.remove();
            });

            document.querySelectorAll('[id*="cookie"], [id*="privacy"], [id*="consent"]').forEach(el => {
                el.remove();
            });
        }
    """)

async def smooth_scroll(page, target_y, duration=1000):
    """Smooth scroll to target position"""
    await page.evaluate(f"""
        () => {{
            window.scrollTo({{
                top: {target_y},
                behavior: 'smooth'
            }});
        }}
    """)
    await asyncio.sleep(duration / 1000)

async def smooth_mouse_move(page, x, y, steps=30):
    """Move mouse smoothly to target position"""
    try:
        # Get current position or default to center
        current_pos = await page.evaluate("() => ({ x: window.lastMouseX || 960, y: window.lastMouseY || 540 })")
        start_x = current_pos.get('x', 960)
        start_y = current_pos.get('y', 540)

        for i in range(steps + 1):
            progress = i / steps
            # Ease in-out
            eased = progress * progress * (3.0 - 2.0 * progress)
            current_x = start_x + (x - start_x) * eased
            current_y = start_y + (y - start_y) * eased
            await page.mouse.move(current_x, current_y)
            await asyncio.sleep(0.02)

        # Store last position
        await page.evaluate(f"() => {{ window.lastMouseX = {x}; window.lastMouseY = {y}; }}")

    except Exception as e:
        logger.warning(f"Mouse move error: {e}")

async def type_slowly(page, selector, text, delay=80):
    """Type text slowly with realistic delays"""
    try:
        element = await page.query_selector(selector)
        if element:
            # Move mouse to element first
            box = await element.bounding_box()
            if box:
                await smooth_mouse_move(page, box['x'] + 50, box['y'] + box['height']/2)
                await asyncio.sleep(0.3)

            await element.click()
            await asyncio.sleep(0.3)

            for char in text:
                await element.type(char, delay=delay)

        else:
            logger.warning(f"Element not found: {selector}")
    except Exception as e:
        logger.warning(f"Type error for {selector}: {e}")

# ============================================================================
# SLIDE WORKFLOWS
# ============================================================================

async def slide_01_introduction(page, recorder, duration):
    """Slide 1: Introduction - Platform overview"""
    logger.info("📄 Loading homepage...")
    await page.goto(BASE_URL, wait_until='domcontentloaded', timeout=30000)
    await remove_privacy_banners(page)
    await asyncio.sleep(3)

    # Start recording AFTER page is loaded
    recorder.start_recording("slide_01_introduction.mp4")
    await asyncio.sleep(1)

    # Show homepage
    await smooth_scroll(page, 0, 500)
    await asyncio.sleep(3)

    # Scroll to show value proposition
    await smooth_scroll(page, 400, 1000)
    await asyncio.sleep(5)

    await smooth_scroll(page, 800, 1000)
    await asyncio.sleep(6)

    # Back to top showing CTA
    await smooth_scroll(page, 300, 1000)
    await asyncio.sleep(5)

    await smooth_scroll(page, 0, 1000)
    await asyncio.sleep(5)

    recorder.stop_recording()
    logger.info("✅ Slide 1 complete")

async def slide_02_getting_started(page, recorder, duration):
    """Slide 2: Show how to get started"""
    logger.info("📄 Staying on homepage for getting started...")
    await asyncio.sleep(1)

    recorder.start_recording("slide_02_getting_started.mp4")
    await asyncio.sleep(1)

    # Scroll to show Register Organization button
    await smooth_scroll(page, 400, 1000)
    await asyncio.sleep(3)

    # Find and hover over Register Organization link
    try:
        register_link = await page.query_selector('a:has-text("Register Organization")')
        if register_link:
            box = await register_link.bounding_box()
            if box:
                await smooth_mouse_move(page, box['x'] + box['width']/2, box['y'] + box['height']/2)
                await asyncio.sleep(5)

                # Highlight with a subtle move
                await smooth_mouse_move(page, box['x'] + box['width']/2 + 10, box['y'] + box['height']/2)
                await asyncio.sleep(2)
    except Exception as e:
        logger.warning(f"Register link hover error: {e}")

    await smooth_scroll(page, 600, 1000)
    await asyncio.sleep(5)

    await smooth_scroll(page, 300, 1000)
    await asyncio.sleep(4)

    recorder.stop_recording()
    logger.info("✅ Slide 2 complete")

async def slide_03_create_organization(page, recorder, duration):
    """Slide 3: Fill organization registration form"""
    logger.info("📄 Loading organization registration...")
    await page.goto(f"{BASE_URL}/html/organization-registration.html", wait_until='domcontentloaded', timeout=30000)
    await remove_privacy_banners(page)
    await asyncio.sleep(3)

    recorder.start_recording("slide_03_create_organization.mp4")
    await asyncio.sleep(1)

    # Show form
    await asyncio.sleep(2)

    # Fill organization name
    await type_slowly(page, '#organization-name', 'TechCorp Global Training', delay=80)
    await asyncio.sleep(2)

    # Fill website
    await type_slowly(page, '#organization-website', 'https://techcorp.training', delay=60)
    await asyncio.sleep(2)

    # Scroll to description
    await smooth_scroll(page, 400, 1000)
    await asyncio.sleep(2)

    # Fill description
    await type_slowly(page, '#organization-description', 'Enterprise software development training for 500+ engineers', delay=50)
    await asyncio.sleep(3)

    # Scroll to show more of form
    await smooth_scroll(page, 700, 1000)
    await asyncio.sleep(5)

    # Scroll to submit button area
    await smooth_scroll(page, 900, 1000)
    await asyncio.sleep(5)

    # Move mouse to submit area
    await smooth_mouse_move(page, 960, 850)
    await asyncio.sleep(5)

    recorder.stop_recording()
    logger.info("✅ Slide 3 complete")

async def slide_04_projects_tracks(page, recorder, duration):
    """Slide 4: Projects and tracks"""
    logger.info("📄 Loading org admin dashboard...")
    await page.goto(f"{BASE_URL}/html/org-admin-dashboard-modular.html", wait_until='domcontentloaded', timeout=30000)
    await remove_privacy_banners(page)
    await asyncio.sleep(3)

    recorder.start_recording("slide_04_projects_tracks.mp4")
    await asyncio.sleep(1)

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

async def slide_05_assign_instructors(page, recorder, duration):
    """Slide 5: Assign instructors to tracks"""
    logger.info("📄 Staying on org admin dashboard...")
    await asyncio.sleep(1)

    recorder.start_recording("slide_05_assign_instructors.mp4")
    await asyncio.sleep(1)

    await asyncio.sleep(3)
    await smooth_scroll(page, 500, 1000)
    await asyncio.sleep(12)

    await smooth_scroll(page, 900, 1000)
    await asyncio.sleep(12)

    await smooth_scroll(page, 300, 1000)
    await asyncio.sleep(7)

    recorder.stop_recording()
    logger.info("✅ Slide 5 complete")

async def slide_06_create_course_ai(page, recorder, duration):
    """Slide 6: Create course with AI assistance"""
    logger.info("📄 Loading instructor dashboard...")
    await page.goto(f"{BASE_URL}/html/instructor-dashboard-modular.html", wait_until='domcontentloaded', timeout=30000)
    await remove_privacy_banners(page)
    await asyncio.sleep(3)

    recorder.start_recording("slide_06_create_course_ai.mp4")
    await asyncio.sleep(1)

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
    """Slide 7: Enroll employees in tracks"""
    logger.info("📄 Loading org admin for enrollment...")
    await page.goto(f"{BASE_URL}/html/org-admin-dashboard-modular.html", wait_until='domcontentloaded', timeout=30000)
    await remove_privacy_banners(page)
    await asyncio.sleep(3)

    recorder.start_recording("slide_07_enroll_employees.mp4")
    await asyncio.sleep(1)

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
    """Slide 8: Student dashboard and learning experience"""
    logger.info("📄 Loading student dashboard...")
    await page.goto(f"{BASE_URL}/html/student-dashboard-modular.html", wait_until='domcontentloaded', timeout=30000)
    await remove_privacy_banners(page)
    await asyncio.sleep(3)

    recorder.start_recording("slide_08_student_experience.mp4")
    await asyncio.sleep(1)

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

async def slide_09_ai_assistant(page, recorder, duration):
    """Slide 9: AI assistant and contact capture"""
    logger.info("📄 Loading demo player with AI assistant...")
    await page.goto(f"{BASE_URL}/html/demo-player.html", wait_until='domcontentloaded', timeout=30000)
    await remove_privacy_banners(page)
    await asyncio.sleep(3)

    recorder.start_recording("slide_09_ai_assistant.mp4")
    await asyncio.sleep(1)

    await asyncio.sleep(3)

    # Try to find and click AI chatbot button
    try:
        ai_button = await page.query_selector('#ai-tour-guide-trigger')
        if ai_button:
            box = await ai_button.bounding_box()
            if box:
                await smooth_mouse_move(page, box['x'] + box['width']/2, box['y'] + box['height']/2)
                await asyncio.sleep(2)
                await ai_button.click()
                await asyncio.sleep(3)

                # Type a question
                await type_slowly(page, '#ai-guide-input', 'How does SSO integration work?', delay=80)
                await asyncio.sleep(5)

                # Simulate send (if there's a send button)
                try:
                    send_btn = await page.query_selector('#ai-guide-send')
                    if send_btn:
                        await send_btn.click()
                        await asyncio.sleep(8)
                except:
                    pass

                # Type another message
                await page.fill('#ai-guide-input', '')
                await asyncio.sleep(1)
                await type_slowly(page, '#ai-guide-input', 'I want to schedule a demo', delay=80)
                await asyncio.sleep(5)

    except Exception as e:
        logger.warning(f"AI assistant interaction error: {e}")

    await asyncio.sleep(10)

    recorder.stop_recording()
    logger.info("✅ Slide 9 complete")

async def slide_10_summary(page, recorder, duration):
    """Slide 10: Summary and call to action"""
    logger.info("📄 Loading homepage for summary...")
    await page.goto(BASE_URL, wait_until='domcontentloaded', timeout=30000)
    await remove_privacy_banners(page)
    await asyncio.sleep(3)

    recorder.start_recording("slide_10_summary.mp4")
    await asyncio.sleep(1)

    await asyncio.sleep(4)
    await smooth_scroll(page, 400, 1000)
    await asyncio.sleep(8)

    await smooth_scroll(page, 800, 1000)
    await asyncio.sleep(8)

    await smooth_scroll(page, 300, 1000)
    await asyncio.sleep(5)

    await smooth_scroll(page, 0, 1000)
    await asyncio.sleep(4)

    recorder.stop_recording()
    logger.info("✅ Slide 10 complete")

# ============================================================================
# MAIN EXECUTION
# ============================================================================

async def main():
    print("="*70)
    print("🎬 GENERATING DEMO VIDEOS - Playwright + OBS Studio")
    print("  ✓ OBS Studio high-quality recording")
    print("  ✓ Visible mouse cursor")
    print("  ✓ Smooth animations")
    print("  ✓ Form interactions")
    print("="*70)
    print()

    # Load slide definitions
    with open('/home/bbrelin/course-creator/scripts/demo_narration_scripts.json', 'r') as f:
        data = json.load(f)

    # Initialize OBS recorder
    recorder = OBSRecorder()
    recorder.connect()

    slides = [
        (1, "Introduction", slide_01_introduction, data['slides'][0]['duration']),
        (2, "Getting Started", slide_02_getting_started, data['slides'][1]['duration']),
        (3, "Create Organization", slide_03_create_organization, data['slides'][2]['duration']),
        (4, "Projects & Tracks", slide_04_projects_tracks, data['slides'][3]['duration']),
        (5, "Assign Instructors", slide_05_assign_instructors, data['slides'][4]['duration']),
        (6, "Create Course with AI", slide_06_create_course_ai, data['slides'][5]['duration']),
        (7, "Enroll Employees", slide_07_enroll_employees, data['slides'][6]['duration']),
        (8, "Student Experience", slide_08_student_experience, data['slides'][7]['duration']),
        (9, "AI Assistant", slide_09_ai_assistant, data['slides'][8]['duration']),
        (10, "Summary", slide_10_summary, data['slides'][9]['duration']),
    ]

    try:
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
                ignore_https_errors=True,
                record_video_dir=None  # OBS handles recording
            )

            page = await context.new_page()

            for slide_num, slide_title, slide_func, duration in slides:
                print(f"\n🎥 Slide {slide_num}/10: {slide_title}")
                await slide_func(page, recorder, duration)

                # Small pause between slides
                if slide_num < len(slides):
                    await asyncio.sleep(2)

            await context.close()
            await browser.close()

    finally:
        recorder.disconnect()

    print("\n" + "="*70)
    print("✅ ALL 10 VIDEOS GENERATED")
    print("="*70)
    print(f"\nVideos saved to: {VIDEOS_DIR}")

if __name__ == "__main__":
    asyncio.run(main())
