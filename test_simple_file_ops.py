#!/usr/bin/env python3

import requests
import json
import time

LAB_MANAGER_URL = "http://localhost:8006"
LAB_ID = "lab-permission_test-final_test-1753604192"

def test_file_operations():
    print("🗂️ Testing File Operations in Student Lab")
    print("=" * 50)
    
    # Test 1: Write a file
    print("1. Writing test file...")
    write_request = {
        "lab_id": LAB_ID,
        "ide_type": "vscode",
        "action": "write_file",
        "payload": {
            "file_path": "hello.py",
            "content": "# Student workspace file\nprint('Hello from student workspace!')\nprint('File operations working!')\n"
        },
        "ai_session_id": "test_session"
    }
    
    response = requests.post(f"{LAB_MANAGER_URL}/ai-assistant/proxy", json=write_request)
    print(f"Write response: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Write result: {result}")
        if result["success"]:
            print("   ✅ File written successfully")
        else:
            print(f"   ❌ Write failed: {result.get('error')}")
    else:
        print(f"   ❌ Request failed: {response.status_code} - {response.text}")
    
    # Test 2: List workspace files
    print("\n2. Listing workspace files...")
    response = requests.get(f"{LAB_MANAGER_URL}/labs/{LAB_ID}/files")
    print(f"List response: {response.status_code}")
    if response.status_code == 200:
        file_list = response.json()
        print(f"File list result: {file_list}")
        files = file_list.get("files", [])
        print(f"   ✅ Found {len(files)} files:")
        for file_info in files:
            print(f"     📄 {file_info['name']} ({file_info['size']} bytes)")
    else:
        print(f"   ❌ List failed: {response.status_code} - {response.text}")
    
    # Test 3: Download individual file
    print("\n3. Testing individual file download...")
    response = requests.get(f"{LAB_MANAGER_URL}/labs/{LAB_ID}/download/hello.py")
    print(f"Download response: {response.status_code}")
    if response.status_code == 200:
        content = response.text
        print(f"   ✅ Downloaded file: {len(content)} characters")
        print(f"   Content preview: {content[:100]}...")
    else:
        print(f"   ❌ Download failed: {response.status_code} - {response.text}")
    
    # Test 4: Download workspace ZIP
    print("\n4. Testing workspace ZIP download...")
    response = requests.get(f"{LAB_MANAGER_URL}/labs/{LAB_ID}/download-workspace")
    print(f"ZIP download response: {response.status_code}")
    if response.status_code == 200:
        zip_size = len(response.content)
        print(f"   ✅ ZIP downloaded: {zip_size} bytes")
        
        # Save and test ZIP
        with open("/tmp/test_workspace.zip", "wb") as f:
            f.write(response.content)
        
        import zipfile
        try:
            with zipfile.ZipFile("/tmp/test_workspace.zip", "r") as zip_file:
                file_list = zip_file.namelist()
                print(f"   ZIP contains {len(file_list)} files: {file_list}")
        except Exception as e:
            print(f"   ⚠️ Could not read ZIP: {e}")
    else:
        print(f"   ❌ ZIP download failed: {response.status_code} - {response.text}")

if __name__ == "__main__":
    test_file_operations()