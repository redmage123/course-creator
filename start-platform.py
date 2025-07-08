#!/usr/bin/env python3
"""
Intelligent startup script for Course Creator Platform
Uses dependency graph for optimal service startup order
"""

import subprocess
import time
import sys
import signal
import threading
import asyncio
import httpx
from pathlib import Path
from typing import Dict, List, Optional

class IntelligentPlatformManager:
    def __init__(self):
        self.processes = {}
        self.service_order = ['course-management', 'course-generator', 'content-storage', 'user-management']
        self.services = {
            "course-management": {"name": "course-management", "port": 8004, "dir": "services/course-management"}, "course-generator": {"name": "course-generator", "port": 8001, "dir": "services/course-generator"}, "content-storage": {"name": "content-storage", "port": 8003, "dir": "services/content-storage"}, "user-management": {"name": "user-management", "port": 8000, "dir": "services/user-management"}
        }
        self.frontend_port = 3000
        self.startup_timeout = 60  # seconds
        self.health_check_timeout = 30  # seconds
    
    async def start_all(self):
        """Start all services in dependency order"""
        print("🚀 Starting Course Creator Platform with dependency awareness...")
        
        # Start services in dependency order
        for service_name in self.service_order:
            success = await self.start_service_with_health_check(service_name)
            if not success:
                print(f"❌ Failed to start {service_name}, stopping...")
                await self.stop_all()
                return False
        
        # Start frontend server
        await self.start_frontend()
        
        print("\n✅ Platform started successfully!")
        print("\n🌐 Access URLs:")
        for service_name in self.service_order:
            service = self.services[service_name]
            print(f"  {service_name}: http://localhost:{service['port']}")
        print(f"  Frontend: http://localhost:{self.frontend_port}")
        print("\nPress Ctrl+C to stop all services...")
        
        # Wait for interrupt
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            await self.stop_all()
        
        return True
    
    async def start_service_with_health_check(self, service_name: str) -> bool:
        """Start service and wait for health check"""
        service = self.services[service_name]
        service_dir = Path(service["dir"])
        
        if not service_dir.exists():
            print(f"❌ Service directory not found: {service_dir}")
            return False
        
        print(f"  🔧 Starting {service_name}...")
        
        # Start the service
        cmd = [sys.executable, "run.py"]
        process = subprocess.Popen(
            cmd,
            cwd=service_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        self.processes[service_name] = process
        
        # Wait for service to be healthy
        if await self.wait_for_service_health(service_name, service["port"]):
            print(f"  ✅ {service_name} started and healthy on port {service['port']}")
            return True
        else:
            print(f"  ❌ {service_name} failed to become healthy")
            return False
    
    async def wait_for_service_health(self, service_name: str, port: int) -> bool:
        """Wait for service to respond to health checks"""
        health_url = f"http://localhost:{port}/health"
        start_time = time.time()
        
        async with httpx.AsyncClient() as client:
            while time.time() - start_time < self.health_check_timeout:
                try:
                    response = await client.get(health_url, timeout=5.0)
                    if response.status_code == 200:
                        return True
                except:
                    pass
                
                await asyncio.sleep(2)
        
        return False
    
    async def start_frontend(self):
        """Start frontend server"""
        try:
            import http.server
            import socketserver
            import os
            
            def serve_frontend():
                if Path("frontend").exists():
                    os.chdir("frontend")
                    handler = http.server.SimpleHTTPRequestHandler
                    with socketserver.TCPServer(("", self.frontend_port), handler) as httpd:
                        httpd.serve_forever()
                else:
                    print("  ⚠️ Frontend directory not found")
            
            frontend_thread = threading.Thread(target=serve_frontend, daemon=True)
            frontend_thread.start()
            print(f"  ✅ Started frontend on port {self.frontend_port}")
            
        except Exception as e:
            print(f"  ❌ Failed to start frontend: {e}")
    
    async def stop_all(self):
        """Stop all services in reverse order"""
        print("\n🛑 Stopping all services...")
        
        # Stop in reverse order
        for service_name in reversed(self.service_order):
            if service_name in self.processes:
                try:
                    process = self.processes[service_name]
                    process.terminate()
                    process.wait(timeout=5)
                    print(f"  ✅ Stopped {service_name}")
                except:
                    process.kill()
                    print(f"  🔪 Force killed {service_name}")
        
        print("✅ All services stopped")

async def main():
    manager = IntelligentPlatformManager()
    await manager.start_all()

if __name__ == "__main__":
    asyncio.run(main())
