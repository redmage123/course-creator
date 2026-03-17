#!/bin/bash

# Multi-IDE startup script for Python lab environment
echo "Starting Python Lab with Multi-IDE Support..."

# Ensure workspace has proper permissions - run as root initially
if [ "$(id -u)" = "0" ]; then
    # Wait a moment for volume mounting to complete
    sleep 1
    
    # Fix workspace permissions after volume is mounted
    echo "Fixing workspace permissions..."
    chown -R labuser:labuser /home/labuser/workspace
    chmod -R 755 /home/labuser/workspace
    
    # Verify permissions were set correctly
    ls -la /home/labuser/ | grep workspace
    
    # Now switch to labuser and continue
    exec su labuser -c "$0"
fi

# Now running as labuser - workspace should have correct permissions

# Function to start a service in background with logging
start_service() {
    local service_name=$1
    local command=$2
    echo "Starting $service_name..."
    $command > "/tmp/${service_name}.log" 2>&1 &
    local pid=$!
    echo "Started $service_name with PID $pid"
}

# Start JupyterLab on port 8081
start_service "jupyterlab" "jupyter lab --ip=0.0.0.0 --port=8081 --no-browser --allow-root --NotebookApp.token='' --NotebookApp.password='' --ServerApp.token='' --ServerApp.password=''"

# Start code-server (VS Code) on port 8080  
start_service "vscode" "code-server --bind-addr 0.0.0.0:8080 --auth none --disable-telemetry /home/labuser/workspace"

# Start Jupyter Notebook on port 8082
start_service "jupyter" "jupyter notebook --ip=0.0.0.0 --port=8082 --no-browser --allow-root --NotebookApp.token='' --NotebookApp.password=''"

# Create a simple health check endpoint using Python
cat > /tmp/health_server.py << 'EOF'
#!/usr/bin/env python3
import http.server
import socketserver
import json
import urllib.request
from threading import Thread
import time

class HealthHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            # Check if services are running
            services = {
                'vscode': self.check_service('http://localhost:8080'),
                'jupyterlab': self.check_service('http://localhost:8081/lab'),
                'jupyter': self.check_service('http://localhost:8082')
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'status': 'healthy',
                'services': services,
                'workspace': '/home/labuser/workspace'
            }).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def check_service(self, url):
        try:
            urllib.request.urlopen(url, timeout=2)
            return 'running'
        except:
            return 'not_ready'
    
    def log_message(self, format, *args):
        pass  # Suppress logs

def run_health_server():
    with socketserver.TCPServer(("", 8083), HealthHandler) as httpd:
        httpd.serve_forever()

if __name__ == "__main__":
    Thread(target=run_health_server, daemon=True).start()
    print("Health server started on port 8083")
    
    # Keep the container running
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        pass
EOF

# Start the health server and keep container running
echo "Starting health monitoring on port 8083..."
python3 /tmp/health_server.py