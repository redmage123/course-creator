#!/usr/bin/env python3
"""
Test script to demonstrate lab container creation with multi-IDE support
"""

import requests
import json
import time
import sys

# Configuration
LAB_MANAGER_URL = "http://localhost:8006"

def test_lab_manager_health():
    """Test if lab manager is healthy"""
    try:
        response = requests.get(f"{LAB_MANAGER_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Lab Manager is healthy")
            print(f"   Docker Status: {data.get('docker_status')}")
            print(f"   Active Labs: {data.get('active_labs')}")
            print(f"   CPU Usage: {data.get('system_resources', {}).get('cpu_percent')}%")
            return True
        else:
            print(f"❌ Lab Manager health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to Lab Manager: {e}")
        return False

def create_student_lab():
    """Create a new student lab container"""
    lab_request = {
        "user_id": "test_student_123",
        "course_id": "python_course_1",
        "lab_type": "python",
        "preferred_ide": "vscode",
        "enable_multi_ide": True
    }
    
    try:
        print(f"🚀 Creating student lab...")
        response = requests.post(f"{LAB_MANAGER_URL}/labs/student", json=lab_request)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Lab created successfully!")
            print(f"   Lab ID: {data.get('lab_id')}")
            print(f"   Status: {data.get('status')}")
            print(f"   Container ID: {data.get('container_id')}")
            
            # Show IDE access URLs
            if 'ide_ports' in data:
                print(f"   IDE Access URLs:")
                ide_ports = data['ide_ports']
                print(f"     VSCode: http://localhost:{ide_ports.get('vscode', 'N/A')}")
                print(f"     JupyterLab: http://localhost:{ide_ports.get('jupyter', 'N/A')}")
                print(f"     Jupyter Notebook: http://localhost:{ide_ports.get('terminal', 'N/A')}")
            
            return data
        else:
            print(f"❌ Lab creation failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error creating lab: {e}")
        return None

def test_ide_connectivity(lab_data):
    """Test connectivity to the IDEs in the lab"""
    if not lab_data or 'ide_ports' not in lab_data:
        print("❌ No IDE port information available")
        return
        
    ide_ports = lab_data['ide_ports']
    
    print(f"🔍 Testing IDE connectivity...")
    time.sleep(10)  # Give containers time to start
    
    for ide_name, port in ide_ports.items():
        try:
            response = requests.get(f"http://localhost:{port}", timeout=5)
            if response.status_code < 400:
                print(f"   ✅ {ide_name.title()}: http://localhost:{port} - Accessible")
            else:
                print(f"   ⚠️  {ide_name.title()}: http://localhost:{port} - Status {response.status_code}")
        except requests.exceptions.Timeout:
            print(f"   ⏳ {ide_name.title()}: http://localhost:{port} - Still starting...")
        except Exception as e:
            print(f"   ❌ {ide_name.title()}: http://localhost:{port} - Error: {e}")

def get_lab_status(lab_id):
    """Get status of a specific lab"""
    try:
        response = requests.get(f"{LAB_MANAGER_URL}/labs/{lab_id}")
        if response.status_code == 200:
            data = response.json()
            print(f"📊 Lab Status:")
            print(f"   Lab ID: {data.get('lab_id')}")
            print(f"   Status: {data.get('status')}")
            print(f"   IDE Status: {data.get('ide_status', {})}")
            return data
        else:
            print(f"❌ Cannot get lab status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting lab status: {e}")

def main():
    """Main test function"""
    print("🧪 Lab Container Multi-IDE Test Script")
    print("=" * 50)
    
    # Test 1: Health check
    if not test_lab_manager_health():
        print("❌ Lab Manager not healthy, exiting")
        sys.exit(1)
    
    print()
    
    # Test 2: Create lab
    lab_data = create_student_lab()
    if not lab_data:
        print("❌ Cannot create lab, exiting")
        sys.exit(1)
    
    print()
    
    # Test 3: Test IDE connectivity
    test_ide_connectivity(lab_data)
    
    print()
    
    # Test 4: Get lab status
    if 'lab_id' in lab_data:
        get_lab_status(lab_data['lab_id'])
    
    print()
    print("🎉 Test completed! You can now access the IDEs at the URLs shown above.")
    print("   Note: It may take a minute for all services to fully start.")

if __name__ == "__main__":
    main()