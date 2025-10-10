#!/usr/bin/env python3
"""
Multi-IDE Startup Script for Course Creator Lab Containers
Manages multiple IDE servers within a single container
"""

import asyncio
import json
import logging
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/home/labuser/ide-startup.log')
    ]
)
logger = logging.getLogger(__name__)

class IDEManager:
    """Manages multiple IDE servers in the lab container"""
    
    def __init__(self):
        self.processes: Dict[str, subprocess.Popen] = {}
        self.ide_configs = {
            'terminal': {
                'name': 'Terminal (xterm.js)',
                'port': 8080,
                'command': None,  # Handled by main web server
                'enabled': True,
                'health_endpoint': '/health'
            },
            'vscode': {
                'name': 'VSCode Server',
                'port': 8081,
                'command': [
                    'code-server',
                    '--bind-addr', '0.0.0.0:8081',
                    '--auth', 'none',
                    '--disable-telemetry',
                    '--disable-update-check',
                    '/home/labuser/workspace'
                ],
                'enabled': True,
                'health_endpoint': '/healthz'
            },
            'jupyter': {
                'name': 'JupyterLab',
                'port': 8082,
                'command': [
                    'jupyter', 'lab',
                    '--ip=0.0.0.0',
                    '--port=8082',
                    '--no-browser',
                    '--allow-root',
                    '--NotebookApp.token=""',
                    '--NotebookApp.password=""',
                    '--notebook-dir=/home/labuser/workspace'
                ],
                'enabled': True,
                'health_endpoint': '/lab/api/status'
            },
            'intellij': {
                'name': 'IntelliJ IDEA',
                'port': 8083,
                'command': [
                    'projector', 'run', 'IntelliJ IDEA Community Edition',
                    '--port', '8083',
                    '--host', '0.0.0.0'
                ],
                'enabled': True,  # Enabled for Java/Kotlin courses
                'health_endpoint': '/projector'
            },
            'pycharm': {
                'name': 'PyCharm Community',
                'port': 8084,
                'command': [
                    'projector', 'run', 'PyCharm Community Edition',
                    '--port', '8084',
                    '--host', '0.0.0.0'
                ],
                'enabled': True,  # Enabled by default for Python courses
                'health_endpoint': '/projector'
            }
        }
        self.running = True
        
    async def start_ide_server(self, ide_name: str, config: Dict) -> bool:
        """Start an IDE server"""
        if not config.get('enabled', True):
            logger.info(f"IDE {ide_name} is disabled, skipping")
            return True
            
        if config['command'] is None:
            logger.info(f"IDE {ide_name} handled externally")
            return True
            
        try:
            logger.info(f"Starting {config['name']} on port {config['port']}")
            
            # Set environment variables
            env = os.environ.copy()
            env['PORT'] = str(config['port'])
            
            # Start the process
            process = subprocess.Popen(
                config['command'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                cwd='/home/labuser/workspace'
            )
            
            self.processes[ide_name] = process
            
            # Give the process time to start
            await asyncio.sleep(2)
            
            # Check if process is still running
            if process.poll() is None:
                logger.info(f"Successfully started {config['name']} (PID: {process.pid})")
                return True
            else:
                stdout, stderr = process.communicate()
                logger.error(f"Failed to start {config['name']}: {stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"Error starting {config['name']}: {e}")
            return False
    
    async def stop_ide_server(self, ide_name: str) -> bool:
        """Stop an IDE server"""
        if ide_name not in self.processes:
            return True
            
        try:
            process = self.processes[ide_name]
            process.terminate()
            
            # Wait for graceful shutdown
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if not terminated gracefully
                process.kill()
                process.wait()
                
            del self.processes[ide_name]
            logger.info(f"Stopped IDE server: {ide_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping {ide_name}: {e}")
            return False
    
    async def health_check(self) -> Dict[str, bool]:
        """Check health of all IDE servers"""
        import aiohttp
        
        health_status = {}
        
        async with aiohttp.ClientSession() as session:
            for ide_name, config in self.ide_configs.items():
                if not config.get('enabled', True):
                    health_status[ide_name] = False
                    continue
                    
                try:
                    url = f"http://localhost:{config['port']}{config['health_endpoint']}"
                    async with session.get(url, timeout=5) as response:
                        health_status[ide_name] = response.status == 200
                except:
                    health_status[ide_name] = False
        
        return health_status
    
    async def start_web_server(self):
        """Start the main web server that provides IDE selection and terminal"""
        from aiohttp import web, web_runner
        import aiohttp_cors
        
        async def ide_status_handler(request):
            """Handle IDE status requests"""
            health = await self.health_check()
            return web.json_response({
                'status': 'healthy',
                'ides': {
                    name: {
                        'name': config['name'],
                        'port': config['port'],
                        'enabled': config.get('enabled', True),
                        'healthy': health.get(name, False),
                        'url': f'/ide/{name}' if health.get(name, False) else None
                    }
                    for name, config in self.ide_configs.items()
                }
            })
        
        async def ide_proxy_handler(request):
            """Handle IDE proxy requests"""
            ide_name = request.match_info['ide_name']
            path = request.match_info.get('path', '')
            
            if ide_name not in self.ide_configs:
                return web.Response(status=404, text=f"IDE {ide_name} not found")
            
            config = self.ide_configs[ide_name]
            target_url = f"http://localhost:{config['port']}/{path}"
            
            # Simple proxy implementation
            import aiohttp
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.request(
                        request.method,
                        target_url,
                        headers=dict(request.headers),
                        data=await request.read()
                    ) as response:
                        body = await response.read()
                        return web.Response(
                            body=body,
                            status=response.status,
                            headers=dict(response.headers)
                        )
                except Exception as e:
                    return web.Response(status=502, text=f"Proxy error: {e}")
        
        async def terminal_handler(request):
            """Serve terminal interface"""
            html_content = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Course Creator Lab Terminal</title>
                <script src="https://unpkg.com/xterm@4.19.0/lib/xterm.js"></script>
                <script src="https://unpkg.com/xterm-addon-fit@0.5.0/lib/xterm-addon-fit.js"></script>
                <link rel="stylesheet" href="https://unpkg.com/xterm@4.19.0/css/xterm.css" />
                <style>
                    body { margin: 0; padding: 10px; background: #1e1e1e; }
                    #terminal { height: calc(100vh - 20px); }
                </style>
            </head>
            <body>
                <div id="terminal"></div>
                <script>
                    const term = new Terminal({
                        cursorBlink: true,
                        theme: {
                            background: '#1e1e1e',
                            foreground: '#ffffff'
                        }
                    });
                    const fitAddon = new FitAddon.FitAddon();
                    term.loadAddon(fitAddon);
                    term.open(document.getElementById('terminal'));
                    fitAddon.fit();
                    
                    // Simple bash simulation for demo
                    term.writeln('Course Creator Lab Terminal');
                    term.writeln('Type "help" for available commands');
                    term.write('labuser@lab:~/workspace$ ');
                    
                    let currentLine = '';
                    term.onData(data => {
                        if (data === '\\r') {
                            term.writeln('');
                            // Process command here
                            if (currentLine.trim() === 'help') {
                                term.writeln('Available commands:');
                                term.writeln('  help - Show this help');
                                term.writeln('  ls - List files');
                                term.writeln('  clear - Clear terminal');
                            } else if (currentLine.trim() === 'clear') {
                                term.clear();
                            } else if (currentLine.trim() === 'ls') {
                                term.writeln('assignments/  solutions/  data/  notebooks/  projects/');
                            } else if (currentLine.trim()) {
                                term.writeln('Command not found: ' + currentLine.trim());
                            }
                            currentLine = '';
                            term.write('labuser@lab:~/workspace$ ');
                        } else if (data === '\\u007F') {
                            if (currentLine.length > 0) {
                                currentLine = currentLine.slice(0, -1);
                                term.write('\\b \\b');
                            }
                        } else {
                            currentLine += data;
                            term.write(data);
                        }
                    });
                    
                    window.addEventListener('resize', () => {
                        fitAddon.fit();
                    });
                </script>
            </body>
            </html>
            """
            return web.Response(text=html_content, content_type='text/html')
        
        # Create web application
        app = web.Application()
        
        # Setup CORS
        cors = aiohttp_cors.setup(app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*"
            )
        })
        
        # Add routes
        app.router.add_get('/api/status', ide_status_handler)
        app.router.add_get('/health', ide_status_handler)
        app.router.add_get('/', terminal_handler)
        app.router.add_get('/terminal', terminal_handler)
        app.router.add_route('*', '/ide/{ide_name}/{path:.*}', ide_proxy_handler)
        
        # Add CORS to all routes
        for route in list(app.router.routes()):
            cors.add(route)
        
        # Start the server
        runner = web_runner.AppRunner(app)
        await runner.setup()
        site = web_runner.TCPSite(runner, '0.0.0.0', 8080)
        await site.start()
        
        logger.info("Web server started on port 8080")
    
    async def start_all_ides(self):
        """Start all enabled IDE servers"""
        logger.info("Starting IDE servers...")
        
        # Start web server first
        await self.start_web_server()
        
        # Start IDE servers
        for ide_name, config in self.ide_configs.items():
            if config.get('enabled', True) and config['command']:
                success = await self.start_ide_server(ide_name, config)
                if not success:
                    logger.warning(f"Failed to start {ide_name}, continuing with others")
        
        logger.info("IDE startup complete")
    
    async def monitor_processes(self):
        """Monitor IDE processes and restart if necessary"""
        while self.running:
            try:
                # Check process health
                for ide_name, process in list(self.processes.items()):
                    if process.poll() is not None:
                        logger.warning(f"Process {ide_name} died, restarting...")
                        await self.stop_ide_server(ide_name)
                        config = self.ide_configs.get(ide_name)
                        if config:
                            await self.start_ide_server(ide_name, config)
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in process monitoring: {e}")
                await asyncio.sleep(10)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    async def run(self):
        """Main run loop"""
        # Set up signal handlers
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        
        try:
            # Start all IDE servers
            await self.start_all_ides()
            
            # Start monitoring task
            monitor_task = asyncio.create_task(self.monitor_processes())
            
            # Wait for shutdown signal
            while self.running:
                await asyncio.sleep(1)
            
            # Cleanup
            monitor_task.cancel()
            
            # Stop all IDE servers
            for ide_name in list(self.processes.keys()):
                await self.stop_ide_server(ide_name)
            
            logger.info("IDE Manager shutdown complete")
            
        except Exception as e:
            logger.error(f"Error in IDE manager: {e}")
            sys.exit(1)


if __name__ == "__main__":
    # Install required packages
    try:
        import aiohttp
        import aiohttp_cors
    except ImportError:
        logger.info("Installing required packages...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--user', 'aiohttp', 'aiohttp-cors'])
        import aiohttp
        import aiohttp_cors
    
    # Run the IDE manager
    manager = IDEManager()
    asyncio.run(manager.run())