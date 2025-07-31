"""
Lab lifecycle management service.
Handles creation, management, and cleanup of lab environments.
"""

import asyncio
import json
import os
import shutil
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from fastapi import HTTPException

from ..models.lab_models import (
    LabEnvironment, LabConfig, LabStatus, IDEType, 
    LabRequest, StudentLabRequest, LabResponse
)
from .docker_service import DockerService


class LabLifecycleService:
    """Service for managing lab environment lifecycle."""
    
    def __init__(self, docker_service: DockerService, logger):
        self.docker_service = docker_service
        self.logger = logger
        self.active_labs: Dict[str, LabEnvironment] = {}
        self.user_labs: Dict[str, str] = {}  # user_id -> lab_id mapping
        self.base_storage_path = Path("/tmp/lab-storage")
        self.base_storage_path.mkdir(exist_ok=True)
    
    async def create_student_lab(self, 
                               student_id: str, 
                               request: StudentLabRequest) -> LabResponse:
        """Create or retrieve student lab environment."""
        try:
            # Check if student already has a lab for this course
            existing_lab_id = self._get_student_lab(student_id, request.course_id)
            if existing_lab_id:
                lab = self.active_labs.get(existing_lab_id)
                if lab and lab.status == LabStatus.RUNNING:
                    return LabResponse(
                        success=True,
                        message="Existing lab retrieved",
                        lab_id=lab.id,
                        urls=lab.ide_urls,
                        status=lab.status
                    )
            
            # Create new lab
            lab_config = request.config or LabConfig()
            lab_env = await self._create_lab_environment(
                student_id, request.course_id, lab_config
            )
            
            # Start the container
            await self._start_lab_container(lab_env)
            
            # Register lab
            self.active_labs[lab_env.id] = lab_env
            self.user_labs[f"{student_id}:{request.course_id}"] = lab_env.id
            
            return LabResponse(
                success=True,
                message="Lab created successfully",
                lab_id=lab_env.id,
                urls=lab_env.ide_urls,
                status=lab_env.status
            )
            
        except Exception as e:
            self.logger.error(f"Failed to create lab for student {student_id}: {e}")
            return LabResponse(
                success=False,
                message=f"Lab creation failed: {str(e)}"
            )
    
    async def pause_lab(self, lab_id: str) -> LabResponse:
        """Pause a lab environment."""
        try:
            lab = self.active_labs.get(lab_id)
            if not lab:
                return LabResponse(
                    success=False,
                    message="Lab not found"
                )
            
            # Stop the container
            success = self.docker_service.stop_container(lab.container_name)
            if success:
                lab.status = LabStatus.STOPPED
                lab.last_accessed = datetime.utcnow()
                
                return LabResponse(
                    success=True,
                    message="Lab paused successfully",
                    lab_id=lab_id,
                    status=lab.status
                )
            else:
                return LabResponse(
                    success=False,
                    message="Failed to pause lab"
                )
                
        except Exception as e:
            self.logger.error(f"Failed to pause lab {lab_id}: {e}")
            return LabResponse(
                success=False,
                message=f"Pause failed: {str(e)}"
            )
    
    async def resume_lab(self, lab_id: str) -> LabResponse:
        """Resume a paused lab environment."""
        try:
            lab = self.active_labs.get(lab_id)
            if not lab:
                return LabResponse(
                    success=False,
                    message="Lab not found"
                )
            
            # Start the container
            await self._start_lab_container(lab)
            
            return LabResponse(
                success=True,
                message="Lab resumed successfully",
                lab_id=lab_id,
                urls=lab.ide_urls,
                status=lab.status
            )
            
        except Exception as e:
            self.logger.error(f"Failed to resume lab {lab_id}: {e}")
            return LabResponse(
                success=False,
                message=f"Resume failed: {str(e)}"
            )
    
    async def delete_lab(self, lab_id: str) -> LabResponse:
        """Delete a lab environment."""
        try:
            lab = self.active_labs.get(lab_id)
            if not lab:
                return LabResponse(
                    success=False,
                    message="Lab not found"
                )
            
            # Stop and remove container
            self.docker_service.stop_container(lab.container_name)
            self.docker_service.remove_container(lab.container_name, force=True)
            
            # Clean up storage
            if lab.persistent_storage_path:
                storage_path = Path(lab.persistent_storage_path)
                if storage_path.exists():
                    shutil.rmtree(storage_path)
            
            # Remove from tracking
            del self.active_labs[lab_id]
            user_key = f"{lab.student_id}:{lab.course_id}"
            if user_key in self.user_labs:
                del self.user_labs[user_key]
            
            return LabResponse(
                success=True,
                message="Lab deleted successfully",
                lab_id=lab_id
            )
            
        except Exception as e:
            self.logger.error(f"Failed to delete lab {lab_id}: {e}")
            return LabResponse(
                success=False,
                message=f"Deletion failed: {str(e)}"
            )
    
    def get_lab_status(self, lab_id: str) -> Optional[LabEnvironment]:
        """Get lab environment status."""
        lab = self.active_labs.get(lab_id)
        if lab:
            # Update status from container
            container_status = self.docker_service.get_container_status(lab.container_name)
            if container_status:
                lab.status = self._map_container_status(container_status)
        return lab
    
    def list_student_labs(self, student_id: str) -> List[LabEnvironment]:
        """List all labs for a student."""
        return [
            lab for lab in self.active_labs.values()
            if lab.student_id == student_id
        ]
    
    def list_course_labs(self, course_id: str) -> List[LabEnvironment]:
        """List all labs for a course."""
        return [
            lab for lab in self.active_labs.values()
            if lab.course_id == course_id
        ]
    
    async def cleanup_idle_labs(self, max_idle_hours: int = 24) -> int:
        """Clean up labs that have been idle for too long."""
        cleaned = 0
        cutoff_time = datetime.utcnow() - timedelta(hours=max_idle_hours)
        
        labs_to_remove = []
        for lab_id, lab in self.active_labs.items():
            if (lab.last_accessed and lab.last_accessed < cutoff_time) or \
               (not lab.last_accessed and lab.created_at < cutoff_time):
                labs_to_remove.append(lab_id)
        
        for lab_id in labs_to_remove:
            result = await self.delete_lab(lab_id)
            if result.success:
                cleaned += 1
        
        self.logger.info(f"Cleaned up {cleaned} idle labs")
        return cleaned
    
    async def _create_lab_environment(self, 
                                    student_id: str,
                                    course_id: str,
                                    config: LabConfig) -> LabEnvironment:
        """Create a new lab environment."""
        from uuid import uuid4
        
        lab_id = str(uuid4())
        container_name = f"lab-{student_id}-{course_id}-{lab_id[:8]}"
        
        # Create persistent storage directory
        storage_path = self.base_storage_path / student_id / course_id
        storage_path.mkdir(parents=True, exist_ok=True)
        
        # Determine ports based on IDE configuration
        ports = self._allocate_ports(config)
        
        lab_env = LabEnvironment(
            id=lab_id,
            student_id=student_id,
            course_id=course_id,
            container_name=container_name,
            status=LabStatus.CREATING,
            created_at=datetime.utcnow(),
            config=config,
            ports=ports,
            persistent_storage_path=str(storage_path)
        )
        
        return lab_env
    
    async def _start_lab_container(self, lab: LabEnvironment):
        """Start the lab container."""
        try:
            lab.status = LabStatus.STARTING
            
            # Select appropriate image
            image_name = self._get_lab_image(lab.config)
            
            # Prepare volumes
            volumes = {
                lab.persistent_storage_path: {"bind": "/home/student", "mode": "rw"}
            }
            
            # Prepare environment
            environment = {
                "STUDENT_ID": lab.student_id,
                "COURSE_ID": lab.course_id,
                "LAB_ID": lab.id,
                **lab.config.environment_vars
            }
            
            # Create container
            container_id = self.docker_service.create_container(
                image_name=image_name,
                container_name=lab.container_name,
                ports=lab.ports,
                volumes=volumes,
                environment=environment,
                cpu_limit=lab.config.cpu_limit,
                memory_limit=lab.config.memory_limit
            )
            
            lab.container_id = container_id
            lab.status = LabStatus.RUNNING
            lab.last_accessed = datetime.utcnow()
            
            # Generate IDE URLs
            lab.ide_urls = self._generate_ide_urls(lab)
            
        except Exception as e:
            lab.status = LabStatus.ERROR
            self.logger.error(f"Failed to start container for lab {lab.id}: {e}")
            raise
    
    def _get_student_lab(self, student_id: str, course_id: str) -> Optional[str]:
        """Get existing lab ID for student and course."""
        return self.user_labs.get(f"{student_id}:{course_id}")
    
    def _allocate_ports(self, config: LabConfig) -> Dict[str, int]:
        """Allocate ports for lab services."""
        base_port = 8080
        ports = {}
        
        if config.ide_type == IDEType.VSCODE or config.enable_multi_ide:
            ports["8080/tcp"] = self._find_available_port(base_port)
        
        if config.ide_type == IDEType.JUPYTER or config.enable_multi_ide:
            ports["8888/tcp"] = self._find_available_port(base_port + 1)
        
        if config.enable_multi_ide:
            # Additional ports for multi-IDE setup
            ports["8081/tcp"] = self._find_available_port(base_port + 10)  # IntelliJ
            ports["8082/tcp"] = self._find_available_port(base_port + 20)  # Terminal
        
        return ports
    
    def _find_available_port(self, start_port: int) -> int:
        """Find an available port."""
        return self.docker_service._find_available_port(start_port)
    
    def _get_lab_image(self, config: LabConfig) -> str:
        """Get appropriate Docker image for lab configuration."""
        if config.enable_multi_ide:
            return f"lab-{config.language}-multi-ide:latest"
        else:
            return f"lab-{config.language}-{config.ide_type.value}:latest"
    
    def _generate_ide_urls(self, lab: LabEnvironment) -> Dict[str, str]:
        """Generate URLs for IDE access."""
        urls = {}
        
        for port_spec, external_port in lab.ports.items():
            internal_port = port_spec.split('/')[0]
            
            if internal_port == "8080":
                urls["vscode"] = f"http://localhost:{external_port}"
            elif internal_port == "8888":
                urls["jupyter"] = f"http://localhost:{external_port}"
            elif internal_port == "8081":
                urls["intellij"] = f"http://localhost:{external_port}"
            elif internal_port == "8082":
                urls["terminal"] = f"http://localhost:{external_port}"
        
        return urls
    
    def _map_container_status(self, container_status: str) -> LabStatus:
        """Map Docker container status to lab status."""
        status_map = {
            "running": LabStatus.RUNNING,
            "exited": LabStatus.STOPPED,
            "paused": LabStatus.PAUSED,
            "restarting": LabStatus.STARTING,
            "created": LabStatus.CREATING
        }
        return status_map.get(container_status.lower(), LabStatus.ERROR)