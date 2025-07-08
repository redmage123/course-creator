#!/usr/bin/env python3
"""
Fixed Course Creator Platform Generator
Generates services file-by-file with Hydra configuration
"""

import os
import sys
import json
import argparse
import asyncio
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
import ast

# Third-party imports
import anthropic
from anthropic import RateLimitError, APIError, APIConnectionError, APITimeoutError

# Local imports
from dependency_graph import (
    ServiceDependencyGraph, build_course_creator_graph,
    ServiceNode, DependencyEdge, DependencyType, ServiceType
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PlatformGenerator:
    """Graph-based platform generator with dependency analysis and Hydra configuration"""
    
    def __init__(self, api_key: str, output_dir: Path, verbose: bool = True):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.output_dir = Path(output_dir)
        self.verbose = verbose
        self.services = []
        self.dependency_graph = None
        self.service_interfaces = {}
        self.generation_context = {}
        
    async def generate_platform(self, template_dir: Path):
        """Generate platform using dependency graph analysis"""
        
        logger.info("🔧 Starting graph-based platform generation...")
        
        # Build dependency graph
        await self._build_dependency_graph(template_dir)
        
        # Analyze architecture
        await self._analyze_architecture()
        
        # Generate services in dependency order
        await self._generate_services_by_dependency_order()
        
        # Generate inter-service communication code
        await self._generate_service_communication()
        
        # Generate frontend with service integration
        await self._generate_frontend_with_integration()
        
        # Generate intelligent startup script
        await self._generate_intelligent_startup_script()
        
        # Generate documentation and graphs
        await self._generate_documentation()
        
        logger.info("✅ Graph-based generation completed!")
    
    async def _build_dependency_graph(self, template_dir: Path = None):
        """Build the service dependency graph"""
        logger.info("📊 Building service dependency graph...")
        
        # Use predefined course creator graph (template integration can be added later)
        self.dependency_graph = build_course_creator_graph()
        
        # Validate graph
        cycles = self.dependency_graph.detect_circular_dependencies()
        if cycles:
            logger.warning(f"⚠️ Detected circular dependencies: {cycles}")
        
        # Export graph for reference
        graph_json = self.dependency_graph.export_graph("json")
        graph_dot = self.dependency_graph.export_graph("dot")
        
        # Save graph files
        graphs_dir = self.output_dir / "graphs"
        graphs_dir.mkdir(exist_ok=True)
        
        with open(graphs_dir / "dependency_graph.json", 'w') as f:
            f.write(graph_json)
        
        with open(graphs_dir / "dependency_graph.dot", 'w') as f:
            f.write(graph_dot)
        
        logger.info(f"✅ Built dependency graph with {len(self.dependency_graph.services)} services")
    
    async def _analyze_architecture(self):
        """Analyze the overall architecture using the dependency graph"""
        logger.info("🔍 Analyzing architecture with dependency graph...")
        
        # Get generation order
        generation_order = self.dependency_graph.get_service_generation_order()
        logger.info(f"📋 Service generation order: {generation_order}")
        
        # Analyze each service
        for service_name in generation_order:
            analysis = self.dependency_graph.analyze_service_dependencies(service_name)
            interfaces = self.dependency_graph.generate_service_interfaces(service_name)
            
            self.service_interfaces[service_name] = interfaces
            
            # Store context for generation
            self.generation_context[service_name] = {
                "analysis": analysis,
                "interfaces": interfaces,
                "service": self.dependency_graph.services[service_name]
            }
            
            logger.info(f"📊 Analyzed {service_name}: depends on {len(analysis['depends_on'])} services")
        
        # Identify critical path
        critical_path = self.dependency_graph.get_critical_path()
        logger.info(f"🎯 Critical path: {' -> '.join(critical_path)}")
    
    async def _generate_services_by_dependency_order(self):
        """Generate services in dependency order"""
        logger.info("🔧 Generating services by dependency order...")
        
        generation_order = self.dependency_graph.get_service_generation_order()
        
        for service_name in generation_order:
            logger.info(f"🏗️ Generating {service_name} service...")
            await self._generate_service_with_context(service_name)
    
    async def _generate_service_with_context(self, service_name: str):
        """Generate a service with full dependency context"""
        context = self.generation_context[service_name]
        service = context["service"]
        analysis = context["analysis"]
        interfaces = context["interfaces"]
        
        service_dir = self.output_dir / "services" / service_name
        service_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate each file with dependency context
        # Convert service context back to template format for existing methods
        service_template = {
            'name': service_name,
            'port': service.port,
            'database_models': service.database_models,
            'endpoints': service.api_endpoints,
            'description': service.description,
            'dependencies': analysis['depends_on'],
            'interfaces': interfaces
        }
        
        files_to_generate = [
            ('config.py', self._generate_config_file),
            ('models.py', self._generate_models_file),
            ('schemas.py', self._generate_schemas_file),
            ('main.py', self._generate_main_file),
            ('services.py', self._generate_services_file),
            ('dependencies.py', self._generate_dependencies_file),
            ('requirements.txt', self._generate_requirements_file),
            ('run.py', self._generate_run_file),
        ]
        
        for filename, generator_func in files_to_generate:
            try:
                logger.info(f"  📝 Generating {filename} with dependency context...")
                content = await generator_func(service_template)
                
                if content and len(content.strip()) > 10:
                    file_path = service_dir / filename
                    with open(file_path, 'w') as f:
                        f.write(content)
                    
                    # Check if this was a fallback generation
                    if "fallback" in content.lower() or "# no service" in content.lower():
                        logger.info(f"    ⚠️  Created {file_path} (using fallback template)")
                    else:
                        logger.info(f"    ✅ Created {file_path}")
                    
                    # Validate Python files
                    if filename.endswith('.py'):
                        if self._validate_python_file(file_path):
                            logger.info(f"    ✅ {filename} syntax valid")
                        else:
                            logger.warning(f"    ⚠️  {filename} has syntax errors")
                else:
                    logger.warning(f"    ❌ Failed to generate {filename} - no content generated")
                    
            except Exception as e:
                logger.error(f"    ❌ Error generating {filename}: {e}")
        
        logger.info(f"  🎉 Completed {service_name}")
    
    async def _generate_config_file(self, service_template: Dict) -> str:
        """Generate Hydra configuration file with dependency awareness"""
        
        service_name = service_template['name']
        port = service_template.get('port', 8000)
        dependencies = service_template.get('dependencies', [])
        interfaces = service_template.get('interfaces', {})
        
        dependency_info = ""
        if dependencies:
            dependency_info = f"""
Service Dependencies: {[dep['service'] for dep in dependencies]}
Required Service Clients: {[client['service'] for client in interfaces.get('required_clients', [])]}
"""
        
        prompt = f"""Generate a complete Hydra configuration file for the {service_name} microservice.

Service Context:{dependency_info}

Requirements:
- Use Hydra for all configuration management
- Include database, Redis, service URLs, and API keys
- Include configuration for all dependent services
- Add service discovery and health check URLs
- Support different environments (dev, staging, prod)
- Include proper type hints and validation

Create a config.py file with Hydra configuration that includes all service dependencies."""
        
        try:
            response = await self._make_api_call(prompt)
            
            # Extract Python code from response
            if 'config' in response.lower() and 'hydra' in response.lower():
                return self._extract_python_code(response)
            
            # Enhanced fallback template with dependency info
            dep_services = {}
            if dependencies:
                for dep in dependencies:
                    service_name_clean = dep['service'].replace('-', '_').upper()
                    port_map = {
                        'user-management': 8000,
                        'course-generator': 8001, 
                        'content-storage': 8003,
                        'course-management': 8004
                    }
                    dep_port = port_map.get(dep['service'], 8000)
                    dep_services[dep['service'].replace('-', '_')] = f"${{oc.env:{service_name_clean}_URL,http://localhost:{dep_port}}}"
            
            services_config = ", ".join([f'"{k}": "{v}"' for k, v in dep_services.items()]) if dep_services else '# No service dependencies'
            
            return f'''import os
from hydra import compose, initialize
from omegaconf import DictConfig, OmegaConf
from typing import Optional
import logging

logger = logging.getLogger(__name__)

def get_config() -> DictConfig:
    """Get Hydra configuration"""
    try:
        with initialize(config_path="../config", version_base=None):
            cfg = compose(config_name="{service_name}")
            return cfg
    except Exception as e:
        logger.warning(f"Failed to load Hydra config: {{e}}")
        return get_default_config()

def get_default_config() -> DictConfig:
    """Default configuration fallback with service dependencies"""
    config = {{
        "service": {{
            "name": "{service_name}",
            "port": {port},
            "host": "0.0.0.0",
            "debug": True,
            "log_level": "INFO"
        }},
        "database": {{
            "url": "${{oc.env:DATABASE_URL,postgresql://user:pass@localhost/db}}",
            "echo": False,
            "pool_size": 10
        }},
        "redis": {{
            "url": "${{oc.env:REDIS_URL,redis://localhost:6379}}",
            "db": 0
        }},
        "security": {{
            "secret_key": "${{oc.env:SECRET_KEY,your-secret-key}}",
            "algorithm": "HS256",
            "access_token_expire_minutes": 30
        }},
        "services": {{
            {services_config}
        }},
        "anthropic": {{
            "api_key": "${{oc.env:ANTHROPIC_API_KEY,}}"
        }}
    }}
    return OmegaConf.create(config)

# Global config instance
config = get_config()
'''
            
        except Exception as e:
            logger.error(f"Failed to generate config file: {e}")
            return ""
    
    async def _generate_models_file(self, service_template: Dict) -> str:
        """Generate SQLAlchemy models file"""
        
        models_data = service_template.get('database_models', [])
        service_name = service_template['name']
        
        prompt = f"""Generate complete SQLAlchemy models for {service_name} service.

Database models to implement: {json.dumps(models_data, indent=2)}

Requirements:
- Use SQLAlchemy ORM with proper relationships
- Include all fields and constraints from the template
- Add proper indexes and foreign keys
- Include __repr__ methods
- Use UUID primary keys where appropriate
- Add proper imports and Base class

Return only the Python code."""
        
        try:
            response = await self._make_api_call(prompt)
            return self._extract_python_code(response)
            
        except Exception as e:
            logger.error(f"Failed to generate models: {e}")
            return self._get_fallback_models(service_name)
    
    async def _generate_schemas_file(self, service_template: Dict) -> str:
        """Generate Pydantic schemas file"""
        
        models_data = service_template.get('database_models', [])
        service_name = service_template['name']
        
        prompt = f"""Generate complete Pydantic schemas for {service_name} service.

Database models: {json.dumps(models_data, indent=2)}

Requirements:
- Create request/response schemas for all models
- Include proper validation and type hints
- Add BaseModel classes with common functionality
- Include schemas for create, update, and response operations
- Use proper datetime and UUID handling

Return only the Python code."""
        
        try:
            response = await self._make_api_call(prompt)
            return self._extract_python_code(response)
            
        except Exception as e:
            logger.error(f"Failed to generate schemas: {e}")
            return self._get_fallback_schemas(service_name)
    
    async def _generate_main_file(self, service_template: Dict) -> str:
        """Generate FastAPI main application file"""
        
        endpoints = service_template.get('endpoints', [])
        service_name = service_template['name']
        port = service_template.get('port', 8000)
        
        prompt = f"""Generate complete FastAPI main.py file for {service_name} service.

Endpoints to implement: {json.dumps(endpoints, indent=2)}

Requirements:
- Use FastAPI with proper middleware (CORS, logging, etc.)
- Implement ALL endpoints from the template
- Include proper error handling and validation
- Use Hydra config for all settings
- Add health check and root endpoints
- Include proper startup/shutdown events
- Use dependency injection for database and auth
- Add comprehensive logging

Return only the Python code."""
        
        try:
            response = await self._make_api_call(prompt)
            return self._extract_python_code(response)
            
        except Exception as e:
            logger.error(f"Failed to generate main file: {e}")
            return self._get_fallback_main(service_name, port)
    
    async def _generate_services_file(self, service_template: Dict) -> str:
        """Generate business logic services file"""
        
        service_name = service_template['name']
        
        prompt = f"""Generate complete business logic services file for {service_name}.

Requirements:
- Implement all business logic for the service
- Include proper error handling and logging
- Use dependency injection patterns
- Add inter-service communication helpers
- Include data validation and processing
- Use async/await patterns

Return only the Python code."""
        
        try:
            response = await self._make_api_call(prompt)
            return self._extract_python_code(response)
            
        except Exception as e:
            logger.error(f"Failed to generate services: {e}")
            return self._get_fallback_services(service_name)
    
    async def _generate_dependencies_file(self, service_template: Dict) -> str:
        """Generate FastAPI dependencies file"""
        
        service_name = service_template['name']
        
        prompt = f"""Generate FastAPI dependencies.py file for {service_name}.

Requirements:
- Database session dependency
- Authentication dependencies
- Configuration dependencies using Hydra
- Logging setup
- Inter-service HTTP clients
- Error handling utilities

Return only the Python code."""
        
        try:
            response = await self._make_api_call(prompt)
            return self._extract_python_code(response)
            
        except Exception as e:
            logger.error(f"Failed to generate dependencies: {e}")
            return self._get_fallback_dependencies(service_name)
    
    async def _generate_requirements_file(self, service_template: Dict) -> str:
        """Generate requirements.txt file"""
        
        return """fastapi>=0.104.0
uvicorn[standard]>=0.24.0
sqlalchemy>=2.0.0
alembic>=1.12.0
pydantic>=2.4.0
psycopg2-binary>=2.9.0
redis>=5.0.0
httpx>=0.25.0
python-multipart>=0.0.6
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
hydra-core>=1.3.0
omegaconf>=2.3.0
aiofiles>=23.2.1
pytest>=7.4.0
pytest-asyncio>=0.21.0
"""
    
    async def _generate_run_file(self, service_template: Dict) -> str:
        """Generate run.py startup file"""
        
        service_name = service_template['name']
        port = service_template.get('port', 8000)
        
        return f'''#!/usr/bin/env python3
"""
Startup script for {service_name} service
"""

import uvicorn
from config import config

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.service.host,
        port=config.service.port,
        reload=config.service.debug,
        log_level=config.service.log_level.lower()
    )
'''
    
    async def _generate_frontend(self):
        """Generate complete frontend application"""
        
        logger.info("🎨 Generating frontend application...")
        
        frontend_dir = self.output_dir / "frontend"
        frontend_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate main HTML file
        html_content = self._get_frontend_html()
        with open(frontend_dir / "index.html", 'w') as f:
            f.write(html_content)
        
        # Generate CSS
        css_dir = frontend_dir / "css"
        css_dir.mkdir(exist_ok=True)
        css_content = self._get_frontend_css()
        with open(css_dir / "main.css", 'w') as f:
            f.write(css_content)
        
        # Generate JavaScript
        js_dir = frontend_dir / "js"
        js_dir.mkdir(exist_ok=True)
        js_content = self._get_frontend_js()
        with open(js_dir / "main.js", 'w') as f:
            f.write(js_content)
        
        logger.info("  ✅ Frontend generated")
    
    async def _generate_startup_script(self):
        """Generate master startup script"""
        
        logger.info("🚀 Generating startup script...")
        
        startup_content = f'''#!/usr/bin/env python3
"""
Master startup script for Course Creator Platform
"""

import subprocess
import time
import sys
import signal
import threading
from pathlib import Path

class PlatformManager:
    def __init__(self):
        self.processes = {{}}
        self.services = [
            {{"name": "user-management", "port": 8000, "dir": "services/user-management"}},
            {{"name": "course-generator", "port": 8001, "dir": "services/course-generator"}},
            {{"name": "content-storage", "port": 8003, "dir": "services/content-storage"}},
            {{"name": "course-management", "port": 8004, "dir": "services/course-management"}},
        ]
        self.frontend_port = 3000
    
    def start_all(self):
        """Start all services"""
        print("🚀 Starting Course Creator Platform...")
        
        # Start backend services
        for service in self.services:
            self.start_service(service)
        
        # Start frontend server
        self.start_frontend()
        
        print("\\n✅ Platform started successfully!")
        print("\\n🌐 Access URLs:")
        for service in self.services:
            print(f"  {service['name']}: http://localhost:{service['port']}")
        print(f"  Frontend: http://localhost:{self.frontend_port}")
        print("\\nPress Ctrl+C to stop all services...")
        
        # Wait for interrupt
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop_all()
    
    def start_service(self, service):
        """Start individual service"""
        try:
            service_dir = Path(service["dir"])
            if not service_dir.exists():
                print(f"❌ Service directory not found: {service_dir}")
                return
            
            cmd = [sys.executable, "run.py"]
            process = subprocess.Popen(
                cmd,
                cwd=service_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            self.processes[service["name"]] = process
            print(f"  ✅ Started {service['name']} on port {service['port']}")
            
        except Exception as e:
            print(f"  ❌ Failed to start {service['name']}: {e}")
    
    def start_frontend(self):
        """Start frontend server"""
        try:
            import http.server
            import socketserver
            import os
            
            def serve_frontend():
                os.chdir("frontend")
                handler = http.server.SimpleHTTPRequestHandler
                with socketserver.TCPServer(("", self.frontend_port), handler) as httpd:
                    httpd.serve_forever()
            
            frontend_thread = threading.Thread(target=serve_frontend, daemon=True)
            frontend_thread.start()
            print(f"  ✅ Started frontend on port {self.frontend_port}")
            
        except Exception as e:
            print(f"  ❌ Failed to start frontend: {e}")
    
    def stop_all(self):
        """Stop all services"""
        print("\\n🛑 Stopping all services...")
        
        for name, process in self.processes.items():
            try:
                process.terminate()
                process.wait(timeout=5)
                print(f"  ✅ Stopped {name}")
            except:
                process.kill()
                print(f"  🔪 Force killed {name}")
        
        print("✅ All services stopped")

if __name__ == "__main__":
    manager = PlatformManager()
    manager.start_all()
'''
        
        with open(self.output_dir / "start-platform.py", 'w') as f:
            f.write(startup_content)
        
        # Make executable
        os.chmod(self.output_dir / "start-platform.py", 0o755)
        
        logger.info("  ✅ Startup script created")
    
    async def _generate_service_communication(self):
        """Generate inter-service communication patterns"""
        logger.info("🔗 Generating service communication patterns...")
        
        # Create communication documentation
        comm_dir = self.output_dir / "docs"
        comm_dir.mkdir(exist_ok=True)
        
        communication_doc = self._generate_communication_documentation()
        with open(comm_dir / "service_communication.md", 'w') as f:
            f.write(communication_doc)
        
        logger.info("  ✅ Service communication documentation generated")
    
    def _generate_communication_documentation(self) -> str:
        """Generate documentation for service communication patterns"""
        doc = "# Service Communication Patterns\n\n"
        
        if not hasattr(self, 'generation_context'):
            doc += "Service communication patterns will be documented here.\n"
            return doc
        
        for service_name, context in self.generation_context.items():
            analysis = context["analysis"]
            doc += f"## {service_name}\n\n"
            
            if analysis["depends_on"]:
                doc += "### Dependencies:\n"
                for dep in analysis["depends_on"]:
                    doc += f"- **{dep['service']}**: {dep['description']} ({dep['type']})\n"
                doc += "\n"
            
            if analysis["depended_by"]:
                doc += "### Consumers:\n"
                for dep in analysis["depended_by"]:
                    doc += f"- **{dep['service']}**: {dep['description']} ({dep['type']})\n"
                doc += "\n"
        
        return doc
    
    async def _generate_frontend_with_integration(self):
        """Generate frontend with service integration"""
        logger.info("🎨 Generating frontend with service integration...")
        
        frontend_dir = self.output_dir / "frontend"
        frontend_dir.mkdir(exist_ok=True)
        
        # Generate service-aware frontend
        html_content = self._generate_integrated_frontend_html()
        js_content = self._generate_integrated_frontend_js()
        css_content = self._generate_integrated_frontend_css()
        
        with open(frontend_dir / "index.html", 'w') as f:
            f.write(html_content)
        
        css_dir = frontend_dir / "css"
        css_dir.mkdir(exist_ok=True)
        with open(css_dir / "main.css", 'w') as f:
            f.write(css_content)
        
        js_dir = frontend_dir / "js"
        js_dir.mkdir(exist_ok=True)
        with open(js_dir / "main.js", 'w') as f:
            f.write(js_content)
        
        logger.info("  ✅ Frontend with service integration generated")
    
    def _generate_integrated_frontend_html(self) -> str:
        """Generate HTML with service integration"""
        if not hasattr(self, 'dependency_graph') or not self.dependency_graph:
            services = ["user-management", "course-generator", "content-storage", "course-management"]
        else:
            services = list(self.dependency_graph.services.keys())
        
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Course Creator Platform</title>
    <link rel="stylesheet" href="css/main.css">
</head>
<body>
    <header>
        <h1>Course Creator Platform</h1>
        <nav>
            <a href="#dashboard">Dashboard</a>
            <a href="#courses">Courses</a>
            <a href="#create">Create Course</a>
            <a href="#profile">Profile</a>
            <a href="#services">Services</a>
        </nav>
    </header>
    
    <main id="main-content">
        <section id="dashboard">
            <h2>Platform Dashboard</h2>
            <div class="service-status">
                <h3>Service Status</h3>
                <div id="service-health">
                    {' '.join(f'<div class="service-item" data-service="{service}"><span class="service-name">{service}</span><span class="service-status">Checking...</span></div>' for service in services)}
                </div>
            </div>
        </section>
        
        <section id="services" style="display:none;">
            <h2>Service Architecture</h2>
            <div id="dependency-graph">
                <p>Service dependency visualization will be loaded here.</p>
            </div>
        </section>
    </main>
    
    <script src="js/main.js"></script>
</body>
</html>'''
    
    def _generate_integrated_frontend_js(self) -> str:
        """Generate JavaScript with service integration"""
        if not hasattr(self, 'dependency_graph') or not self.dependency_graph:
            services = {
                "user-management": 8000,
                "course-generator": 8001, 
                "content-storage": 8003,
                "course-management": 8004
            }
        else:
            services = {name: service.port for name, service in self.dependency_graph.services.items()}
        
        return f'''// Service configuration based on dependency graph
const SERVICES = {json.dumps(services)};
const SERVICE_URLS = {{}};

// Initialize service URLs
Object.keys(SERVICES).forEach(service => {{
    SERVICE_URLS[service] = `http://localhost:${{SERVICES[service]}}`;
}});

class ServiceHealthMonitor {{
    constructor() {{
        this.healthStatus = {{}};
        this.checkInterval = 30000; // 30 seconds
    }}
    
    async checkServiceHealth(serviceName) {{
        try {{
            const response = await fetch(`${{SERVICE_URLS[serviceName]}}/health`, {{
                method: 'GET',
                timeout: 5000
            }});
            
            if (response.ok) {{
                const health = await response.json();
                this.healthStatus[serviceName] = {{
                    status: 'healthy',
                    lastCheck: new Date(),
                    details: health
                }};
            }} else {{
                throw new Error(`HTTP ${{response.status}}`);
            }}
        }} catch (error) {{
            this.healthStatus[serviceName] = {{
                status: 'unhealthy',
                lastCheck: new Date(),
                error: error.message
            }};
        }}
        
        this.updateServiceDisplay(serviceName);
    }}
    
    updateServiceDisplay(serviceName) {{
        const element = document.querySelector(`[data-service="${{serviceName}}"] .service-status`);
        if (element) {{
            const status = this.healthStatus[serviceName];
            element.textContent = status.status;
            element.className = `service-status ${{status.status}}`;
        }}
    }}
    
    startMonitoring() {{
        // Initial check
        Object.keys(SERVICES).forEach(service => {{
            this.checkServiceHealth(service);
        }});
        
        // Periodic checks
        setInterval(() => {{
            Object.keys(SERVICES).forEach(service => {{
                this.checkServiceHealth(service);
            }});
        }}, this.checkInterval);
    }}
}}

// Initialize application
document.addEventListener('DOMContentLoaded', function() {{
    const healthMonitor = new ServiceHealthMonitor();
    
    // Start health monitoring
    healthMonitor.startMonitoring();
    
    // Navigation handling
    document.querySelectorAll('nav a').forEach(link => {{
        link.addEventListener('click', function(e) {{
            e.preventDefault();
            const target = this.getAttribute('href').substring(1);
            showSection(target);
        }});
    }});
    
    function showSection(sectionId) {{
        document.querySelectorAll('main section').forEach(section => {{
            section.style.display = 'none';
        }});
        
        const targetSection = document.getElementById(sectionId);
        if (targetSection) {{
            targetSection.style.display = 'block';
        }}
    }}
    
    console.log('Course Creator Platform loaded with dependency graph integration');
}});'''
    
    def _generate_integrated_frontend_css(self) -> str:
        """Generate CSS with service status styling"""
        return '''body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 0;
    background-color: #f5f5f5;
}

header {
    background-color: #2c3e50;
    color: white;
    padding: 1rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

nav a {
    color: white;
    text-decoration: none;
    margin: 0 1rem;
    padding: 0.5rem 1rem;
    border-radius: 4px;
    transition: background-color 0.3s;
}

nav a:hover {
    background-color: #34495e;
}

main {
    padding: 2rem;
}

.service-status {
    background: white;
    border-radius: 8px;
    padding: 1rem;
    margin: 1rem 0;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.service-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.5rem 0;
    border-bottom: 1px solid #eee;
}

.service-item:last-child {
    border-bottom: none;
}

.service-name {
    font-weight: bold;
}

.service-status.healthy {
    color: #27ae60;
    background-color: #d5f5d9;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
}

.service-status.unhealthy {
    color: #e74c3c;
    background-color: #fdf2f2;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
}

button {
    background-color: #3498db;
    color: white;
    border: none;
    padding: 0.5rem 1rem;
    border-radius: 4px;
    cursor: pointer;
    transition: background-color 0.3s;
}

button:hover {
    background-color: #2980b9;
}

#dependency-graph {
    background: white;
    border-radius: 8px;
    padding: 2rem;
    margin: 1rem 0;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    min-height: 400px;
}'''
    
    async def _generate_intelligent_startup_script(self):
        """Generate intelligent startup script with dependency awareness"""
        logger.info("🚀 Generating intelligent startup script...")
        
        if hasattr(self, 'dependency_graph') and self.dependency_graph:
            generation_order = self.dependency_graph.get_service_generation_order()
            services_config = []
            for service_name in generation_order:
                service = self.dependency_graph.services[service_name]
                services_config.append(f'{{"name": "{service_name}", "port": {service.port}, "dir": "services/{service_name}"}}')
        else:
            generation_order = ["user-management", "course-generator", "content-storage", "course-management"]
            services_config = [
                '{"name": "user-management", "port": 8000, "dir": "services/user-management"}',
                '{"name": "course-generator", "port": 8001, "dir": "services/course-generator"}',
                '{"name": "content-storage", "port": 8003, "dir": "services/content-storage"}',
                '{"name": "course-management", "port": 8004, "dir": "services/course-management"}'
            ]
        
        startup_content = f'''#!/usr/bin/env python3
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
        self.processes = {{}}
        self.service_order = {generation_order}
        self.services = {{
            {', '.join(f'"{service.split(": ")[1].split(",")[0].strip()[1:-1]}": {service}' for service in services_config)}
        }}
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
                print(f"❌ Failed to start {{service_name}}, stopping...")
                await self.stop_all()
                return False
        
        # Start frontend server
        await self.start_frontend()
        
        print("\\n✅ Platform started successfully!")
        print("\\n🌐 Access URLs:")
        for service_name in self.service_order:
            service = self.services[service_name]
            print(f"  {{service_name}}: http://localhost:{{service['port']}}")
        print(f"  Frontend: http://localhost:{{self.frontend_port}}")
        print("\\nPress Ctrl+C to stop all services...")
        
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
            print(f"❌ Service directory not found: {{service_dir}}")
            return False
        
        print(f"  🔧 Starting {{service_name}}...")
        
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
            print(f"  ✅ {{service_name}} started and healthy on port {{service['port']}}")
            return True
        else:
            print(f"  ❌ {{service_name}} failed to become healthy")
            return False
    
    async def wait_for_service_health(self, service_name: str, port: int) -> bool:
        """Wait for service to respond to health checks"""
        health_url = f"http://localhost:{{port}}/health"
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
            print(f"  ✅ Started frontend on port {{self.frontend_port}}")
            
        except Exception as e:
            print(f"  ❌ Failed to start frontend: {{e}}")
    
    async def stop_all(self):
        """Stop all services in reverse order"""
        print("\\n🛑 Stopping all services...")
        
        # Stop in reverse order
        for service_name in reversed(self.service_order):
            if service_name in self.processes:
                try:
                    process = self.processes[service_name]
                    process.terminate()
                    process.wait(timeout=5)
                    print(f"  ✅ Stopped {{service_name}}")
                except:
                    process.kill()
                    print(f"  🔪 Force killed {{service_name}}")
        
        print("✅ All services stopped")

async def main():
    manager = IntelligentPlatformManager()
    await manager.start_all()

if __name__ == "__main__":
    asyncio.run(main())
'''
        
        with open(self.output_dir / "start-platform.py", 'w') as f:
            f.write(startup_content)
        
        # Make executable
        os.chmod(self.output_dir / "start-platform.py", 0o755)
        
        logger.info("  ✅ Intelligent startup script created")
    
    async def _generate_documentation(self):
        """Generate comprehensive documentation"""
        logger.info("📚 Generating documentation...")
        
        docs_dir = self.output_dir / "docs"
        docs_dir.mkdir(exist_ok=True)
        
        # Generate architecture documentation
        arch_doc = self._generate_architecture_documentation()
        with open(docs_dir / "architecture.md", 'w') as f:
            f.write(arch_doc)
        
        logger.info("  ✅ Documentation generated")
    
    def _generate_architecture_documentation(self) -> str:
        """Generate architecture documentation"""
        doc = "# Course Creator Platform Architecture\n\n"
        doc += "## Service Dependency Graph\n\n"
        
        if not hasattr(self, 'dependency_graph') or not self.dependency_graph:
            doc += "Architecture documentation will be generated here.\n"
            return doc
        
        # Add service overview
        doc += "### Services\n\n"
        for service_name, service in self.dependency_graph.services.items():
            doc += f"#### {service_name}\n"
            doc += f"- **Type**: {service.service_type.value}\n"
            doc += f"- **Port**: {service.port}\n"
            doc += f"- **Description**: {service.description}\n"
            doc += f"- **Responsibilities**: {', '.join(service.responsibilities)}\n\n"
        
        # Add dependency information
        doc += "### Dependencies\n\n"
        for dep in self.dependency_graph.dependencies:
            doc += f"- **{dep.from_service}** → **{dep.to_service}**\n"
            doc += f"  - Type: {dep.dependency_type.value}\n"
            doc += f"  - Description: {dep.description}\n"
            doc += f"  - Required: {dep.required}\n\n"
        
        return doc
    
    async def _make_api_call(self, prompt: str, max_tokens: int = 4000, max_retries: int = 3) -> str:
        """Make API call to Claude with retry logic for handling server errors"""
        
        import time
        
        for attempt in range(max_retries):
            try:
                response = self.client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=max_tokens,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
                
            except Exception as e:
                error_str = str(e)
                
                # Check if it's a server error (500) or rate limit that we should retry
                if "500" in error_str or "Internal server error" in error_str or "rate_limit" in error_str.lower():
                    if attempt < max_retries - 1:
                        wait_time = (2 ** attempt) + 1  # Exponential backoff: 2, 5, 9 seconds
                        logger.warning(f"API error (attempt {attempt + 1}/{max_retries}): {e}")
                        logger.info(f"Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                        continue
                
                logger.error(f"API call failed after {max_retries} attempts: {e}")
                return ""
        
        return ""
    
    def _extract_python_code(self, text: str) -> str:
        """Extract Python code from Claude's response"""
        
        import re
        
        # Look for code blocks
        patterns = [
            r'```python\s*\n(.*?)```',
            r'```\s*\n(.*?)```',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                if len(match.strip()) > 50:
                    return match.strip()
        
        # If no code blocks, return the whole text if it looks like Python
        if 'import ' in text or 'def ' in text or 'class ' in text:
            return text.strip()
        
        return ""
    
    def _validate_python_file(self, file_path: Path) -> bool:
        """Validate Python file syntax"""
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            ast.parse(content)
            return True
        except:
            return False
    
    # Fallback templates for when Claude fails
    def _get_fallback_models(self, service_name: str) -> str:
        return f'''from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class BaseModel(Base):
    __abstract__ = True
    
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
'''
    
    def _get_fallback_schemas(self, service_name: str) -> str:
        return f'''from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class BaseSchema(BaseModel):
    class Config:
        from_attributes = True

class HealthResponse(BaseSchema):
    status: str
    service: str
'''
    
    def _get_fallback_main(self, service_name: str, port: int) -> str:
        return f'''from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import config

app = FastAPI(title="{service_name.title()} Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {{"service": "{service_name}", "status": "running"}}

@app.get("/health")
async def health():
    return {{"status": "healthy"}}
'''
    
    def _get_fallback_services(self, service_name: str) -> str:
        return f'''import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class {service_name.replace("-", "_").title()}Service:
    def __init__(self):
        self.name = "{service_name}"
    
    async def get_status(self) -> Dict[str, Any]:
        return {{"status": "healthy", "service": self.name}}
'''
    
    def _get_fallback_dependencies(self, service_name: str) -> str:
        return f'''from fastapi import Depends
from config import config
import logging

logger = logging.getLogger(__name__)

async def get_config():
    return config

async def get_logger():
    return logger
'''
    
    def _get_frontend_html(self) -> str:
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Course Creator Platform</title>
    <link rel="stylesheet" href="css/main.css">
</head>
<body>
    <header>
        <h1>Course Creator Platform</h1>
        <nav>
            <a href="#home">Home</a>
            <a href="#courses">Courses</a>
            <a href="#create">Create Course</a>
            <a href="#profile">Profile</a>
        </nav>
    </header>
    
    <main id="main-content">
        <section id="home">
            <h2>Welcome to Course Creator</h2>
            <p>Create and manage online courses with AI assistance.</p>
            <button onclick="loadCourses()">View Courses</button>
        </section>
    </main>
    
    <script src="js/main.js"></script>
</body>
</html>'''
    
    def _get_frontend_css(self) -> str:
        return '''body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 0;
    background-color: #f5f5f5;
}

header {
    background-color: #2c3e50;
    color: white;
    padding: 1rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

nav a {
    color: white;
    text-decoration: none;
    margin: 0 1rem;
    padding: 0.5rem 1rem;
    border-radius: 4px;
    transition: background-color 0.3s;
}

nav a:hover {
    background-color: #34495e;
}

main {
    padding: 2rem;
}

button {
    background-color: #3498db;
    color: white;
    border: none;
    padding: 0.5rem 1rem;
    border-radius: 4px;
    cursor: pointer;
}

button:hover {
    background-color: #2980b9;
}

.course-card {
    background: white;
    border-radius: 8px;
    padding: 1rem;
    margin: 1rem 0;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}'''
    
    def _get_frontend_js(self) -> str:
        return '''const API_BASE = 'http://localhost:8000';

async function loadCourses() {
    try {
        const response = await fetch(`${API_BASE}/api/courses`);
        const data = await response.json();
        displayCourses(data.courses || []);
    } catch (error) {
        console.error('Error loading courses:', error);
        alert('Failed to load courses');
    }
}

function displayCourses(courses) {
    const main = document.getElementById('main-content');
    main.innerHTML = `
        <section>
            <h2>Available Courses</h2>
            <div id="courses-list">
                ${courses.map(course => `
                    <div class="course-card">
                        <h3>${course.title}</h3>
                        <p>${course.description}</p>
                        <button onclick="viewCourse(${course.id})">View Course</button>
                    </div>
                `).join('')}
            </div>
        </section>
    `;
}

async function viewCourse(courseId) {
    try {
        const response = await fetch(`${API_BASE}/api/courses/${courseId}`);
        const course = await response.json();
        
        const main = document.getElementById('main-content');
        main.innerHTML = `
            <section>
                <h2>${course.title}</h2>
                <p>${course.description}</p>
                <p>Instructor: ${course.instructor}</p>
                <p>Duration: ${course.duration_hours} hours</p>
                <button onclick="loadCourses()">Back to Courses</button>
            </section>
        `;
    } catch (error) {
        console.error('Error loading course:', error);
        alert('Failed to load course details');
    }
}

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    console.log('Course Creator Platform loaded');
});'''

async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Course Platform Generator")
    parser.add_argument("--api-key", help="Anthropic API key (or set ANTHROPIC_API_KEY env var)")
    parser.add_argument("--templates", default="tools/code-generation/templates", help="Templates directory")
    parser.add_argument("--output", default=".", help="Output directory")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Get API key
    api_key = args.api_key or os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        logger.error("API key required. Set ANTHROPIC_API_KEY or use --api-key")
        sys.exit(1)
    
    generator = PlatformGenerator(
        api_key=api_key,
        output_dir=Path(args.output),
        verbose=args.verbose
    )
    
    try:
        await generator.generate_platform(Path(args.templates))
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())