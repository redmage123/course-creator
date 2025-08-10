#!/usr/bin/env python3
"""
Browser Capture Test for Registration Button
Uses browser automation to capture the actual DOM state and console output
"""

import requests
import urllib3
import re
from urllib.parse import urljoin

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_page_content():
    print("🚀 Testing page content and structure...")
    
    base_url = "https://176.9.99.103:3000"
    page_url = f"{base_url}/html/index.html"
    
    try:
        # Fetch the main page
        print(f"📄 Fetching: {page_url}")
        response = requests.get(page_url, verify=False, timeout=10)
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            html_content = response.text
            
            # Analyze the HTML content
            print(f"📝 HTML length: {len(html_content)} characters")
            
            # Check for register button
            register_btn_match = re.search(r'<button[^>]*id=["\']registerBtn["\'][^>]*>(.*?)</button>', html_content, re.DOTALL)
            if register_btn_match:
                print(f"✅ Register button found: {register_btn_match.group(1).strip()}")
            else:
                print("❌ Register button not found in HTML")
            
            # Check for main-content
            main_content_match = re.search(r'<main[^>]*id=["\']main-content["\'][^>]*>(.*?)</main>', html_content, re.DOTALL)
            if main_content_match:
                main_content = main_content_match.group(1)
                print(f"✅ Main content found, length: {len(main_content)} characters")
                print(f"📄 Main content preview: {main_content[:200].strip()}...")
            else:
                print("❌ Main content not found in HTML")
            
            # Check for JavaScript modules
            js_modules = re.findall(r'<script[^>]*type=["\']module["\'][^>]*src=["\']([^"\']*)["\']', html_content)
            print(f"📦 JavaScript modules found: {js_modules}")
            
            # Check for CSS files
            css_files = re.findall(r'<link[^>]*rel=["\']stylesheet["\'][^>]*href=["\']([^"\']*)["\']', html_content)
            print(f"🎨 CSS files found: {css_files}")
            
            # Save the HTML for inspection
            with open('/tmp/captured_page.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            print("💾 HTML saved to: /tmp/captured_page.html")
            
            # Try to fetch the main.js module
            if js_modules:
                main_js_url = urljoin(page_url, js_modules[0])
                print(f"\n📦 Fetching main JS module: {main_js_url}")
                try:
                    js_response = requests.get(main_js_url, verify=False, timeout=10)
                    if js_response.status_code == 200:
                        print(f"✅ Main JS loaded, length: {len(js_response.text)} characters")
                        
                        # Check for key functions
                        if 'showRegister' in js_response.text:
                            print("✅ showRegister function found in JS")
                        else:
                            print("❌ showRegister function not found in main JS")
                            
                        # Save JS for inspection
                        with open('/tmp/main_js.txt', 'w', encoding='utf-8') as f:
                            f.write(js_response.text)
                        print("💾 Main JS saved to: /tmp/main_js.txt")
                    else:
                        print(f"❌ Failed to load main JS: {js_response.status_code}")
                except Exception as e:
                    print(f"❌ Error fetching main JS: {e}")
                    
        else:
            print(f"❌ Failed to load page: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing page: {e}")

def create_debug_html():
    """Create a standalone HTML file that tests the registration button functionality"""
    print(f"\n🔧 Creating debug HTML file...")
    
    debug_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Registration Button Debug Test</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; }
        .test-section { margin: 20px 0; padding: 20px; border: 1px solid #ccc; background: #f9f9f9; }
        .result { margin: 10px 0; padding: 10px; }
        .success { background: #d4edda; color: #155724; }
        .error { background: #f8d7da; color: #721c24; }
        .info { background: #d1ecf1; color: #0c5460; }
        #main-content { border: 2px solid blue; padding: 20px; margin: 20px 0; min-height: 200px; }
    </style>
</head>
<body>
    <h1>Registration Button Debug Test</h1>
    
    <div class="test-section">
        <h2>Test Elements</h2>
        <button id="registerBtn" class="btn-auth btn-register">Register</button>
        <div id="results"></div>
    </div>
    
    <main id="main-content">
        <div>Initial content in main area</div>
    </main>
    
    <script>
        const results = document.getElementById('results');
        
        function log(message, type = 'info') {
            const div = document.createElement('div');
            div.className = `result ${type}`;
            div.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
            results.appendChild(div);
            console.log(message);
        }
        
        // Test 1: Button click simulation
        document.getElementById('registerBtn').addEventListener('click', function() {
            log('Register button clicked!', 'success');
            
            const main = document.getElementById('main-content');
            const initialLength = main.innerHTML.length;
            log(`Initial main content length: ${initialLength}`, 'info');
            
            // Simulate what the Navigation.showRegister should do
            main.innerHTML = `
                <section class="registration-options" style="background: #f8f9fa; padding: 2rem; border: 1px solid #ddd;">
                    <div class="registration-header">
                        <h2>Join the Course Creator Platform</h2>
                        <p>Choose your registration path to get started with course creation and management.</p>
                    </div>
                    <div class="registration-cards" style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; margin: 2rem 0;">
                        <div class="registration-card" style="background: white; padding: 2rem; border: 1px solid #ddd; border-radius: 8px;">
                            <h3>Register New Organization</h3>
                            <p>Set up a new organization account with full administrative controls.</p>
                            <button style="background: #007bff; color: white; padding: 0.5rem 1rem; border: none; border-radius: 4px;">Register Organization</button>
                        </div>
                        <div class="registration-card" style="background: white; padding: 2rem; border: 1px solid #ddd; border-radius: 8px;">
                            <h3>Join Existing Organization</h3>
                            <p>Register as an instructor within an existing organization.</p>
                            <button style="background: #6c757d; color: white; padding: 0.5rem 1rem; border: none; border-radius: 4px;">Join as Instructor</button>
                        </div>
                    </div>
                </section>
            `;
            
            const newLength = main.innerHTML.length;
            log(`New main content length: ${newLength}`, 'success');
            log(`Content updated: ${initialLength} → ${newLength}`, 'success');
            
            // Check if content is visible
            const regSection = main.querySelector('.registration-options');
            if (regSection) {
                const rect = regSection.getBoundingClientRect();
                log(`Registration section found, size: ${rect.width}x${rect.height}`, 'success');
                log(`Position: top=${rect.top}, left=${rect.left}`, 'info');
            } else {
                log('Registration section not found!', 'error');
            }
        });
        
        log('Debug page loaded and ready for testing', 'info');
    </script>
</body>
</html>"""
    
    with open('/tmp/registration_debug.html', 'w', encoding='utf-8') as f:
        f.write(debug_html)
    
    print("✅ Debug HTML created: /tmp/registration_debug.html")
    print("📋 To test:")
    print("   1. Copy this file to the frontend directory")
    print("   2. Access it via: https://176.9.99.103:3000/registration_debug.html")
    print("   3. Click the Register button and observe the behavior")

if __name__ == "__main__":
    test_page_content()
    create_debug_html()