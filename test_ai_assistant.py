#!/usr/bin/env python3
"""
Test script for AI Assistant proxy functionality
"""

import requests
import json
import time

# Configuration
LAB_MANAGER_URL = "http://localhost:8006"

def test_ai_assistant_functionality():
    """Test AI assistant proxy endpoints"""
    print("🤖 AI Assistant Proxy Test Script")
    print("=" * 50)
    
    # First, create a lab to test with
    print("1. Creating test lab...")
    lab_request = {
        "user_id": "test_student_ai",
        "course_id": "python_course_ai",
        "lab_type": "python",
        "preferred_ide": "vscode",
        "enable_multi_ide": True
    }
    
    response = requests.post(f"{LAB_MANAGER_URL}/labs/student", json=lab_request)
    if response.status_code != 200:
        print(f"❌ Failed to create lab: {response.text}")
        return
    
    lab_data = response.json()
    lab_id = lab_data["lab_id"]
    print(f"✅ Lab created: {lab_id}")
    
    # Wait for lab to be running
    print("2. Waiting for lab to start...")
    max_wait = 60
    wait_time = 0
    
    while wait_time < max_wait:
        response = requests.get(f"{LAB_MANAGER_URL}/labs/{lab_id}")
        if response.status_code == 200:
            status = response.json().get("status")
            if status == "running":
                print("✅ Lab is running")
                break
            elif status == "error":
                print("❌ Lab failed to start")
                return
        
        time.sleep(2)
        wait_time += 2
    
    if wait_time >= max_wait:
        print("❌ Lab took too long to start")
        return
    
    # Test AI Assistant endpoints
    print("3. Testing AI Assistant endpoints...")
    
    # Test workspace info
    print("   Testing workspace info...")
    response = requests.get(f"{LAB_MANAGER_URL}/ai-assistant/labs/{lab_id}/workspace")
    if response.status_code == 200:
        workspace_info = response.json()
        print(f"   ✅ Workspace info: {workspace_info.get('available_ides')}")
        print(f"   ✅ IDE ports: {workspace_info.get('ide_ports')}")
    else:
        print(f"   ❌ Workspace info failed: {response.text}")
    
    # Test AI proxy - write file
    print("   Testing AI proxy - write file...")
    ai_request = {
        "lab_id": lab_id,
        "ide_type": "vscode",
        "action": "write_file",
        "payload": {
            "file_path": "test_ai.py",
            "content": "# AI Assistant Test File\nprint('Hello from AI Assistant!')\n"
        },
        "ai_session_id": "test_session_001"
    }
    
    response = requests.post(f"{LAB_MANAGER_URL}/ai-assistant/proxy", json=ai_request)
    if response.status_code == 200:
        result = response.json()
        if result["success"]:
            print("   ✅ File written successfully")
        else:
            print(f"   ❌ Write file failed: {result.get('error')}")
    else:
        print(f"   ❌ AI proxy write failed: {response.text}")
    
    # Test AI proxy - read file
    print("   Testing AI proxy - read file...")
    ai_request = {
        "lab_id": lab_id,
        "ide_type": "vscode",
        "action": "read_file",
        "payload": {
            "file_path": "test_ai.py"
        },
        "ai_session_id": "test_session_001"
    }
    
    response = requests.post(f"{LAB_MANAGER_URL}/ai-assistant/proxy", json=ai_request)
    if response.status_code == 200:
        result = response.json()
        if result["success"]:
            content = result["data"]["content"]
            print(f"   ✅ File read successfully: {len(content)} characters")
            print(f"   Content preview: {content[:50]}...")
        else:
            print(f"   ❌ Read file failed: {result.get('error')}")
    else:
        print(f"   ❌ AI proxy read failed: {response.text}")
    
    # Test AI proxy - get workspace
    print("   Testing AI proxy - get workspace...")
    ai_request = {
        "lab_id": lab_id,
        "ide_type": "vscode", 
        "action": "get_workspace",
        "payload": {},
        "ai_session_id": "test_session_001"
    }
    
    response = requests.post(f"{LAB_MANAGER_URL}/ai-assistant/proxy", json=ai_request)
    if response.status_code == 200:
        result = response.json()
        if result["success"]:
            files = result["data"]["files"]
            print(f"   ✅ Workspace files: {files}")
        else:
            print(f"   ❌ Get workspace failed: {result.get('error')}")
    else:
        print(f"   ❌ AI proxy workspace failed: {response.text}")
    
    # Test AI proxy - execute code (Jupyter)
    print("   Testing AI proxy - execute code...")
    ai_request = {
        "lab_id": lab_id,
        "ide_type": "jupyter",
        "action": "execute_code",
        "payload": {
            "code": "import datetime\nprint(f'AI executed at: {datetime.datetime.now()}')"
        },
        "ai_session_id": "test_session_001"
    }
    
    response = requests.post(f"{LAB_MANAGER_URL}/ai-assistant/proxy", json=ai_request)
    if response.status_code == 200:
        result = response.json()
        if result["success"]:
            output = result["data"]["output"]
            print(f"   ✅ Code executed successfully")
            print(f"   Output: {output.strip()}")
        else:
            print(f"   ❌ Execute code failed: {result.get('error')}")
    else:
        print(f"   ❌ AI proxy execute failed: {response.text}")
    
    # Test AI proxy - terminal command
    print("   Testing AI proxy - terminal command...")
    ai_request = {
        "lab_id": lab_id,
        "ide_type": "terminal",
        "action": "terminal_command",
        "payload": {
            "command": "ls -la && echo 'AI terminal test successful'"
        },
        "ai_session_id": "test_session_001"
    }
    
    response = requests.post(f"{LAB_MANAGER_URL}/ai-assistant/proxy", json=ai_request)
    if response.status_code == 200:
        result = response.json()
        if result["success"]:
            output = result["data"]["output"]
            print(f"   ✅ Terminal command executed")
            print(f"   Output preview: {output[:100]}...")
        else:
            print(f"   ❌ Terminal command failed: {result.get('error')}")
    else:
        print(f"   ❌ AI proxy terminal failed: {response.text}")
    
    print("\\n🎉 AI Assistant tests completed!")
    print(f"Lab ID: {lab_id} - You can manually test the tunnel endpoint:")
    print(f"   VSCode: {LAB_MANAGER_URL}/ai-assistant/labs/{lab_id}/tunnel/vscode/")
    print(f"   Jupyter: {LAB_MANAGER_URL}/ai-assistant/labs/{lab_id}/tunnel/jupyter/")

if __name__ == "__main__":
    test_ai_assistant_functionality()