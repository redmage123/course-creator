#!/usr/bin/env python3
"""
Complete Demo Generation with REAL Authentication
Logs in with demo users and records actual workflows
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

# Demo credentials (must use EMAIL for login, not username)
DEMO_USERS = {
    'org_admin': {'email': 'demo.admin@techcorp.training', 'password': 'Demo1234!'},
    'instructor': {'email': 'demo.instructor@techcorp.training', 'password': 'Demo1234!'},
    'student': {'email': 'demo.student@techcorp.training', 'password': 'Demo1234!'}
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

async def login_user(page, email, password):
    """
    Login with real credentials via the login page
    """
    logger.info(f"🔐 Logging in as {email}...")

    try:
        # Navigate to login page
        await page.goto(f"{BASE_URL}/html/student-login.html", wait_until='domcontentloaded', timeout=10000)
        await asyncio.sleep(2)

        # Remove privacy banners first
        await remove_privacy_banners(page)
        await asyncio.sleep(1)

        # Fill in login form (login page uses email field)
        await page.fill('#email', email)
        await asyncio.sleep(0.5)
        await page.fill('#password', password)
        await asyncio.sleep(0.5)
        
        # Submit login
        logger.info(f"   Submitting login...")
        submit_btn = await page.query_selector('button[type="submit"], #credentialsBtn')
        if submit_btn:
            await submit_btn.click()
            # Wait for API call to complete
            await asyncio.sleep(5)
        else:
            await page.keyboard.press('Enter')
            await asyncio.sleep(5)

        # Take diagnostic screenshot
        await page.screenshot(path='/tmp/login_after_submit.jpg')

        # Check for error messages
        error_msg = await page.query_selector('#errorMessage')
        if error_msg:
            error_visible = await error_msg.evaluate("el => el.style.display !== 'none'")
            if error_visible:
                error_text = await error_msg.inner_text()
                if error_text.strip():  # Only fail if there's actual error text
                    logger.error(f"   Login error message: {error_text}")
                    return False

        # Check if we're logged in
        current_url = page.url
        logger.info(f"   Current URL after login: {current_url}")

        # Check if auth token was stored
        has_token = await page.evaluate("() => sessionStorage.getItem('authToken') !== null")
        logger.info(f"   Auth token stored: {has_token}")

        # Debug: Check what's in localStorage
        stored_data = await page.evaluate("""
            () => ({
                role: localStorage.getItem('userRole'),
                user: localStorage.getItem('currentUser'),
                token: sessionStorage.getItem('authToken') ? 'present' : 'missing'
            })
        """)
        logger.info(f"   Stored data - Role: {stored_data['role']}, User: {stored_data['user']}, Token: {stored_data['token']}")

        # Verify login success
        if has_token:
            # For demo users, manually set organization_id if missing
            if email.endswith('@techcorp.training'):
                await page.evaluate("""
                    () => {
                        const user = JSON.parse(localStorage.getItem('currentUser') || '{}');
                        if (!user.organization_id) {
                            user.organization_id = '4fc54313-454c-403e-bf91-eb83fe6ffd4e';
                            localStorage.setItem('currentUser', JSON.stringify(user));
                        }
                    }
                """)
                logger.info(f"   ✅ Login successful as {email} (token stored, org_id set for demo)")
            else:
                logger.info(f"   ✅ Login successful as {email} (token stored)")
            return True
        else:
            logger.warning(f"   ⚠️  Login may not have succeeded (URL: {current_url}, Has token: {has_token})")
            return False

    except Exception as e:
        logger.error(f"   ❌ Login failed: {e}")
        return False

async def remove_privacy_banners(page):
    try:
        removed = await page.evaluate("""
            () => {
                let count = 0;
                // Only remove privacy MODALS and BANNERS, not form elements
                const selectorsToRemove = [
                    '.privacy-modal',
                    '#privacyModal',
                    '.cookie-banner',
                    '.gdpr-banner',
                    '#cookieBanner',
                    '#gdprBanner',
                    '.modal-backdrop',
                    '.overlay:not(form .overlay)'
                ];
                selectorsToRemove.forEach(selector => {
                    document.querySelectorAll(selector).forEach(el => {
                        el.remove();
                        count++;
                    });
                });
                // Remove privacy notice section but NOT consent checkboxes in forms
                document.querySelectorAll('.privacy-notice').forEach(el => {
                    // Only remove if not inside a form
                    if (!el.closest('form')) {
                        el.remove();
                        count++;
                    }
                });
                return count;
            }
        """)
        if removed > 0:
            logger.info(f"   🗑️  Removed {removed} privacy elements")
        await asyncio.sleep(0.5)
    except:
        pass

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
        logger.warning(f"   Type failed for {selector}: {e}")

# Test login flow first
async def test_login(page):
    """Test login with org admin"""
    logger.info("🧪 Testing login flow...")

    success = await login_user(page, DEMO_USERS['org_admin']['email'], DEMO_USERS['org_admin']['password'])
    
    if success:
        # Try to navigate to org admin dashboard
        logger.info("   Testing dashboard access...")
        await page.goto(f"{BASE_URL}/html/org-admin-dashboard-modular.html", wait_until='domcontentloaded')
        await asyncio.sleep(2)
        
        current_url = page.url
        logger.info(f"   Dashboard URL: {current_url}")
        
        if 'org-admin-dashboard' in current_url:
            logger.info("   ✅ Authentication working! Can access protected pages!")
            return True
        else:
            logger.warning(f"   ⚠️  Redirected to: {current_url}")
            return False
    else:
        logger.error("   ❌ Login test failed")
        return False

async def main():
    print("="*80)
    print("🎬 Demo Generation with REAL Authentication")
    print("="*80)
    print("  Phase 1: Testing authentication flow")
    print("="*80)
    
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    
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

        # Enable console logging
        page.on("console", lambda msg: logger.info(f"   BROWSER: {msg.type}: {msg.text}"))
        page.on("pageerror", lambda exc: logger.error(f"   BROWSER ERROR: {exc}"))
        page.on("requestfailed", lambda req: logger.error(f"   REQUEST FAILED: {req.url} - {req.failure}"))
        
        # Test login
        auth_works = await test_login(page)
        
        if auth_works:
            print("\n✅ Authentication test passed!")
            print("Ready to generate all 13 slides with real authentication.")
        else:
            print("\n❌ Authentication test failed!")
            print("Need to debug login flow before proceeding.")
        
        await asyncio.sleep(3)
        await browser.close()
    
    return 0 if auth_works else 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
