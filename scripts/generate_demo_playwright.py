#!/usr/bin/env python3
"""
Generate Demo Videos with Playwright
- Visible mouse cursor
- Smooth animations and transitions
- Form filling interactions
- No black screens
"""

import json
import os
import time
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright
import subprocess

BASE_URL = "https://localhost:3000"
VIDEOS_DIR = Path("/home/bbrelin/course-creator/frontend/static/demo/videos")
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

RESOLUTION = (1920, 1080)
DISPLAY = os.environ.get('DISPLAY', ':99')

# Custom cursor CSS to make it visible
CURSOR_CSS = """
<style>
* {
    cursor: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32"><path fill="black" stroke="white" stroke-width="1" d="M3,3 L3,27 L11,19 L15,28 L18,27 L14,18 L23,18 Z"/></svg>') 0 0, auto !important;
}
</style>
"""

async def inject_visible_cursor(page):
    """Inject custom cursor styling to make it visible in recordings"""
    await page.add_style_tag(content=CURSOR_CSS)

async def remove_privacy_banners(page):
    """Remove all privacy/GDPR modals"""
    await page.evaluate("""
        () => {
            const modal = document.getElementById('privacyModal');
            if (modal) modal.remove();

            document.querySelectorAll('[class*="modal"], [class*="overlay"], [class*="backdrop"]').forEach(el => {
                if (el.style.display !== 'none') el.remove();
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

async def smooth_mouse_move(page, x, y, steps=20):
    """Move mouse smoothly to target position"""
    current_pos = await page.evaluate("() => ({ x: window.mouseX || 0, y: window.mouseY || 0 })")
    start_x = current_pos.get('x', 0)
    start_y = current_pos.get('y', 0)

    for i in range(steps + 1):
        progress = i / steps
        current_x = start_x + (x - start_x) * progress
        current_y = start_y + (y - start_y) * progress
        await page.mouse.move(current_x, current_y)
        await asyncio.sleep(0.02)

async def type_slowly(page, selector, text, delay=100):
    """Type text slowly with realistic delays"""
    element = await page.query_selector(selector)
    if element:
        await element.click()
        await asyncio.sleep(0.3)
        for char in text:
            await element.type(char, delay=delay)
    else:
        print(f"    ⚠️  Element not found: {selector}")

def start_recording(output_file, duration):
    """Start FFmpeg screen recording"""
    cmd = [
        'ffmpeg', '-f', 'x11grab',
        '-video_size', f'{RESOLUTION[0]}x{RESOLUTION[1]}',
        '-framerate', '30',
        '-i', DISPLAY,
        '-t', str(duration),
        '-vcodec', 'libx264',
        '-preset', 'medium',
        '-pix_fmt', 'yuv420p',
        '-y', str(output_file)
    ]
    return subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# ============================================================================
# SLIDE WORKFLOWS
# ============================================================================

async def slide_01_introduction(page, duration):
    """Slide 1: Introduction - Platform overview"""
    print("  📄 Loading homepage...")
    await page.goto(BASE_URL, wait_until='networkidle')
    await remove_privacy_banners(page)
    await inject_visible_cursor(page)
    await asyncio.sleep(2)

    print("  🎥 Recording...")
    recorder = start_recording(VIDEOS_DIR / "slide_01_introduction.mp4", duration)

    # Wait for recording to start
    await asyncio.sleep(1)

    # Show homepage
    await smooth_scroll(page, 0, 500)
    await asyncio.sleep(3)

    # Scroll to show features
    await smooth_scroll(page, 400, 1000)
    await asyncio.sleep(5)

    await smooth_scroll(page, 800, 1000)
    await asyncio.sleep(6)

    # Back to top
    await smooth_scroll(page, 300, 1000)
    await asyncio.sleep(5)

    await smooth_scroll(page, 0, 1000)
    await asyncio.sleep(5)

    recorder.wait()
    print("  ✅ Slide 1 complete")

async def slide_02_getting_started(page, duration):
    """Slide 2: Show how to get started"""
    print("  📄 Loading homepage for getting started...")
    await page.goto(BASE_URL, wait_until='networkidle')
    await remove_privacy_banners(page)
    await inject_visible_cursor(page)
    await asyncio.sleep(2)

    print("  🎥 Recording...")
    recorder = start_recording(VIDEOS_DIR / "slide_02_getting_started.mp4", duration)
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
    except:
        pass

    await smooth_scroll(page, 600, 1000)
    await asyncio.sleep(5)

    await smooth_scroll(page, 300, 1000)
    await asyncio.sleep(6)

    recorder.wait()
    print("  ✅ Slide 2 complete")

async def slide_03_create_organization(page, duration):
    """Slide 3: Fill organization registration form"""
    print("  📄 Loading organization registration...")
    await page.goto(f"{BASE_URL}/html/organization-registration.html", wait_until='networkidle')
    await remove_privacy_banners(page)
    await inject_visible_cursor(page)
    await asyncio.sleep(2)

    print("  🎥 Recording...")
    recorder = start_recording(VIDEOS_DIR / "slide_03_create_organization.mp4", duration)
    await asyncio.sleep(1)

    # Fill organization name
    await asyncio.sleep(2)
    try:
        org_name = await page.query_selector('#organization-name')
        if org_name:
            box = await org_name.bounding_box()
            if box:
                await smooth_mouse_move(page, box['x'] + 50, box['y'] + 15)
                await asyncio.sleep(1)
            await type_slowly(page, '#organization-name', 'TechCorp Global Training', delay=80)
            await asyncio.sleep(2)
    except Exception as e:
        print(f"    ⚠️  Form filling error: {e}")

    # Fill website
    try:
        website = await page.query_selector('#organization-website')
        if website:
            box = await website.bounding_box()
            if box:
                await smooth_mouse_move(page, box['x'] + 50, box['y'] + 15)
            await type_slowly(page, '#organization-website', 'https://techcorp.training', delay=60)
            await asyncio.sleep(2)
    except:
        pass

    # Scroll to description
    await smooth_scroll(page, 400, 1000)
    await asyncio.sleep(2)

    # Fill description
    try:
        desc = await page.query_selector('#organization-description')
        if desc:
            box = await desc.bounding_box()
            if box:
                await smooth_mouse_move(page, box['x'] + 50, box['y'] + 15)
            await type_slowly(page, '#organization-description', 'Enterprise software development training for 500+ engineers', delay=50)
            await asyncio.sleep(3)
    except:
        pass

    # Scroll to show more of form
    await smooth_scroll(page, 700, 1000)
    await asyncio.sleep(5)

    # Scroll to submit button area
    await smooth_scroll(page, 900, 1000)
    await asyncio.sleep(5)

    # Move mouse to submit area
    await smooth_mouse_move(page, 960, 850)
    await asyncio.sleep(5)

    recorder.wait()
    print("  ✅ Slide 3 complete")

async def slide_04_projects_tracks(page, duration):
    """Slide 4: Projects and tracks"""
    print("  📄 Loading org admin dashboard...")
    await page.goto(f"{BASE_URL}/html/org-admin-dashboard-modular.html", wait_until='networkidle')
    await remove_privacy_banners(page)
    await inject_visible_cursor(page)
    await asyncio.sleep(2)

    print("  🎥 Recording...")
    recorder = start_recording(VIDEOS_DIR / "slide_04_projects_tracks.mp4", duration)
    await asyncio.sleep(1)

    await asyncio.sleep(3)
    await smooth_scroll(page, 400, 1000)
    await asyncio.sleep(10)

    await smooth_scroll(page, 800, 1000)
    await asyncio.sleep(10)

    await smooth_scroll(page, 1100, 1000)
    await asyncio.sleep(8)

    await smooth_scroll(page, 600, 1000)
    await asyncio.sleep(9)

    recorder.wait()
    print("  ✅ Slide 4 complete")

async def slide_05_assign_instructors(page, duration):
    """Slide 5: Assign instructors to tracks"""
    print("  📄 Loading org admin dashboard for instructors...")
    await page.goto(f"{BASE_URL}/html/org-admin-dashboard-modular.html", wait_until='networkidle')
    await remove_privacy_banners(page)
    await inject_visible_cursor(page)
    await asyncio.sleep(2)

    print("  🎥 Recording...")
    recorder = start_recording(VIDEOS_DIR / "slide_05_assign_instructors.mp4", duration)
    await asyncio.sleep(1)

    await asyncio.sleep(3)
    await smooth_scroll(page, 500, 1000)
    await asyncio.sleep(12)

    await smooth_scroll(page, 900, 1000)
    await asyncio.sleep(12)

    await smooth_scroll(page, 300, 1000)
    await asyncio.sleep(8)

    recorder.wait()
    print("  ✅ Slide 5 complete")

async def slide_06_create_course_ai(page, duration):
    """Slide 6: Create course with AI assistance"""
    print("  📄 Loading instructor dashboard...")
    await page.goto(f"{BASE_URL}/html/instructor-dashboard-modular.html", wait_until='networkidle')
    await remove_privacy_banners(page)
    await inject_visible_cursor(page)
    await asyncio.sleep(2)

    print("  🎥 Recording...")
    recorder = start_recording(VIDEOS_DIR / "slide_06_create_course_ai.mp4", duration)
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

    recorder.wait()
    print("  ✅ Slide 6 complete")

async def slide_07_enroll_employees(page, duration):
    """Slide 7: Enroll employees in tracks"""
    print("  📄 Loading org admin for enrollment...")
    await page.goto(f"{BASE_URL}/html/org-admin-dashboard-modular.html", wait_until='networkidle')
    await remove_privacy_banners(page)
    await inject_visible_cursor(page)
    await asyncio.sleep(2)

    print("  🎥 Recording...")
    recorder = start_recording(VIDEOS_DIR / "slide_07_enroll_employees.mp4", duration)
    await asyncio.sleep(1)

    await asyncio.sleep(4)
    await smooth_scroll(page, 500, 1000)
    await asyncio.sleep(14)

    await smooth_scroll(page, 1000, 1000)
    await asyncio.sleep(14)

    await smooth_scroll(page, 200, 1000)
    await asyncio.sleep(8)

    recorder.wait()
    print("  ✅ Slide 7 complete")

async def slide_08_student_experience(page, duration):
    """Slide 8: Student dashboard and learning experience"""
    print("  📄 Loading student dashboard...")
    await page.goto(f"{BASE_URL}/html/student-dashboard-modular.html", wait_until='networkidle')
    await remove_privacy_banners(page)
    await inject_visible_cursor(page)
    await asyncio.sleep(2)

    print("  🎥 Recording...")
    recorder = start_recording(VIDEOS_DIR / "slide_08_student_experience.mp4", duration)
    await asyncio.sleep(1)

    await asyncio.sleep(4)
    await smooth_scroll(page, 300, 1000)
    await asyncio.sleep(10)

    await smooth_scroll(page, 700, 1000)
    await asyncio.sleep(12)

    await smooth_scroll(page, 1000, 1000)
    await asyncio.sleep(10)

    await smooth_scroll(page, 400, 1000)
    await asyncio.sleep(9)

    recorder.wait()
    print("  ✅ Slide 8 complete")

async def slide_09_ai_assistant(page, duration):
    """Slide 9: AI assistant and contact capture"""
    print("  📄 Loading demo player with AI assistant...")
    await page.goto(f"{BASE_URL}/html/demo-player.html", wait_until='networkidle')
    await remove_privacy_banners(page)
    await inject_visible_cursor(page)
    await asyncio.sleep(2)

    print("  🎥 Recording...")
    recorder = start_recording(VIDEOS_DIR / "slide_09_ai_assistant.mp4", duration)
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
    except:
        pass

    await asyncio.sleep(10)

    # Type a question
    try:
        ai_input = await page.query_selector('#ai-guide-input')
        if ai_input:
            await type_slowly(page, '#ai-guide-input', 'How does SSO integration work?', delay=80)
            await asyncio.sleep(5)
    except:
        pass

    await asyncio.sleep(15)

    # Type another message
    try:
        await page.fill('#ai-guide-input', '')
        await type_slowly(page, '#ai-guide-input', 'I want to schedule a demo', delay=80)
        await asyncio.sleep(5)
    except:
        pass

    await asyncio.sleep(10)

    recorder.wait()
    print("  ✅ Slide 9 complete")

async def slide_10_summary(page, duration):
    """Slide 10: Summary and call to action"""
    print("  📄 Loading homepage for summary...")
    await page.goto(BASE_URL, wait_until='networkidle')
    await remove_privacy_banners(page)
    await inject_visible_cursor(page)
    await asyncio.sleep(2)

    print("  🎥 Recording...")
    recorder = start_recording(VIDEOS_DIR / "slide_10_summary.mp4", duration)
    await asyncio.sleep(1)

    await asyncio.sleep(4)
    await smooth_scroll(page, 400, 1000)
    await asyncio.sleep(8)

    await smooth_scroll(page, 800, 1000)
    await asyncio.sleep(8)

    await smooth_scroll(page, 300, 1000)
    await asyncio.sleep(5)

    await smooth_scroll(page, 0, 1000)
    await asyncio.sleep(5)

    recorder.wait()
    print("  ✅ Slide 10 complete")

# ============================================================================
# MAIN EXECUTION
# ============================================================================

async def generate_slide(browser, slide_num, slide_func, duration):
    """Generate a single slide"""
    context = await browser.new_context(
        viewport={'width': RESOLUTION[0], 'height': RESOLUTION[1]},
        ignore_https_errors=True
    )
    page = await context.new_page()

    try:
        await slide_func(page, duration)
    finally:
        await context.close()

async def main():
    print("="*70)
    print("🎬 GENERATING DEMO VIDEOS - Playwright")
    print("  ✓ Visible mouse cursor")
    print("  ✓ Smooth animations")
    print("  ✓ Form interactions")
    print("="*70)
    print()

    # Load slide definitions
    with open('/home/bbrelin/course-creator/scripts/demo_narration_scripts.json', 'r') as f:
        data = json.load(f)

    slides = [
        (1, slide_01_introduction, data['slides'][0]['duration']),
        (2, slide_02_getting_started, data['slides'][1]['duration']),
        (3, slide_03_create_organization, data['slides'][2]['duration']),
        (4, slide_04_projects_tracks, data['slides'][3]['duration']),
        (5, slide_05_assign_instructors, data['slides'][4]['duration']),
        (6, slide_06_create_course_ai, data['slides'][5]['duration']),
        (7, slide_07_enroll_employees, data['slides'][6]['duration']),
        (8, slide_08_student_experience, data['slides'][7]['duration']),
        (9, slide_09_ai_assistant, data['slides'][8]['duration']),
        (10, slide_10_summary, data['slides'][9]['duration']),
    ]

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--ignore-certificate-errors',
                f'--window-size={RESOLUTION[0]},{RESOLUTION[1]}'
            ]
        )

        for slide_num, slide_func, duration in slides:
            print(f"\n🎥 Slide {slide_num}/10")
            await generate_slide(browser, slide_num, slide_func, duration)

        await browser.close()

    print("\n" + "="*70)
    print("✅ ALL 10 VIDEOS GENERATED")
    print("="*70)

if __name__ == "__main__":
    asyncio.run(main())
