#!/usr/bin/env python3

import requests
import json

LAB_MANAGER_URL = "http://localhost:8006"
LAB_ID = "lab-test_file_ops-file_test_course-1753602810"

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
            "content": "# Student workspace file\nprint('Hello from student workspace!')\n"
        },
        "ai_session_id": "test_session"
    }
    
    response = requests.post(f"{LAB_MANAGER_URL}/ai-assistant/proxy", json=write_request)
    if response.status_code == 200:
        result = response.json()
        if result["success"]:
            print("   ✅ File written successfully")
        else:
            print(f"   ❌ Write failed: {result.get('error')}")
    else:
        print(f"   ❌ Request failed: {response.status_code}")
    
    # Test 2: Read the file back
    print("2. Reading file back...")
    read_request = {
        "lab_id": LAB_ID,
        "ide_type": "vscode",
        "action": "read_file",
        "payload": {
            "file_path": "hello.py"
        },
        "ai_session_id": "test_session"
    }
    
    response = requests.post(f"{LAB_MANAGER_URL}/ai-assistant/proxy", json=read_request)
    if response.status_code == 200:
        result = response.json()
        if result["success"]:
            content = result["data"]["content"]
            print(f"   ✅ File read successfully: {len(content)} characters")
            print(f"   Content: {content[:50]}...")
        else:
            print(f"   ❌ Read failed: {result.get('error')}")
    else:
        print(f"   ❌ Request failed: {response.status_code}")
    
    # Test 3: List workspace files
    print("3. Listing workspace files...")
    workspace_request = {
        "lab_id": LAB_ID,
        "ide_type": "vscode",
        "action": "get_workspace",
        "payload": {},
        "ai_session_id": "test_session"
    }
    
    response = requests.post(f"{LAB_MANAGER_URL}/ai-assistant/proxy", json=workspace_request)
    if response.status_code == 200:
        result = response.json()
        if result["success"]:
            files = result["data"]["files"]
            print(f"   ✅ Found {len(files)} files: {files}")
        else:
            print(f"   ❌ List failed: {result.get('error')}")
    else:
        print(f"   ❌ Request failed: {response.status_code}")

if __name__ == "__main__":
    test_file_operations()