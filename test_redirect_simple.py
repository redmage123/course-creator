#!/usr/bin/env python3
"""
Simple test to debug the redirect issue
"""
import requests
import subprocess
import time
import os
import signal

def test_redirect_issue():
    """Test to find the source of the automatic redirect"""
    print("🔍 Testing redirect issue...")
    
    # Test 1: Check if the problem is in the HTML itself
    print("\n1. Checking HTML for automatic redirect code...")
    
    with open('/home/bbrelin/course-creator/frontend/instructor-dashboard.html', 'r') as f:
        html_content = f.read()
    
    # Look for problematic patterns
    problematic_patterns = [
        'showSection("overview")',
        "showSection('overview')",
        'window.location.hash = "#overview"',
        'setTimeout.*showSection.*overview',
        'setInterval.*showSection.*overview',
        'DOMContentLoaded.*showSection.*overview'
    ]
    
    for pattern in problematic_patterns:
        if pattern in html_content:
            print(f"❌ Found problematic pattern: {pattern}")
            return False
    
    print("✅ No obvious redirect code found in HTML")
    
    # Test 2: Check if the modular JS is actually disabled
    print("\n2. Checking if modular JS is properly disabled...")
    
    if '<!-- <script type="module" src="js/main-modular.js"></script> -->' in html_content:
        print("✅ Modular JS is commented out")
    else:
        print("❌ Modular JS may still be active")
        return False
    
    # Test 3: Check if there's an automatic overview click
    print("\n3. Checking for automatic overview activation...")
    
    # Count how many times overview is mentioned
    overview_count = html_content.count('overview')
    print(f"   'overview' mentioned {overview_count} times")
    
    # Look for onclick="showSection('overview')" patterns
    if 'onclick="showSection(\'overview\')"' in html_content:
        print("✅ Found overview navigation link (this is normal)")
    
    # Test 4: Check if the navigation has active class that auto-triggers
    print("\n4. Checking navigation active state...")
    
    if 'nav-link active" onclick="showSection(\'overview\')"' in html_content:
        print("⚠️  Overview nav link has 'active' class - this might auto-trigger!")
        # This could be causing the issue if there's CSS or JS that auto-clicks active nav items
        return False
    
    print("✅ No automatic triggers found")
    return True

def main():
    """Run the test"""
    print("🚀 SIMPLE REDIRECT TEST")
    print("=" * 30)
    
    success = test_redirect_issue()
    
    if success:
        print("\n✅ No obvious redirect issues found in static analysis")
        print("   The problem might be in runtime JavaScript execution")
        print("   or a timing issue with page load sequence")
    else:
        print("\n❌ Found potential redirect issues!")
        print("   This explains the automatic redirect behavior")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)