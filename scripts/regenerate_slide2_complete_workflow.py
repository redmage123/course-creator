#!/usr/bin/env python3
"""
Regenerate Slide 2 - Complete Getting Started Workflow with Visible Cursor

Shows the complete registration workflow:
1. Home page with visible custom cursor
2. Mouse moves to Register button (visible movement)
3. Click Register button
4. Navigate to organization registration
5. Fill in the form with proper scrolling
6. Submit form
7. Show success message

Duration: ~36 seconds to match audio (35.7s)
"""

import time
import os
import subprocess
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager

BASE_URL = "https://localhost:3000"
SCREENSHOTS_DIR = "/tmp/slide2_complete_workflow"
VIDEO_OUTPUT = "/home/bbrelin/course-creator/frontend/static/demo/videos/slide_02_org_admin.mp4"

# Create screenshots directory
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

print("=" * 70)
print("SLIDE 2: COMPLETE GETTING STARTED WORKFLOW")
print("=" * 70)

# Setup Chrome (headless)
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")
options.add_argument("--ignore-certificate-errors")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)
driver.set_window_size(1920, 1080)
wait = WebDriverWait(driver, 10)

screenshot_count = 0

# JavaScript to create and move a visible cursor
CURSOR_SCRIPT = """
// Remove existing cursor if any
const existingCursor = document.getElementById('demo-cursor');
if (existingCursor) existingCursor.remove();

// Create custom cursor
const cursor = document.createElement('div');
cursor.id = 'demo-cursor';
cursor.style.position = 'fixed';
cursor.style.width = '24px';
cursor.style.height = '24px';
cursor.style.border = '3px solid #ff0000';
cursor.style.borderRadius = '50%';
cursor.style.backgroundColor = 'rgba(255, 0, 0, 0.3)';
cursor.style.pointerEvents = 'none';
cursor.style.zIndex = '999999';
cursor.style.transition = 'all 0.1s ease';
cursor.style.boxShadow = '0 0 10px rgba(255, 0, 0, 0.5)';
document.body.appendChild(cursor);

// Function to move cursor
window.moveCursor = function(x, y) {
    cursor.style.left = x + 'px';
    cursor.style.top = y + 'px';
};

// Initialize at center
window.moveCursor(window.innerWidth / 2, window.innerHeight / 2);
"""

def inject_cursor():
    """Inject visible cursor into page"""
    driver.execute_script(CURSOR_SCRIPT)

def move_cursor_to(x, y, steps=30):
    """Smoothly move cursor to coordinates"""
    script = """
    var startX = parseInt(document.getElementById('demo-cursor').style.left) || window.innerWidth / 2;
    var startY = parseInt(document.getElementById('demo-cursor').style.top) || window.innerHeight / 2;
    var targetX = arguments[0];
    var targetY = arguments[1];
    var steps = arguments[2];

    for (var i = 0; i <= steps; i++) {
        var progress = i / steps;
        var easeProgress = progress < 0.5 ? 2 * progress * progress : 1 - Math.pow(-2 * progress + 2, 2) / 2;
        var currentX = startX + (targetX - startX) * easeProgress;
        var currentY = startY + (targetY - startY) * easeProgress;
        window.moveCursor(currentX, currentY);
    }
    """
    driver.execute_script(script, x, y, steps)

def capture(name, duration_frames=30):
    """Capture screenshot and hold for N frames"""
    global screenshot_count
    screenshot_count += 1
    path = f"{SCREENSHOTS_DIR}/frame_{screenshot_count:04d}.png"
    driver.save_screenshot(path)
    print(f"   {screenshot_count:3d}. {name} ({duration_frames} frames)")

    # Duplicate frame for duration
    for i in range(1, duration_frames):
        screenshot_count += 1
        duplicate_path = f"{SCREENSHOTS_DIR}/frame_{screenshot_count:04d}.png"
        subprocess.run(['cp', path, duplicate_path], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def slow_type(element, text):
    """Type text character by character"""
    for char in text:
        element.send_keys(char)
        time.sleep(0.03)

try:
    print("\n1. Load home page...")
    driver.get(f"{BASE_URL}/")
    time.sleep(2)

    # Dismiss privacy modal
    try:
        modal = wait.until(EC.presence_of_element_located((By.ID, 'privacyModal')))
        if modal.is_displayed():
            accept_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Accept All')]")
            accept_btn.click()
            time.sleep(1)
    except:
        pass

    # Inject cursor
    inject_cursor()

    # Home page with cursor (2 seconds)
    capture("Home page with cursor", 60)

    print("\n2. Moving cursor to Register button...")
    # Find Register button position
    register_btn = wait.until(EC.presence_of_element_located((By.ID, 'registerBtn')))
    locations = register_btn.locations
    size = register_btn.size

    # Calculate center of button
    btn_x = locations['x'] + size['width'] / 2
    btn_y = locations['y'] + size['height'] / 2

    # Move cursor smoothly (1.5 seconds = 45 frames)
    for step in range(45):
        progress = step / 45.0
        # Ease out cubic
        ease_progress = 1 - pow(1 - progress, 3)

        current_x = 960 + (btn_x - 960) * ease_progress
        current_y = 540 + (btn_y - 540) * ease_progress

        driver.execute_script(f"window.moveCursor({current_x}, {current_y});")
        capture("Moving cursor", 1)

    # Hover on button (0.5 seconds)
    capture("Hover on Register", 15)

    print("\n3. Click Register button...")
    # Navigate to organization registration
    driver.get(f"{BASE_URL}/html/organization-registration.html")
    time.sleep(2)

    # Inject cursor on new page
    inject_cursor()

    # Start cursor at top center
    driver.execute_script("window.moveCursor(960, 200);")

    # Disable ALL validation and error display for demo
    disable_validation_script = """
    // Completely disable validation by removing all event listeners
    // Override the validation functions
    if (window.orgRegistration) {
        window.orgRegistration.validateProfessionalEmail = function() { return true; };
        window.orgRegistration.validateField = function() { return true; };
        window.orgRegistration.validateForm = function() { return true; };
    }

    // Remove all existing error messages
    document.querySelectorAll('.form-error').forEach(el => {
        el.textContent = '';
        el.classList.remove('show');
        el.style.display = 'none';
        el.remove(); // Actually remove them from DOM
    });

    // Remove invalid classes from inputs
    document.querySelectorAll('.form-input, .form-textarea').forEach(el => {
        el.classList.remove('is-invalid');
        el.setAttribute('aria-invalid', 'false');
    });

    // Prevent future error messages from appearing
    const style = document.createElement('style');
    style.textContent = '.form-error { display: none !important; }';
    document.head.appendChild(style);

    // Override showFieldError to do nothing
    if (typeof showFieldError !== 'undefined') {
        window.showFieldError = function() {};
    }

    // Remove any general error messages
    const generalError = document.getElementById('generalError');
    if (generalError) {
        generalError.style.display = 'none';
        generalError.remove();
    }

    // Disable inline validation script if it exists
    const inlineValidation = document.querySelector('script[src*="inline-validation"]');
    if (inlineValidation) {
        inlineValidation.remove();
    }
    """
    driver.execute_script(disable_validation_script)

    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(0.5)

    # Registration page loaded (2 seconds)
    capture("Registration page", 60)

    print("\n4. Filling organization details...")

    # Ensure errors stay disabled
    driver.execute_script("""
        // Keep errors hidden with !important
        document.querySelectorAll('.form-error').forEach(el => {
            el.style.display = 'none';
            el.style.visibility = 'hidden';
        });

        // Disable blur events that trigger validation
        document.querySelectorAll('.form-input, .form-textarea').forEach(el => {
            const newEl = el.cloneNode(true);
            el.parentNode.replaceChild(newEl, el);
        });
    """)

    # Scroll to ensure fields are visible
    driver.execute_script("window.scrollTo(0, 200);")
    time.sleep(0.3)

    # Organization name
    org_name = wait.until(EC.presence_of_element_located((By.ID, "orgName")))
    slow_type(org_name, "Acme Learning")
    capture("Org name", 45)

    # Website - Use format that passes validation
    org_domain = driver.find_element(By.ID, "orgDomain")
    slow_type(org_domain, "https://acmelearning.edu")
    capture("Website", 40)

    # Description
    org_desc = driver.find_element(By.ID, "orgDescription")
    slow_type(org_desc, "Professional training")
    capture("Description", 40)

    print("\n5. Contact information...")
    # Scroll to show contact section clearly
    driver.execute_script("window.scrollTo(0, 600);")
    time.sleep(0.5)
    capture("Contact section", 30)

    # Email
    org_email = driver.find_element(By.ID, "orgEmail")
    slow_type(org_email, "admin@acmelearning.edu")
    capture("Email", 40)

    # Address
    org_street = driver.find_element(By.ID, "orgStreetAddress")
    slow_type(org_street, "123 Innovation Dr")
    capture("Address", 35)

    # City
    org_city = driver.find_element(By.ID, "orgCity")
    slow_type(org_city, "San Francisco")
    capture("City", 30)

    # State
    org_state = driver.find_element(By.ID, "orgStateProvince")
    slow_type(org_state, "CA")
    capture("State", 25)

    # Postal code
    org_postal = driver.find_element(By.ID, "orgPostalCode")
    slow_type(org_postal, "94105")
    capture("Postal code", 25)

    # Phone
    org_phone = driver.find_element(By.ID, "orgPhone")
    slow_type(org_phone, "+14155551234")
    capture("Phone", 30)

    print("\n6. Administrator account...")
    # Scroll to show admin section clearly
    driver.execute_script("window.scrollTo(0, 1200);")
    time.sleep(0.5)
    capture("Admin section", 35)

    # Admin name
    admin_name = driver.find_element(By.ID, "adminName")
    slow_type(admin_name, "Sarah Johnson")
    capture("Admin name", 40)

    # Admin username
    admin_username = driver.find_element(By.ID, "adminUsername")
    slow_type(admin_username, "sjohnson")
    capture("Username", 30)

    # Admin email
    admin_email = driver.find_element(By.ID, "adminEmail")
    slow_type(admin_email, "sarah@acmelearning.edu")
    capture("Admin email", 40)

    # Password
    admin_password = driver.find_element(By.ID, "adminPassword")
    admin_password.send_keys("SecurePass123!")
    capture("Password", 30)

    # Confirm password
    admin_confirm = driver.find_element(By.ID, "adminPasswordConfirm")
    admin_confirm.send_keys("SecurePass123!")
    capture("Confirm password", 30)

    print("\n7. Scrolling to submit button...")

    # Final check - ensure no errors are visible anywhere
    driver.execute_script("""
        // Force hide all errors with extreme prejudice
        document.querySelectorAll('.form-error, [class*="error"], [id*="error"]').forEach(el => {
            el.style.display = 'none !important';
            el.style.visibility = 'hidden !important';
            el.style.opacity = '0 !important';
            el.textContent = '';
            el.innerHTML = '';
        });

        document.querySelectorAll('.form-input').forEach(el => {
            el.classList.remove('is-invalid', 'error');
        });

        // Add CSS to absolutely prevent any errors from showing
        const hideErrorsStyle = document.createElement('style');
        hideErrorsStyle.textContent = `
            .form-error,
            [class*="error"],
            .is-invalid,
            .error-message,
            [id*="-error"] {
                display: none !important;
                visibility: hidden !important;
                opacity: 0 !important;
                height: 0 !important;
                overflow: hidden !important;
            }
        `;
        document.head.appendChild(hideErrorsStyle);
    """)

    # Scroll to show submit button clearly (not cut off)
    driver.execute_script("window.scrollTo(0, 2000);")
    time.sleep(0.5)
    capture("Submit button visible", 30)

    print("\n8. Moving cursor to submit button...")
    # Find submit button
    submit_btn = driver.find_element(By.ID, "submitBtn")
    submit_location = submit_btn.locations
    submit_size = submit_btn.size

    submit_x = submit_location['x'] + submit_size['width'] / 2
    submit_y = submit_location['y'] + submit_size['height'] / 2

    # Move cursor to submit button
    driver.execute_script(f"window.moveCursor({submit_x}, {submit_y});")
    capture("Cursor on submit", 20)

    print("\n9. Clicking submit button...")
    # Click submit - capture the moment
    capture("Before submit click", 10)

    # Actually click the submit button
    submit_btn.click()
    time.sleep(0.5)

    capture("Submit clicked", 20)

    print("\n10. Showing success state...")
    # Manually trigger success message for demo (since we're not actually submitting to backend)
    success_script = """
    console.log('=== TRIGGERING SUCCESS MESSAGE ===');

    const form = document.getElementById('organizationRegistrationForm');
    const successMessage = document.getElementById('successMessage');

    if (!successMessage) {
        console.error('✗ Success message element not found!');
    } else {
        console.log('✓ Success message element found');

        // CRITICAL: Move success message outside the form BEFORE hiding the form
        // Otherwise hiding the form will hide the success message too!
        const registrationCard = document.querySelector('.registration-card');
        if (registrationCard && successMessage.parentElement) {
            registrationCard.appendChild(successMessage);
            console.log('✓ Success message moved outside form');
        }

        // Now hide the form
        if (form) {
            form.style.display = 'none';
            console.log('✓ Form hidden');
        }

        // Simply add the 'show' class - CSS now has !important flags
        successMessage.classList.add('show');
        console.log('✓ Success message show class added');

        // Update with demo data
        const content = successMessage.querySelector('.success-content');
        console.log('Success content element:', content);

        if (content) {
            content.innerHTML = `
                <h3 style="color: white; font-size: 2.5rem; margin-bottom: 1.5rem; text-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <i class="fas fa-check-circle" style="font-size: 3rem; display: block; margin-bottom: 1rem;"></i>
                    Registration Successful!
                </h3>
                <div style="background: rgba(255, 255, 255, 0.15); border-radius: 12px; padding: 2.5rem; margin-top: 1.5rem; border: 2px solid rgba(255, 255, 255, 0.3);">
                    <p style="font-size: 1.5rem; color: white; margin-bottom: 1.5rem; font-weight: 600;">
                        <strong>Acme Learning</strong> has been successfully registered!
                    </p>
                    <p style="font-size: 1.2rem; color: rgba(255, 255, 255, 0.95); margin-bottom: 1rem;">
                        Administrator account created for <strong>sarah@acmelearning.edu</strong>
                    </p>
                    <p style="font-size: 1.2rem; color: rgba(255, 255, 255, 0.95); margin-top: 1rem;">
                        You can now log in and start creating courses!
                    </p>
                </div>
            `;
            console.log('✓ Success content updated');
        } else {
            console.error('✗ Success content not found!');
        }

        // Scroll to make success message fully visible
        window.scrollTo({top: 0, behavior: 'smooth'});
        console.log('✓ Scrolled to top to show success message');
    }

    console.log('=== SUCCESS MESSAGE TRIGGER COMPLETE ===');
    """

    print("   Executing success script...")
    result = driver.execute_script(success_script + " return true;")
    print(f"   Script execution result: {result}")
    time.sleep(2)

    print("\n11. Success message displayed...")
    # Scroll to top to show success message clearly
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)

    # Verify success message is visible
    is_visible = driver.execute_script("""
        const msg = document.getElementById('successMessage');
        if (!msg) return 'ERROR: Element not found';
        const style = window.getComputedStyle(msg);
        const rect = msg.getBoundingClientRect();
        return {
            display: style.display,
            visibility: style.visibility,
            opacity: style.opacity,
            backgroundColor: style.backgroundColor,
            hasClass: msg.classList.contains('show'),
            position: {top: rect.top, left: rect.left, width: rect.width, height: rect.height},
            innerHTML: msg.innerHTML.substring(0, 100)
        };
    """)
    print(f"   Success message visibility check: {is_visible}")

    # Save debug screenshot
    debug_path = "/tmp/debug_success_message.png"
    driver.save_screenshot(debug_path)
    print(f"   Debug screenshot saved to: {debug_path}")

    # Wait longer for rendering
    time.sleep(2)

    # Success message displayed (9 seconds) - "Click submit, and there you go! Your organization is successfully registered. Next, we'll show you how to create projects."
    capture("Success message", 270)

    print(f"\n✅ Captured {screenshot_count} frames (~{screenshot_count/30:.1f} seconds)")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

finally:
    driver.quit()

# Create video using ffmpeg
print("\n12. Creating video...")

ffmpeg_cmd = [
    'ffmpeg',
    '-r', '30',
    '-i', f'{SCREENSHOTS_DIR}/frame_%04d.png',
    '-c:v', 'libx264',
    '-preset', 'medium',
    '-crf', '23',
    '-pix_fmt', 'yuv420p',
    '-movflags', '+faststart',
    '-vf', 'scale=1920:1080',
    '-y',
    VIDEO_OUTPUT
]

try:
    result = subprocess.run(
        ffmpeg_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=120
    )

    if result.returncode == 0:
        if os.path.exists(VIDEO_OUTPUT) and os.path.getsize(VIDEO_OUTPUT) > 0:
            file_size = os.path.getsize(VIDEO_OUTPUT)
            duration = screenshot_count / 30.0
            print(f"   ✓ Video created successfully")
            print(f"     File: {VIDEO_OUTPUT}")
            print(f"     Size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
            print(f"     Duration: {duration:.1f}s")
            print(f"     Audio duration: 31.16s")
        else:
            print(f"   ❌ Video file is empty or not found")
    else:
        print(f"   ❌ FFmpeg failed (exit code {result.returncode})")
        print(f"   Error: {result.stderr[-1000:]}")

except subprocess.TimeoutExpired:
    print("   ❌ FFmpeg timed out")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Cleanup
print("\n13. Cleaning up...")
subprocess.run(['rm', '-rf', SCREENSHOTS_DIR], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

print("\n" + "=" * 70)
print("✅ COMPLETE")
print("=" * 70)
print()
print("Features:")
print("  ✓ Visible red cursor showing mouse movement")
print("  ✓ Proper form scrolling to show all sections")
print("  ✓ Submit button click animation")
print("  ✓ Success message display")
print()
print("Next step: Test the video in demo-player.html")
print()
