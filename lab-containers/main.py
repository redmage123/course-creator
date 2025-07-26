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
import docker
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

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
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

# Docker client
docker_client = docker.from_env()

# Configuration from environment
MAX_CONCURRENT_LABS = int(os.getenv('MAX_CONCURRENT_LABS', '50'))
LAB_SESSION_TIMEOUT = int(os.getenv('LAB_SESSION_TIMEOUT', '3600'))  # 1 hour
LAB_STORAGE_PATH = os.getenv('LAB_STORAGE_PATH', '/app/lab-storage')
LAB_IMAGE_REGISTRY = os.getenv('LAB_IMAGE_REGISTRY', 'course-creator/labs')

# In-memory storage for active lab sessions
active_labs: Dict[str, Dict] = {}  # lab_id -> lab_info
user_labs: Dict[str, str] = {}     # user_id -> lab_id mapping


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
                image, build_logs = docker_client.images.build(
                    path=str(build_path),
                    tag=image_tag,
                    rm=True,
                    forcerm=True
                )
                
                logger.info("Lab image built successfully", image_tag=image_tag)
                return image_tag
                
            except docker.errors.BuildError as e:
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
        docker_client.ping()
        return {
            "status": "healthy",
            "docker_status": "connected",
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
        # Check if container is running
        container = docker_client.containers.get(container_id)
        if container.status != 'running':
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
        
    except docker.errors.NotFound:
        return {"status": "container_not_found", "ides": {}}
    except Exception as e:
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
    
    # Create container with persistent storage and multi-IDE support
    container = docker_client.containers.run(
        image=image_tag,
        detach=True,
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
            storage_path: {'bind': '/home/labuser/workspace', 'mode': 'rw'}
        },
        # Security constraints (increased memory for multi-IDE)
        mem_limit='2g' if request.enable_multi_ide else '1g',
        cpu_quota=150000 if request.enable_multi_ide else 100000,  # 150% of one CPU for multi-IDE
        network_mode='bridge',
        cap_drop=['ALL'],
        cap_add=['CHOWN', 'DAC_OVERRIDE', 'FOWNER', 'SETGID', 'SETUID'],
        security_opt=['no-new-privileges:true'],
        restart_policy={'Name': 'unless-stopped'}
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
               container_id=container.id, lab_id=lab_id, port=base_port, 
               ide_ports=ide_ports)
    
    return {
        'container_id': container.id,
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
        container = docker_client.containers.get(lab_data['container_id'])
        container.pause()
        logger.info("Container paused", container_id=lab_data['container_id'])
    except docker.errors.NotFound:
        logger.warning("Container not found during pause", container_id=lab_data['container_id'])
    except Exception as e:
        logger.error("Error pausing container", container_id=lab_data['container_id'], error=str(e))


async def _resume_lab_container(lab_id: str):
    """Resume a paused lab container"""
    
    lab_data = active_labs[lab_id]
    if not lab_data['container_id']:
        return
    
    try:
        container = docker_client.containers.get(lab_data['container_id'])
        container.unpause()
        logger.info("Container resumed", container_id=lab_data['container_id'])
    except docker.errors.NotFound:
        logger.warning("Container not found during resume", container_id=lab_data['container_id'])
    except Exception as e:
        logger.error("Error resuming container", container_id=lab_data['container_id'], error=str(e))


async def _cleanup_lab_container(container_id: str):
    """Stop and remove a lab container"""
    
    try:
        container = docker_client.containers.get(container_id)
        container.stop(timeout=10)
        container.remove()
        logger.info("Container cleaned up", container_id=container_id)
    except docker.errors.NotFound:
        logger.warning("Container not found during cleanup", container_id=container_id)
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


@app.on_event("startup")
async def startup_event():
    """Initialize the lab manager service"""
    logger.info("Enhanced Lab Container Manager starting up")
    
    # Ensure storage directory exists
    Path(LAB_STORAGE_PATH).mkdir(parents=True, exist_ok=True)
    
    # Clean up any existing lab containers on startup
    try:
        containers = docker_client.containers.list(filters={'name': 'lab-'})
        for container in containers:
            container.stop(timeout=5)
            container.remove()
        logger.info(f"Cleaned up {len(containers)} existing lab containers")
    except Exception as e:
        logger.warning("Error during startup cleanup", error=str(e))


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