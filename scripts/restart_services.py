#!/usr/bin/env python3
"""
Service restart script to handle the course-management service restart
"""
import subprocess
import time
import sys

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"Running: {description}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"✅ {description} - Success")
            return True
        else:
            print(f"❌ {description} - Failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} - Timeout")
        return False
    except Exception as e:
        print(f"💥 {description} - Error: {e}")
        return False

def main():
    print("🔄 Restarting Course Creator Services...")
    
    # Stop course-management if running
    run_command("docker stop course-creator-course-management-1", "Stop course-management")
    time.sleep(2)
    
    # Remove container
    run_command("docker rm course-creator-course-management-1", "Remove course-management container")
    time.sleep(1)
    
    # Start all services
    if run_command("docker compose up -d", "Start all services"):
        print("✅ Services restarted successfully")
        
        # Wait a bit and check status
        time.sleep(10)
        run_command("docker compose ps", "Check service status")
        
        # Test course-management health
        time.sleep(5)
        run_command("curl -s http://localhost:8004/health", "Test course-management health")
        
    else:
        print("❌ Failed to restart services")
        sys.exit(1)

if __name__ == "__main__":
    main()