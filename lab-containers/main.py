"""
Enhanced Lab Container Management Service
Manages individual Docker containers for student lab environments with:
- Per-student lab containers with persistent storage
- Instructor lab management capabilities
- Dynamic image building on-demand
- Automatic lifecycle management (login/logout)
- State persistence across sessions
"""

import asyncio
import json
import os
import shutil
import tarfile
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Union
from uuid import uuid4

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Query, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import Response, StreamingResponse, FileResponse
from pydantic import BaseModel
import httpx
import zipfile
import io
import structlog
import psutil
from analytics_client import analytics_client

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()
security = HTTPBearer()

app = FastAPI(title="Enhanced Lab Container Manager", version="2.0.0")

# Docker client - Initialize later to handle Docker-in-Docker properly
docker_client = None

# Configuration from environment
MAX_CONCURRENT_LABS = int(os.getenv('MAX_CONCURRENT_LABS', '50'))
LAB_SESSION_TIMEOUT = int(os.getenv('LAB_SESSION_TIMEOUT', '3600'))  # 1 hour
LAB_STORAGE_PATH = os.getenv('LAB_STORAGE_PATH', '/home/bbrelin/course-creator/lab-storage')
LAB_IMAGE_REGISTRY = os.getenv('LAB_IMAGE_REGISTRY', 'course-creator/labs')

# In-memory storage for active lab sessions
active_labs: Dict[str, Dict] = {}  # lab_id -> lab_info
user_labs: Dict[str, str] = {}     # user_id -> lab_id mapping

def get_docker_client():
    """Initialize Docker client to connect to host Docker daemon"""
    global docker_client
    if docker_client is None:
        try:
            # Use subprocess to call docker CLI directly instead of Python API
            # This avoids the Docker-in-Docker API issues
            import subprocess
            result = subprocess.run(['docker', 'version'], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("Docker CLI available - using subprocess for Docker operations")
                # Set a flag to use CLI instead of API
                docker_client = "CLI_MODE"
            else:
                raise RuntimeError("Docker CLI not available")
        except Exception as e:
            logger.error("Failed to connect to Docker daemon", error=str(e))
            raise RuntimeError(f"Cannot connect to Docker daemon: {e}")
    
    return docker_client

def docker_run_container(image, name, ports, environment, volumes, network, memory_limit, cpu_limit):
    """Run a Docker container using CLI"""
    import subprocess
    
    cmd = [
        'docker', 'run', '-d',
        '--name', name,
        '--network', network,
        '--memory', memory_limit,
        '--cpus', str(cpu_limit/100000),  # Convert to CPU cores
        '--restart', 'unless-stopped'
    ]
    
    # Add port mappings
    for container_port, host_port in ports.items():
        cmd.extend(['-p', f'{host_port}:{container_port}'])
    
    # Add environment variables
    for key, value in environment.items():
        cmd.extend(['-e', f'{key}={value}'])
    
    # Add volume mounts
    for host_path, mount in volumes.items():
        cmd.extend(['-v', f'{host_path}:{mount["bind"]}'])
    
    # Add security constraints (but allow sudo for file operations)
    cmd.extend(['--cap-drop', 'ALL'])
    cmd.extend(['--cap-add', 'CHOWN'])
    cmd.extend(['--cap-add', 'DAC_OVERRIDE']) 
    cmd.extend(['--cap-add', 'FOWNER'])
    cmd.extend(['--cap-add', 'SETGID'])
    cmd.extend(['--cap-add', 'SETUID'])
    # Note: Removed no-new-privileges to allow sudo for workspace permissions
    
    cmd.append(image)
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        container_id = result.stdout.strip()
        logger.info("Container created successfully", container_id=container_id)
        return container_id
    else:
        logger.error("Failed to create container", error=result.stderr)
        raise RuntimeError(f"Failed to create container: {result.stderr}")

def docker_stop_container(container_id):
    """Stop and remove a Docker container using CLI"""
    import subprocess
    
    # Stop container
    subprocess.run(['docker', 'stop', container_id], capture_output=True)
    # Remove container
    result = subprocess.run(['docker', 'rm', container_id], capture_output=True, text=True)
    
    if result.returncode == 0:
        logger.info("Container stopped and removed", container_id=container_id)
    else:
        logger.warning("Failed to remove container", container_id=container_id, error=result.stderr)

def docker_list_containers(name_filter=None):
    """List Docker containers using CLI"""
    import subprocess
    
    cmd = ['docker', 'ps', '-a', '--format', '{{.ID}}\t{{.Names}}\t{{.Status}}']
    if name_filter:
        cmd.extend(['--filter', f'name={name_filter}'])
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        containers = []
        for line in result.stdout.strip().split('\n'):
            if line:
                parts = line.split('\t')
                containers.append({
                    'id': parts[0],
                    'name': parts[1],
                    'status': parts[2]
                })
        return containers
    else:
        logger.error("Failed to list containers", error=result.stderr)
        return []


class LabCreateRequest(BaseModel):
    user_id: str
    course_id: str
    lab_type: str
    lab_config: Dict = {}
    timeout_minutes: Optional[int] = 60
    instructor_mode: Optional[bool] = False
    custom_dockerfile: Optional[str] = None
    preferred_ide: Optional[str] = "terminal"  # terminal, vscode, jupyter, intellij
    enable_multi_ide: Optional[bool] = True


class StudentLabRequest(BaseModel):
    user_id: str
    course_id: str


class IDEInfo(BaseModel):
    name: str
    port: int
    enabled: bool
    healthy: bool
    url: str

class LabSession(BaseModel):
    lab_id: str
    user_id: str
    course_id: str
    lab_type: str
    container_id: Optional[str]
    port: Optional[int]  # Main port (base port)
    ide_ports: Dict[str, int] = {}  # IDE-specific ports: {'terminal': 8080, 'vscode': 8081, etc.}
    status: str  # 'building', 'starting', 'running', 'paused', 'stopped', 'error'
    created_at: datetime
    expires_at: datetime
    last_accessed: datetime
    instructor_mode: bool
    storage_path: str
    access_url: Optional[str] = None
    preferred_ide: str = "terminal"
    multi_ide_enabled: bool = False
    available_ides: Dict[str, IDEInfo] = {}


class AIAssistantRequest(BaseModel):
    lab_id: str
    ide_type: str  # 'vscode', 'jupyter', 'terminal'
    action: str  # 'read_file', 'write_file', 'execute_code', 'get_workspace', 'terminal_command'
    payload: Dict  # Action-specific data
    ai_session_id: str  # Track AI session for logging

class AIAssistantResponse(BaseModel):
    success: bool
    data: Optional[Dict] = None
    error: Optional[str] = None
    ide_type: str
    action: str

class LabListResponse(BaseModel):
    labs: List[LabSession]
    active_count: int
    max_concurrent: int


class InstructorLabManagement(BaseModel):
    course_id: str
    students: List[Dict]  # [{user_id, username, lab_status, last_accessed}]


class DynamicImageBuilder:
    """Handles dynamic Docker image building for lab environments"""
    
    @staticmethod
    async def build_lab_image(lab_type: str, course_id: str, lab_config: Dict, 
                            custom_dockerfile: Optional[str] = None) -> str:
        """Build a custom lab image on-demand"""
        
        image_tag = f"{LAB_IMAGE_REGISTRY}:{lab_type}-{course_id}-{int(time.time())}"
        
        # Create temporary build context
        with tempfile.TemporaryDirectory() as build_dir:
            build_path = Path(build_dir)
            
            if custom_dockerfile:
                # Use custom Dockerfile provided by instructor
                dockerfile_content = custom_dockerfile
            else:
                # Generate Dockerfile based on lab type
                dockerfile_content = DynamicImageBuilder._generate_dockerfile(lab_type, lab_config)
            
            # Write Dockerfile
            (build_path / "Dockerfile").write_text(dockerfile_content)
            
            # Create startup script
            startup_script = DynamicImageBuilder._generate_startup_script(lab_type, lab_config)
            (build_path / "lab-startup.py").write_text(startup_script)
            
            # Create lab configuration file
            (build_path / "lab-config.json").write_text(json.dumps(lab_config, indent=2))
            
            # Build the image
            logger.info("Building lab image", image_tag=image_tag, lab_type=lab_type)
            
            try:
                # Build image using Docker CLI
                import subprocess
                build_cmd = [
                    'docker', 'build',
                    '--tag', image_tag,
                    '--rm',
                    '--force-rm',
                    str(build_path)
                ]
                
                result = subprocess.run(build_cmd, capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    logger.info("Lab image built successfully", image_tag=image_tag)
                    return image_tag
                else:
                    logger.error("Failed to build lab image", error=result.stderr, image_tag=image_tag)
                    raise HTTPException(status_code=500, detail=f"Failed to build lab image: {result.stderr}")
                
            except subprocess.TimeoutExpired as e:
                logger.error("Docker build timeout", error=str(e), image_tag=image_tag)
                raise HTTPException(status_code=500, detail=f"Docker build timeout: {str(e)}")
            except Exception as e:
                logger.error("Failed to build lab image", error=str(e), image_tag=image_tag)
                raise HTTPException(status_code=500, detail=f"Failed to build lab image: {str(e)}")
    
    @staticmethod
    def _generate_dockerfile(lab_type: str, lab_config: Dict) -> str:
        """Generate Dockerfile content based on lab type"""
        
        base_images = {
            'python': 'python:3.10-slim',
            'javascript': 'node:18-slim',
            'web': 'nginx:alpine',
            'java': 'openjdk:17-slim',
            'default': 'ubuntu:22.04'
        }
        
        base_image = base_images.get(lab_type, base_images['default'])
        
        if lab_type == 'python':
            return f"""
FROM {base_image}

ENV PYTHONDONTWRITEBYTECODE=1 \\
    PYTHONUNBUFFERED=1 \\
    DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \\
    curl git nano vim wget build-essential \\
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \\
    jupyter jupyterlab numpy pandas matplotlib seaborn \\
    requests flask fastapi pytest black pylint

# Install custom packages if specified
{DynamicImageBuilder._get_custom_packages_install(lab_config, 'pip')}

RUN groupadd -r labuser && useradd -r -g labuser -m -d /home/labuser labuser
WORKDIR /home/labuser/workspace
RUN mkdir -p /home/labuser/workspace/{{assignments,solutions,data,notebooks}}
RUN chown -R labuser:labuser /home/labuser
USER labuser

COPY lab-startup.py /home/labuser/lab-startup.py
COPY lab-config.json /home/labuser/lab-config.json

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8080/ || exit 1

CMD ["python", "/home/labuser/lab-startup.py"]
"""
        
        elif lab_type == 'javascript':
            return f"""
FROM {base_image}

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \\
    curl git nano vim wget python3 python3-pip build-essential \\
    && rm -rf /var/lib/apt/lists/*

RUN npm install -g \\
    nodemon express-generator create-react-app @vue/cli \\
    typescript ts-node eslint prettier jest

# Install custom packages if specified
{DynamicImageBuilder._get_custom_packages_install(lab_config, 'npm')}

RUN groupadd -r labuser && useradd -r -g labuser -m -d /home/labuser labuser
WORKDIR /home/labuser/workspace
RUN mkdir -p /home/labuser/workspace/{{assignments,solutions,projects,static}}
RUN chown -R labuser:labuser /home/labuser
USER labuser

COPY lab-startup.py /home/labuser/lab-startup.py
COPY lab-config.json /home/labuser/lab-config.json

EXPOSE 8080
CMD ["node", "/home/labuser/lab-startup.py"]
"""
        
        else:
            # Default/generic lab environment
            return f"""
FROM {base_image}

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \\
    curl git nano vim wget build-essential python3 python3-pip nodejs npm \\
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -r labuser && useradd -r -g labuser -m -d /home/labuser labuser
WORKDIR /home/labuser/workspace
RUN mkdir -p /home/labuser/workspace/{{assignments,solutions,projects}}
RUN chown -R labuser:labuser /home/labuser
USER labuser

COPY lab-startup.py /home/labuser/lab-startup.py
COPY lab-config.json /home/labuser/lab-config.json

EXPOSE 8080
CMD ["python3", "/home/labuser/lab-startup.py"]
"""
    
    @staticmethod
    def _get_custom_packages_install(lab_config: Dict, package_manager: str) -> str:
        """Generate package installation commands"""
        if 'packages' not in lab_config or not lab_config['packages']:
            return ""
        
        packages = ' '.join(lab_config['packages'])
        
        if package_manager == 'pip':
            return f"RUN pip install --no-cache-dir {packages}"
        elif package_manager == 'npm':
            return f"RUN npm install -g {packages}"
        else:
            return ""
    
    @staticmethod
    def _generate_startup_script(lab_type: str, lab_config: Dict) -> str:
        """Generate startup script for the lab container"""
        
        return f'''#!/usr/bin/env python3
"""
Dynamic Lab Startup Script
Generated for lab type: {lab_type}
"""

import json
import os
import subprocess
import sys
from pathlib import Path

def setup_lab_environment():
    """Set up the lab environment based on configuration"""
    
    # Load lab configuration
    with open('/home/labuser/lab-config.json', 'r') as f:
        lab_config = json.load(f)
    
    session_id = os.getenv('LAB_SESSION_ID', 'default')
    user_id = os.getenv('USER_ID', 'student')
    course_id = os.getenv('COURSE_ID', 'default-course')
    
    print(f"Setting up {{lab_type}} lab for session: {{session_id}}")
    print(f"User: {{user_id}}, Course: {{course_id}}")
    
    workspace = Path('/home/labuser/workspace')
    
    # Create session info
    session_info = {{
        'session_id': session_id,
        'user_id': user_id,
        'course_id': course_id,
        'lab_type': '{lab_type}',
        'config': lab_config
    }}
    
    (workspace / 'session_info.json').write_text(json.dumps(session_info, indent=2))
    
    # Create starter files if specified
    if 'starter_files' in lab_config:
        for filename, content in lab_config['starter_files'].items():
            file_path = workspace / 'assignments' / filename
            file_path.parent.mkdir(exist_ok=True)
            file_path.write_text(content)
            print(f"Created starter file: {{filename}}")
    
    print("Lab environment setup complete!")

def start_lab_server():
    """Start the appropriate server for this lab type"""
    print("Starting lab server...")
    
    {"# Start JupyterLab for Python" if lab_type == "python" else "# Start Express server for JavaScript" if lab_type == "javascript" else "# Start generic web server"}
    
    {'subprocess.run(["jupyter", "lab", "--ip=0.0.0.0", "--port=8080", "--no-browser", "--allow-root", "--NotebookApp.token=", "--NotebookApp.password=", "--NotebookApp.allow_origin=*"])' if lab_type == "python" else 'subprocess.run(["node", "index.js"])' if lab_type == "javascript" else 'subprocess.run(["python3", "-m", "http.server", "8080"])'}

if __name__ == "__main__":
    setup_lab_environment()
    start_lab_server()
'''


@app.get("/")
async def root():
    """Root endpoint"""
    return {"service": "Enhanced Lab Container Manager", "version": "2.0.0", "status": "running"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test Docker CLI connectivity
        docker_status = get_docker_client()  # This returns "CLI_MODE" if successful
        
        return {
            "status": "healthy",
            "docker_status": "connected" if docker_status == "CLI_MODE" else "unknown",
            "active_labs": len(active_labs),
            "max_concurrent": MAX_CONCURRENT_LABS,
            "system_resources": {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage(LAB_STORAGE_PATH).percent
            }
        }
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(status_code=503, detail="Service unavailable")


@app.post("/labs/student", response_model=LabSession)
async def get_or_create_student_lab(request: StudentLabRequest, background_tasks: BackgroundTasks):
    """Get existing lab or create new lab for a student (called on login)"""
    
    # Check if student already has a lab for this course
    existing_lab_id = _get_user_lab(request.user_id, request.course_id)
    
    if existing_lab_id and existing_lab_id in active_labs:
        lab_data = active_labs[existing_lab_id]
        
        # Resume lab if it's paused
        if lab_data['status'] == 'paused':
            await _resume_lab_container(existing_lab_id)
        
        # Update last accessed
        lab_data['last_accessed'] = datetime.utcnow()
        
        logger.info("Returning existing student lab", 
                   user_id=request.user_id, lab_id=existing_lab_id)
        
        return LabSession(**lab_data)
    
    # Create new lab for student
    lab_request = LabCreateRequest(
        user_id=request.user_id,
        course_id=request.course_id,
        lab_type='python',  # Default lab type
        instructor_mode=False
    )
    
    return await create_lab(lab_request, background_tasks)


@app.post("/labs", response_model=LabSession)
async def create_lab(request: LabCreateRequest, background_tasks: BackgroundTasks):
    """Create a new lab container (used by instructors and for new students)"""
    
    # Check concurrent lab limit
    if len(active_labs) >= MAX_CONCURRENT_LABS:
        raise HTTPException(
            status_code=429, 
            detail=f"Maximum concurrent labs ({MAX_CONCURRENT_LABS}) reached"
        )
    
    lab_id = f"lab-{request.user_id}-{request.course_id}-{int(time.time())}"
    
    # Create persistent storage directory
    storage_path = Path(LAB_STORAGE_PATH) / request.user_id / request.course_id
    storage_path.mkdir(parents=True, exist_ok=True)
    
    try:
        # Calculate expiration time
        timeout_minutes = request.timeout_minutes or 60
        expires_at = datetime.utcnow() + timedelta(minutes=timeout_minutes)
        
        # Create lab session record
        lab_session = {
            'lab_id': lab_id,
            'user_id': request.user_id,
            'course_id': request.course_id,
            'lab_type': request.lab_type,
            'container_id': None,
            'port': None,
            'ide_ports': {},  # Will be populated when container starts
            'status': 'building',
            'created_at': datetime.utcnow(),
            'expires_at': expires_at,
            'last_accessed': datetime.utcnow(),
            'instructor_mode': request.instructor_mode,
            'storage_path': str(storage_path),
            'access_url': None,
            'preferred_ide': request.preferred_ide or 'terminal',
            'multi_ide_enabled': request.enable_multi_ide if request.enable_multi_ide is not None else True,
            'available_ides': {}  # Will be populated when container starts
        }
        
        active_labs[lab_id] = lab_session
        user_labs[f"{request.user_id}-{request.course_id}"] = lab_id
        
        # Build and start container in background
        background_tasks.add_task(_build_and_start_lab, lab_id, request)
        background_tasks.add_task(_schedule_cleanup, lab_id, timeout_minutes * 60)
        
        # Track lab creation analytics
        background_tasks.add_task(
            analytics_client.track_lab_activity,
            request.user_id,
            request.course_id,
            "lab_created",
            {
                "lab_id": lab_id,
                "lab_type": request.lab_type,
                "instructor_mode": request.instructor_mode,
                "timeout_minutes": timeout_minutes
            },
            lab_id
        )
        
        # Track lab usage start
        background_tasks.add_task(
            analytics_client.track_lab_usage,
            request.user_id,
            request.course_id,
            lab_id,
            datetime.utcnow(),
            None,  # session_end
            0,     # actions_performed
            0,     # code_executions
            0,     # errors_encountered
            "in_progress"
        )
        
        logger.info("Lab creation initiated", lab_id=lab_id, user_id=request.user_id)
        
        return LabSession(**lab_session)
        
    except Exception as e:
        # Cleanup on error
        if lab_id in active_labs:
            del active_labs[lab_id]
        
        logger.error("Failed to create lab", lab_id=lab_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to create lab: {str(e)}")


@app.get("/labs", response_model=LabListResponse)
async def list_labs(course_id: Optional[str] = Query(None)):
    """List all active lab sessions, optionally filtered by course"""
    
    labs = []
    for lab_data in active_labs.values():
        if course_id is None or lab_data['course_id'] == course_id:
            labs.append(LabSession(**lab_data))
    
    return LabListResponse(
        labs=labs,
        active_count=len(active_labs),
        max_concurrent=MAX_CONCURRENT_LABS
    )


@app.get("/labs/instructor/{course_id}", response_model=InstructorLabManagement)
async def get_instructor_lab_overview(course_id: str):
    """Get lab overview for instructors - all student labs in a course"""
    
    # This would typically fetch from user service, but for now we'll use active labs
    students = []
    
    for lab_data in active_labs.values():
        if lab_data['course_id'] == course_id and not lab_data['instructor_mode']:
            students.append({
                'user_id': lab_data['user_id'],
                'username': lab_data['user_id'],  # Would be fetched from user service
                'lab_status': lab_data['status'],
                'last_accessed': lab_data['last_accessed'],
                'lab_id': lab_data['lab_id']
            })
    
    return InstructorLabManagement(course_id=course_id, students=students)


@app.get("/labs/{lab_id}", response_model=LabSession)
async def get_lab(lab_id: str):
    """Get details of a specific lab session"""
    
    if lab_id not in active_labs:
        raise HTTPException(status_code=404, detail="Lab session not found")
    
    # Update last accessed time
    active_labs[lab_id]['last_accessed'] = datetime.utcnow()
    
    return LabSession(**active_labs[lab_id])


@app.post("/labs/{lab_id}/pause")
async def pause_lab(lab_id: str):
    """Pause a lab container (called on student logout)"""
    
    if lab_id not in active_labs:
        raise HTTPException(status_code=404, detail="Lab session not found")
    
    try:
        await _pause_lab_container(lab_id)
        active_labs[lab_id]['status'] = 'paused'
        active_labs[lab_id]['last_accessed'] = datetime.utcnow()
        
        # Track lab pause analytics
        lab_data = active_labs[lab_id]
        asyncio.create_task(
            analytics_client.track_lab_activity(
                lab_data['user_id'],
                lab_data['course_id'],
                "lab_paused",
                {
                    "lab_id": lab_id,
                    "lab_type": lab_data['lab_type']
                },
                lab_id
            )
        )
        
        logger.info("Lab container paused", lab_id=lab_id)
        
        return {"message": "Lab paused successfully", "lab_id": lab_id}
        
    except Exception as e:
        logger.error("Failed to pause lab container", lab_id=lab_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to pause lab: {str(e)}")


@app.post("/labs/{lab_id}/resume")
async def resume_lab(lab_id: str):
    """Resume a paused lab container (called on student login)"""
    
    if lab_id not in active_labs:
        raise HTTPException(status_code=404, detail="Lab session not found")
    
    try:
        await _resume_lab_container(lab_id)
        active_labs[lab_id]['status'] = 'running'
        active_labs[lab_id]['last_accessed'] = datetime.utcnow()
        
        # Track lab resume analytics
        lab_data = active_labs[lab_id]
        asyncio.create_task(
            analytics_client.track_lab_activity(
                lab_data['user_id'],
                lab_data['course_id'],
                "lab_resumed",
                {
                    "lab_id": lab_id,
                    "lab_type": lab_data['lab_type']
                },
                lab_id
            )
        )
        
        logger.info("Lab container resumed", lab_id=lab_id)
        
        return {"message": "Lab resumed successfully", "lab_id": lab_id}
        
    except Exception as e:
        logger.error("Failed to resume lab container", lab_id=lab_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to resume lab: {str(e)}")


@app.get("/labs/{lab_id}/ides")
async def get_lab_ides(lab_id: str):
    """Get available IDEs for a lab session"""
    
    if lab_id not in active_labs:
        raise HTTPException(status_code=404, detail="Lab session not found")
    
    lab_data = active_labs[lab_id]
    
    return {
        "lab_id": lab_id,
        "preferred_ide": lab_data.get('preferred_ide', 'terminal'),
        "multi_ide_enabled": lab_data.get('multi_ide_enabled', False),
        "available_ides": lab_data.get('available_ides', {}),
        "ide_ports": lab_data.get('ide_ports', {})
    }


@app.post("/labs/{lab_id}/ide/switch")
async def switch_lab_ide(lab_id: str, ide_type: str):
    """Switch the preferred IDE for a lab session"""
    
    if lab_id not in active_labs:
        raise HTTPException(status_code=404, detail="Lab session not found")
    
    lab_data = active_labs[lab_id]
    available_ides = lab_data.get('available_ides', {})
    
    if ide_type not in available_ides:
        raise HTTPException(
            status_code=400, 
            detail=f"IDE '{ide_type}' not available. Available IDEs: {list(available_ides.keys())}"
        )
    
    # Update preferred IDE
    active_labs[lab_id]['preferred_ide'] = ide_type
    active_labs[lab_id]['last_accessed'] = datetime.utcnow()
    
    ide_info = available_ides[ide_type]
    
    logger.info("IDE switched", lab_id=lab_id, new_ide=ide_type)
    
    return {
        "message": f"Switched to {ide_info['name']}",
        "lab_id": lab_id,
        "ide_type": ide_type,
        "ide_url": ide_info['url']
    }


@app.get("/labs/{lab_id}/ide/status")
async def get_lab_ide_status(lab_id: str):
    """Get IDE health status for a lab session"""
    
    if lab_id not in active_labs:
        raise HTTPException(status_code=404, detail="Lab session not found")
    
    lab_data = active_labs[lab_id]
    container_id = lab_data.get('container_id')
    
    if not container_id:
        return {"status": "container_not_started", "ides": {}}
    
    try:
        # Check if container is running using CLI
        import subprocess
        result = subprocess.run(['docker', 'inspect', '--format={{.State.Status}}', container_id],
                              capture_output=True, text=True)
        if result.returncode != 0 or result.stdout.strip() != 'running':
            return {"status": "container_stopped", "ides": {}}
        
        # Check IDE health by testing ports
        ide_status = {}
        available_ides = lab_data.get('available_ides', {})
        ide_ports = lab_data.get('ide_ports', {})
        
        for ide_name, ide_info in available_ides.items():
            port = ide_ports.get(ide_name)
            if port:
                healthy = await _check_ide_health(container_id, ide_name, port)
                ide_status[ide_name] = {
                    "name": ide_info['name'],
                    "port": port,
                    "healthy": healthy,
                    "url": f"http://localhost:{port}"
                }
        
        return {
            "status": "running",
            "ides": ide_status
        }
        
    except Exception as e:
        if "No such container" in str(e):
            return {"status": "container_not_found", "ides": {}}
        logger.error("Error checking IDE status", lab_id=lab_id, error=str(e))
        return {"status": "error", "message": str(e), "ides": {}}


@app.delete("/labs/{lab_id}")
async def stop_lab(lab_id: str):
    """Stop and remove a lab container (instructor action)"""
    
    if lab_id not in active_labs:
        raise HTTPException(status_code=404, detail="Lab session not found")
    
    try:
        lab_data = active_labs[lab_id]
        
        if lab_data['container_id']:
            await _cleanup_lab_container(lab_data['container_id'])
        
        # Track lab completion/stop analytics
        asyncio.create_task(
            analytics_client.track_lab_activity(
                lab_data['user_id'],
                lab_data['course_id'],
                "lab_stopped",
                {
                    "lab_id": lab_id,
                    "lab_type": lab_data['lab_type'],
                    "session_duration_minutes": int((datetime.utcnow() - lab_data['created_at']).total_seconds() / 60)
                },
                lab_id
            )
        )
        
        # Update final lab usage metrics
        asyncio.create_task(
            analytics_client.track_lab_usage(
                lab_data['user_id'],
                lab_data['course_id'],
                lab_id,
                lab_data['created_at'],
                datetime.utcnow(),  # session_end
                completion_status="completed"
            )
        )
        
        # Update student progress
        asyncio.create_task(
            analytics_client.update_student_progress(
                lab_data['user_id'],
                lab_data['course_id'],
                lab_id,
                "lab",
                "completed",
                100.0,  # progress_percentage
                int((datetime.utcnow() - lab_data['created_at']).total_seconds() / 60)
            )
        )
        
        # Remove from tracking
        del active_labs[lab_id]
        
        # Remove user mapping
        user_key = f"{lab_data['user_id']}-{lab_data['course_id']}"
        if user_key in user_labs:
            del user_labs[user_key]
        
        logger.info("Lab container stopped", lab_id=lab_id)
        
        return {"message": "Lab stopped successfully", "lab_id": lab_id}
        
    except Exception as e:
        logger.error("Failed to stop lab container", lab_id=lab_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to stop lab: {str(e)}")


async def _build_and_start_lab(lab_id: str, request: LabCreateRequest):
    """Build Docker image and start lab container"""
    
    try:
        # Update status
        active_labs[lab_id]['status'] = 'building'
        
        # Build custom image
        image_tag = await DynamicImageBuilder.build_lab_image(
            request.lab_type, 
            request.course_id, 
            request.lab_config,
            request.custom_dockerfile
        )
        
        # Update status
        active_labs[lab_id]['status'] = 'starting'
        
        # Start container
        container_info = await _start_lab_container(lab_id, image_tag, request)
        
        # Update lab session with container info
        active_labs[lab_id].update({
            'container_id': container_info['container_id'],
            'port': container_info['port'],
            'ide_ports': container_info['ide_ports'],
            'available_ides': container_info['available_ides'],
            'status': 'running',
            'access_url': f"http://localhost:{container_info['port']}"
        })
        
        logger.info("Lab built and started successfully", lab_id=lab_id)
        
    except Exception as e:
        # Update status to error
        active_labs[lab_id]['status'] = 'error'
        import traceback
        # Print to stdout so it shows in Docker logs
        print(f"TRACEBACK for lab {lab_id}:")
        print(traceback.format_exc())
        logger.error("Failed to build and start lab", lab_id=lab_id, error=str(e))


async def _start_lab_container(lab_id: str, image_tag: str, request: LabCreateRequest) -> Dict:
    """Start a lab container with persistent storage"""
    
    lab_data = active_labs[lab_id]
    storage_path = lab_data['storage_path']
    
    # Find available port and allocate IDE ports
    base_port = _find_available_port()
    ide_ports = _allocate_ide_ports(base_port, request.enable_multi_ide)
    
    # Create port mappings for all IDEs
    port_mappings = {}
    for ide_name, ide_port in ide_ports.items():
        if ide_name == 'terminal':
            port_mappings['8080/tcp'] = ide_port
        elif ide_name == 'vscode':
            port_mappings['8081/tcp'] = ide_port
        elif ide_name == 'jupyter':
            port_mappings['8082/tcp'] = ide_port
        elif ide_name == 'intellij':
            port_mappings['8083/tcp'] = ide_port
    
    # Determine image to use
    if request.enable_multi_ide and request.lab_type == 'python':
        image_tag = image_tag.replace('python-lab', 'python-lab-multi-ide')
    
    # Create container with persistent storage and multi-IDE support using CLI
    container_id = docker_run_container(
        image=f"multi-ide-python:latest",  # Use the new multi-IDE image
        name=f"lab-{lab_id}",
        ports=port_mappings,
        environment={
            'LAB_SESSION_ID': lab_id,
            'USER_ID': request.user_id,
            'COURSE_ID': request.course_id,
            'LAB_TYPE': request.lab_type,
            'LAB_CONFIG': json.dumps(request.lab_config),
            'PREFERRED_IDE': request.preferred_ide,
            'MULTI_IDE_ENABLED': str(request.enable_multi_ide).lower()
        },
        volumes={
            storage_path: {'bind': '/home/labuser/workspace'}
        },
        network='course-creator_course-creator-network',
        memory_limit='2g' if request.enable_multi_ide else '1g',
        cpu_limit=150000 if request.enable_multi_ide else 100000
    )
    
    # Build available IDEs information
    available_ides = {}
    for ide_name, ide_port in ide_ports.items():
        ide_info = IDEInfo(
            name=_get_ide_display_name(ide_name),
            port=ide_port,
            enabled=True,
            healthy=True,  # Will be updated by health checks
            url=f"http://localhost:{ide_port}"
        )
        available_ides[ide_name] = ide_info.dict()
    
    logger.info("Lab container started", 
               container_id=container_id, lab_id=lab_id, port=base_port, 
               ide_ports=ide_ports)
    
    return {
        'container_id': container_id,
        'port': base_port,
        'ide_ports': ide_ports,
        'available_ides': available_ides
    }


async def _pause_lab_container(lab_id: str):
    """Pause a lab container to save resources"""
    
    lab_data = active_labs[lab_id]
    if not lab_data['container_id']:
        return
    
    try:
        import subprocess
        result = subprocess.run(['docker', 'pause', lab_data['container_id']], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            logger.info("Container paused", container_id=lab_data['container_id'])
        else:
            logger.warning("Failed to pause container", 
                          container_id=lab_data['container_id'], error=result.stderr)
    except Exception as e:
        logger.error("Error pausing container", container_id=lab_data['container_id'], error=str(e))


async def _resume_lab_container(lab_id: str):
    """Resume a paused lab container"""
    
    lab_data = active_labs[lab_id]
    if not lab_data['container_id']:
        return
    
    try:
        import subprocess
        result = subprocess.run(['docker', 'unpause', lab_data['container_id']], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            logger.info("Container resumed", container_id=lab_data['container_id'])
        else:
            logger.warning("Failed to resume container", 
                          container_id=lab_data['container_id'], error=result.stderr)
    except Exception as e:
        logger.error("Error resuming container", container_id=lab_data['container_id'], error=str(e))


async def _cleanup_lab_container(container_id: str):
    """Stop and remove a lab container"""
    
    try:
        docker_stop_container(container_id)
    except Exception as e:
        logger.error("Error during container cleanup", container_id=container_id, error=str(e))


def _find_available_port() -> int:
    """Find an available port for the lab container"""
    import socket
    
    # Try ports from 9000 to 9999
    for port in range(9000, 10000):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind(('', port))
                return port
        except OSError:
            continue
    
    raise Exception("No available ports found")

async def _check_ide_health(container_id: str, ide_name: str, port: int) -> bool:
    """Check if an IDE service is healthy within a container"""
    import socket
    
    try:
        # Simple port check for now
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(2)
            result = sock.connect_ex(('localhost', port))
            return result == 0
    except Exception:
        return False

def _get_ide_display_name(ide_name: str) -> str:
    """Get human-readable IDE name"""
    ide_names = {
        'terminal': 'Terminal (xterm.js)',
        'vscode': 'VSCode Server',
        'jupyter': 'JupyterLab',
        'intellij': 'IntelliJ IDEA'
    }
    return ide_names.get(ide_name, ide_name.title())

def _allocate_ide_ports(base_port: int, enable_multi_ide: bool = True) -> Dict[str, int]:
    """Allocate ports for different IDEs"""
    import socket
    
    ide_ports = {}
    
    if enable_multi_ide:
        # Multi-IDE setup - each IDE gets its own port
        ide_configs = {
            'terminal': base_port,      # Main web interface with terminal
            'vscode': base_port + 1,    # VSCode Server
            'jupyter': base_port + 2,   # JupyterLab
            'intellij': base_port + 3   # IntelliJ IDEA (when available)
        }
        
        for ide_name, port in ide_configs.items():
            # Verify port is available
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.bind(('', port))
                    ide_ports[ide_name] = port
            except OSError:
                # Port not available, find alternative
                alt_port = _find_available_port()
                ide_ports[ide_name] = alt_port
                logger.warning(f"Port {port} not available for {ide_name}, using {alt_port}")
    else:
        # Single IDE setup - only terminal
        ide_ports['terminal'] = base_port
    
    return ide_ports


def _get_user_lab(user_id: str, course_id: str) -> Optional[str]:
    """Get existing lab ID for user and course"""
    return user_labs.get(f"{user_id}-{course_id}")


async def _schedule_cleanup(lab_id: str, timeout_seconds: int):
    """Schedule automatic cleanup of expired lab session"""
    await asyncio.sleep(timeout_seconds)
    
    if lab_id in active_labs:
        lab_data = active_labs[lab_id]
        
        # Check if lab has expired and is not accessed recently
        if datetime.utcnow() > lab_data['expires_at']:
            try:
                if lab_data['container_id']:
                    await _cleanup_lab_container(lab_data['container_id'])
                
                del active_labs[lab_id]
                
                # Remove user mapping
                user_key = f"{lab_data['user_id']}-{lab_data['course_id']}"
                if user_key in user_labs:
                    del user_labs[user_key]
                
                logger.info("Lab session expired and cleaned up", lab_id=lab_id)
            except Exception as e:
                logger.error("Failed to cleanup expired lab", lab_id=lab_id, error=str(e))

# ==================== AI ASSISTANT HELPER FUNCTIONS ====================

async def _handle_ai_ide_request(request: AIAssistantRequest, ide_port: int, lab_data: Dict) -> Dict:
    """Handle AI assistant requests for different IDE types and actions"""
    
    result = {"success": False, "data": None, "error": None}
    
    try:
        if request.ide_type == "vscode":
            result = await _handle_vscode_ai_request(request, ide_port, lab_data)
        elif request.ide_type == "jupyter":
            result = await _handle_jupyter_ai_request(request, ide_port, lab_data)
        elif request.ide_type == "terminal":
            result = await _handle_terminal_ai_request(request, ide_port, lab_data)
        else:
            result["error"] = f"Unsupported IDE type: {request.ide_type}"
            
    except Exception as e:
        result["error"] = str(e)
        logger.error("AI IDE request error", 
                    ide_type=request.ide_type, 
                    action=request.action, 
                    error=str(e))
    
    return result

async def _handle_vscode_ai_request(request: AIAssistantRequest, ide_port: int, lab_data: Dict) -> Dict:
    """Handle AI requests for VSCode Server"""
    
    action = request.action
    payload = request.payload
    
    # VSCode Server API interactions
    base_url = f"http://localhost:{ide_port}"
    
    async with httpx.AsyncClient() as client:
        try:
            if action == "read_file":
                file_path = payload.get("file_path")
                if not file_path:
                    return {"success": False, "error": "file_path required"}
                
                # Use container exec to read file from workspace
                container_name = f"lab-{request.lab_id}"
                result = await _exec_container_command(
                    container_name,
                    ["cat", f"/home/labuser/workspace/{file_path}"]
                )
                
                return {
                    "success": result["success"],
                    "data": {"content": result.get("output", ""), "file_path": file_path},
                    "error": result.get("error")
                }
                
            elif action == "write_file":
                file_path = payload.get("file_path")
                content = payload.get("content", "")
                
                if not file_path:
                    return {"success": False, "error": "file_path required"}
                
                # Use container exec to write file
                container_name = f"lab-{request.lab_id}"
                
                # Create file with content
                import tempfile
                import base64
                encoded_content = base64.b64encode(content.encode()).decode()
                
                result = await _exec_container_command(
                    container_name,
                    ["sh", "-c", f"echo '{encoded_content}' | base64 -d > /home/labuser/workspace/{file_path} && chown labuser:labuser /home/labuser/workspace/{file_path}"]
                )
                
                return {
                    "success": result["success"],
                    "data": {"file_path": file_path, "bytes_written": len(content)},
                    "error": result.get("error")
                }
                
            elif action == "get_workspace":
                # List workspace files
                container_name = f"lab-{request.lab_id}"
                result = await _exec_container_command(
                    container_name,
                    ["find", "/home/labuser/workspace", "-type", "f", "-name", "*.py", "-o", "-name", "*.js", "-o", "-name", "*.html", "-o", "-name", "*.css", "-o", "-name", "*.json", "-o", "-name", "*.md", "-o", "-name", "*.txt"]
                )
                
                if result["success"]:
                    files = [f.replace("/home/labuser/workspace/", "") for f in result["output"].strip().split("\n") if f.strip()]
                    return {"success": True, "data": {"files": files}}
                else:
                    return {"success": False, "error": result.get("error")}
                    
            else:
                return {"success": False, "error": f"Unsupported VSCode action: {action}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

async def _handle_jupyter_ai_request(request: AIAssistantRequest, ide_port: int, lab_data: Dict) -> Dict:
    """Handle AI requests for Jupyter/JupyterLab"""
    
    action = request.action
    payload = request.payload
    
    base_url = f"http://localhost:{ide_port}"
    
    async with httpx.AsyncClient() as client:
        try:
            if action == "execute_code":
                code = payload.get("code", "")
                
                # For now, execute code directly in container
                container_name = f"lab-{request.lab_id}"
                
                # Create temporary Python script and execute
                import base64
                encoded_code = base64.b64encode(code.encode()).decode()
                
                result = await _exec_container_command(
                    container_name,
                    ["sh", "-c", f"cd /home/labuser/workspace && echo '{encoded_code}' | base64 -d | python3"]
                )
                
                return {
                    "success": result["success"],
                    "data": {
                        "output": result.get("output", ""),
                        "execution_count": 1
                    },
                    "error": result.get("error")
                }
                
            elif action == "read_file":
                file_path = payload.get("file_path")
                container_name = f"lab-{request.lab_id}"
                
                result = await _exec_container_command(
                    container_name,
                    ["cat", f"/home/labuser/workspace/{file_path}"]
                )
                
                return {
                    "success": result["success"],
                    "data": {"content": result.get("output", ""), "file_path": file_path},
                    "error": result.get("error")
                }
                
            elif action == "get_workspace":
                container_name = f"lab-{request.lab_id}"
                result = await _exec_container_command(
                    container_name,
                    ["find", "/home/labuser/workspace", "-name", "*.ipynb", "-o", "-name", "*.py"]
                )
                
                if result["success"]:
                    files = [f.replace("/home/labuser/workspace/", "") for f in result["output"].strip().split("\n") if f.strip()]
                    return {"success": True, "data": {"notebooks": files}}
                else:
                    return {"success": False, "error": result.get("error")}
                    
            else:
                return {"success": False, "error": f"Unsupported Jupyter action: {action}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

async def _handle_terminal_ai_request(request: AIAssistantRequest, ide_port: int, lab_data: Dict) -> Dict:
    """Handle AI requests for terminal/shell commands"""
    
    action = request.action
    payload = request.payload
    
    try:
        if action == "terminal_command":
            command = payload.get("command", "")
            
            if not command:
                return {"success": False, "error": "command required"}
            
            container_name = f"lab-{request.lab_id}"
            
            # Execute command in container
            result = await _exec_container_command(
                container_name,
                ["sh", "-c", f"cd /home/labuser/workspace && {command}"]
            )
            
            return {
                "success": result["success"],
                "data": {
                    "output": result.get("output", ""),
                    "command": command
                },
                "error": result.get("error")
            }
            
        elif action == "get_workspace":
            container_name = f"lab-{request.lab_id}"
            result = await _exec_container_command(
                container_name,
                ["ls", "-la", "/home/labuser/workspace"]
            )
            
            return {
                "success": result["success"],
                "data": {"listing": result.get("output", "")},
                "error": result.get("error")
            }
            
        else:
            return {"success": False, "error": f"Unsupported terminal action: {action}"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

async def _exec_container_command(container_name: str, command: List[str]) -> Dict:
    """Execute command in container using Docker CLI"""
    
    try:
        import subprocess
        
        docker_cmd = ["docker", "exec", container_name] + command
        
        result = subprocess.run(
            docker_cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr if result.returncode != 0 else None
        }
        
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timeout"}
    except Exception as e:
        return {"success": False, "error": str(e)}

async def _get_workspace_structure(lab_data: Dict) -> Dict:
    """Get the file structure of the lab workspace"""
    
    container_name = f"lab-{lab_data['lab_id']}"
    
    try:
        # Get directory tree
        result = await _exec_container_command(
            container_name,
            ["find", "/home/labuser/workspace", "-type", "f", "-o", "-type", "d"]
        )
        
        if result["success"]:
            paths = result["output"].strip().split("\n")
            
            # Build file tree structure
            files = []
            directories = []
            
            for path in paths:
                if path.strip():
                    relative_path = path.replace("/home/labuser/workspace/", "").replace("/home/labuser/workspace", "")
                    if relative_path:  # Skip empty root
                        if path.endswith("/") or "." not in relative_path.split("/")[-1]:
                            directories.append(relative_path)
                        else:
                            files.append(relative_path)
            
            return {
                "files": sorted(files),
                "directories": sorted(directories),
                "workspace_path": "/home/labuser/workspace"
            }
        else:
            return {"error": result.get("error", "Failed to get workspace structure")}
            
    except Exception as e:
        return {"error": str(e)}

# ==================== AI ASSISTANT PROXY ENDPOINTS ====================

@app.post("/ai-assistant/proxy", response_model=AIAssistantResponse)
async def ai_assistant_proxy(request: AIAssistantRequest):
    """Proxy AI assistant requests to student lab environments"""
    
    if request.lab_id not in active_labs:
        raise HTTPException(status_code=404, detail="Lab session not found")
    
    lab_data = active_labs[request.lab_id]
    
    if lab_data['status'] != 'running':
        raise HTTPException(status_code=400, detail=f"Lab is not running (status: {lab_data['status']})")
    
    # Get the appropriate IDE port
    if request.ide_type not in lab_data['ide_ports']:
        raise HTTPException(status_code=400, detail=f"IDE type '{request.ide_type}' not available in this lab")
    
    ide_port = lab_data['ide_ports'][request.ide_type]
    
    try:
        # Route request based on IDE type and action
        result = await _handle_ai_ide_request(request, ide_port, lab_data)
        
        # Log AI assistant activity
        asyncio.create_task(
            analytics_client.track_lab_activity(
                lab_data['user_id'],
                lab_data['course_id'],
                "ai_assistant_action",
                {
                    "lab_id": request.lab_id,
                    "ide_type": request.ide_type,
                    "action": request.action,
                    "ai_session_id": request.ai_session_id,
                    "success": result.get('success', False)
                },
                request.lab_id
            )
        )
        
        return AIAssistantResponse(
            success=result.get('success', False),
            data=result.get('data'),
            error=result.get('error'),
            ide_type=request.ide_type,
            action=request.action
        )
        
    except Exception as e:
        logger.error("AI assistant proxy error", 
                    lab_id=request.lab_id, 
                    ide_type=request.ide_type, 
                    action=request.action, 
                    error=str(e))
        return AIAssistantResponse(
            success=False,
            error=str(e),
            ide_type=request.ide_type,
            action=request.action
        )

@app.get("/ai-assistant/labs/{lab_id}/workspace")
async def get_lab_workspace_info(lab_id: str):
    """Get workspace information for AI assistant"""
    
    if lab_id not in active_labs:
        raise HTTPException(status_code=404, detail="Lab session not found")
    
    lab_data = active_labs[lab_id]
    
    if lab_data['status'] != 'running':
        raise HTTPException(status_code=400, detail=f"Lab is not running (status: {lab_data['status']})")
    
    try:
        # Get workspace file structure
        workspace_info = await _get_workspace_structure(lab_data)
        
        return {
            "lab_id": lab_id,
            "user_id": lab_data['user_id'],
            "course_id": lab_data['course_id'],
            "workspace_path": "/home/labuser/workspace",
            "available_ides": list(lab_data['ide_ports'].keys()),
            "ide_ports": lab_data['ide_ports'],
            "workspace_structure": workspace_info,
            "status": lab_data['status']
        }
        
    except Exception as e:
        logger.error("Failed to get workspace info", lab_id=lab_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get workspace info: {str(e)}")

@app.post("/ai-assistant/labs/{lab_id}/tunnel/{ide_type}")
async def create_ai_tunnel(lab_id: str, ide_type: str, request: Request):
    """Create a direct tunnel for AI assistant to IDE"""
    
    if lab_id not in active_labs:
        raise HTTPException(status_code=404, detail="Lab session not found")
    
    lab_data = active_labs[lab_id]
    
    if lab_data['status'] != 'running':
        raise HTTPException(status_code=400, detail=f"Lab is not running (status: {lab_data['status']})")
    
    if ide_type not in lab_data['ide_ports']:
        raise HTTPException(status_code=400, detail=f"IDE type '{ide_type}' not available")
    
    ide_port = lab_data['ide_ports'][ide_type]
    
    try:
        # Forward the request to the appropriate IDE
        async with httpx.AsyncClient() as client:
            url = f"http://localhost:{ide_port}{request.url.path.replace(f'/ai-assistant/labs/{lab_id}/tunnel/{ide_type}', '')}"
            
            # Forward query parameters
            if request.url.query:
                url += f"?{request.url.query}"
            
            # Get request body if present
            body = await request.body()
            
            # Forward headers (excluding host)
            headers = dict(request.headers)
            headers.pop('host', None)
            
            # Make the proxied request
            response = await client.request(
                method=request.method,
                url=url,
                headers=headers,
                content=body,
                timeout=30.0
            )
            
            # Return the response
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
            
    except Exception as e:
        logger.error("AI tunnel error", lab_id=lab_id, ide_type=ide_type, error=str(e))
        raise HTTPException(status_code=500, detail=f"Tunnel error: {str(e)}")

# ==================== STUDENT FILE DOWNLOAD ENDPOINTS ====================

@app.get("/labs/{lab_id}/files")
async def list_workspace_files(lab_id: str):
    """List all files in student workspace for download"""
    
    if lab_id not in active_labs:
        raise HTTPException(status_code=404, detail="Lab session not found")
    
    lab_data = active_labs[lab_id]
    
    if lab_data['status'] != 'running':
        raise HTTPException(status_code=400, detail=f"Lab is not running (status: {lab_data['status']})")
    
    try:
        container_name = f"lab-{lab_id}"
        
        # Get all files recursively
        result = await _exec_container_command(
            container_name,
            ["find", "/home/labuser/workspace", "-type", "f", "-exec", "ls", "-la", "{}", ";"]
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail="Failed to list workspace files")
        
        # Parse the file list
        files = []
        for line in result["output"].strip().split('\n'):
            if line and '/home/labuser/workspace/' in line:
                parts = line.split()
                if len(parts) >= 9:
                    file_path = ' '.join(parts[8:])  # Full path
                    relative_path = file_path.replace('/home/labuser/workspace/', '')
                    if relative_path and relative_path != '/home/labuser/workspace':
                        size = parts[4]
                        modified = ' '.join(parts[5:8])
                        files.append({
                            "name": relative_path,
                            "size": size,
                            "modified": modified,
                            "download_url": f"/labs/{lab_id}/download/{relative_path}"
                        })
        
        return {
            "lab_id": lab_id,
            "files": files,
            "total_files": len(files)
        }
        
    except Exception as e:
        logger.error("Failed to list workspace files", lab_id=lab_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")

@app.get("/labs/{lab_id}/download/{file_path:path}")
async def download_file(lab_id: str, file_path: str):
    """Download individual file from student workspace"""
    
    if lab_id not in active_labs:
        raise HTTPException(status_code=404, detail="Lab session not found")
    
    lab_data = active_labs[lab_id]
    
    if lab_data['status'] != 'running':
        raise HTTPException(status_code=400, detail=f"Lab is not running (status: {lab_data['status']})")
    
    # Security check - prevent path traversal
    if '..' in file_path or file_path.startswith('/'):
        raise HTTPException(status_code=400, detail="Invalid file path")
    
    try:
        container_name = f"lab-{lab_id}"
        
        # Check if file exists and get content
        result = await _exec_container_command(
            container_name,
            ["cat", f"/home/labuser/workspace/{file_path}"]
        )
        
        if not result["success"]:
            if "No such file" in result.get("error", ""):
                raise HTTPException(status_code=404, detail="File not found")
            else:
                raise HTTPException(status_code=500, detail="Failed to read file")
        
        # Get file info for proper headers
        stat_result = await _exec_container_command(
            container_name,
            ["stat", "-c", "%s", f"/home/labuser/workspace/{file_path}"]
        )
        
        file_size = stat_result["output"].strip() if stat_result["success"] else str(len(result["output"]))
        
        # Determine content type based on file extension
        content_type = "text/plain"
        if file_path.endswith('.py'):
            content_type = "text/x-python"
        elif file_path.endswith('.js'):
            content_type = "application/javascript"
        elif file_path.endswith('.html'):
            content_type = "text/html"
        elif file_path.endswith('.css'):
            content_type = "text/css"
        elif file_path.endswith('.json'):
            content_type = "application/json"
        elif file_path.endswith('.md'):
            content_type = "text/markdown"
        
        # Create response with proper headers
        headers = {
            "Content-Disposition": f"attachment; filename=\"{Path(file_path).name}\"",
            "Content-Length": file_size,
            "Content-Type": content_type
        }
        
        return Response(
            content=result["output"],
            headers=headers,
            media_type=content_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to download file", lab_id=lab_id, file_path=file_path, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to download file: {str(e)}")

@app.get("/labs/{lab_id}/download-workspace")
async def download_workspace_zip(lab_id: str):
    """Download entire workspace as ZIP file"""
    
    if lab_id not in active_labs:
        raise HTTPException(status_code=404, detail="Lab session not found")
    
    lab_data = active_labs[lab_id]
    
    if lab_data['status'] != 'running':
        raise HTTPException(status_code=400, detail=f"Lab is not running (status: {lab_data['status']})")
    
    try:
        container_name = f"lab-{lab_id}"
        
        # Get all files in workspace
        result = await _exec_container_command(
            container_name,
            ["find", "/home/labuser/workspace", "-type", "f", "-not", "-path", "*/.*"]
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail="Failed to list workspace files")
        
        file_paths = [f.strip() for f in result["output"].strip().split('\n') if f.strip()]
        
        if not file_paths:
            raise HTTPException(status_code=404, detail="No files found in workspace")
        
        # Create ZIP file in memory
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for file_path in file_paths:
                if file_path == '/home/labuser/workspace':
                    continue
                    
                # Get file content
                file_result = await _exec_container_command(
                    container_name,
                    ["cat", file_path]
                )
                
                if file_result["success"]:
                    # Get relative path for ZIP
                    relative_path = file_path.replace('/home/labuser/workspace/', '')
                    if relative_path:
                        zip_file.writestr(relative_path, file_result["output"])
        
        zip_buffer.seek(0)
        
        # Generate filename with timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"workspace_{lab_data['user_id']}_{timestamp}.zip"
        
        headers = {
            "Content-Disposition": f"attachment; filename=\"{filename}\"",
            "Content-Type": "application/zip"
        }
        
        return StreamingResponse(
            io.BytesIO(zip_buffer.read()),
            headers=headers,
            media_type="application/zip"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create workspace ZIP", lab_id=lab_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to create ZIP file: {str(e)}")


@app.on_event("startup")
async def startup_event():
    """Initialize the lab manager service"""
    logger.info("Enhanced Lab Container Manager starting up")
    
    # Ensure storage directory exists
    Path(LAB_STORAGE_PATH).mkdir(parents=True, exist_ok=True)
    
    # Skip Docker cleanup during startup to avoid connection issues
    # Docker cleanup will happen when first lab is created
    logger.info("Startup complete - Docker cleanup deferred until first API call")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown"""
    logger.info("Enhanced Lab Container Manager shutting down")
    
    # Stop all active lab containers
    for lab_id, lab_data in active_labs.items():
        try:
            if lab_data['container_id']:
                await _cleanup_lab_container(lab_data['container_id'])
        except Exception as e:
            logger.error("Error cleaning up lab during shutdown", 
                        lab_id=lab_id, error=str(e))
    
    active_labs.clear()
    user_labs.clear()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)