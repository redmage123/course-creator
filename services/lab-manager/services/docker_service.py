"""
Docker container management service for lab environments.
Handles container lifecycle, image building, and resource management.
"""

import asyncio
import json
import logging
import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import docker
from docker.errors import APIError, NotFound

from models.lab_models import LabConfig, ContainerSpec


class DockerService:
    """Service for managing Docker containers and images for lab environments."""
    
    def __init__(self, logger: logging.Logger, docker_config: dict = None):
        self.logger = logger
        self.docker_config = docker_config or {}
        self._client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Docker client with proper error handling."""
        try:
            # Use explicit socket path for container environments
            docker_timeout = self.docker_config.get('timeout', 60)
            socket_path = 'unix:///var/run/docker.sock'
            
            # Create Docker client with explicit socket path
            self._client = docker.DockerClient(
                base_url=socket_path,
                timeout=docker_timeout
            )
            
            # Test the connection by getting Docker info
            info = self._client.info()
            self.logger.info(f"Docker client initialized successfully. Server version: {info.get('ServerVersion', 'unknown')}")
            self.logger.info(f"Connected to Docker daemon at {socket_path}")
            
        except Exception as e:
            self.logger.error(f"Cannot connect to Docker daemon at {socket_path}: {e}")
            # Try fallback to environment detection
            try:
                self.logger.info("Attempting fallback to environment-based Docker client...")
                self._client = docker.from_env(timeout=docker_timeout)
                info = self._client.info()
                self.logger.info(f"Fallback successful. Server version: {info.get('ServerVersion', 'unknown')}")
            except Exception as fallback_e:
                self.logger.error(f"Fallback also failed: {fallback_e}")
                raise RuntimeError(f'Cannot connect to Docker daemon: {e}. Fallback failed: {fallback_e}') from e
    
    @property
    def client(self) -> docker.DockerClient:
        """Get Docker client instance."""
        if self._client is None:
            self._initialize_client()
        return self._client
    
    def create_container(self, 
                        image_name: str,
                        container_name: str,
                        ports: Dict[str, int],
                        volumes: Dict[str, str],
                        environment: Dict[str, str],
                        cpu_limit: str = "1.0",
                        memory_limit: str = "1g") -> str:
        """
        Create and start a Docker container as a sibling container on the main VM.
        
        This method creates student lab containers directly on the host Docker daemon,
        NOT as Docker-in-Docker containers. The containers will be siblings to the
        lab-manager container and accessible from the main VM.
        """
        try:
            # Build port configuration
            port_bindings = {}
            exposed_ports = {}
            
            for internal_port, external_port in ports.items():
                if self._is_port_available(external_port):
                    port_bindings[internal_port] = external_port
                    exposed_ports[internal_port] = {}
                else:
                    # Find alternative port
                    alt_port = self._find_available_port(external_port)
                    port_bindings[internal_port] = alt_port
                    exposed_ports[internal_port] = {}
                    self.logger.warning(f"Port {external_port} unavailable, using {alt_port}")
            
            # Prepare volumes with host paths (important for main VM access)
            volume_mounts = {}
            for container_path, host_path in volumes.items():
                # Ensure host paths are accessible from main VM
                volume_mounts[host_path] = {'bind': container_path, 'mode': 'rw'}
            
            # Add environment variables for student containers
            student_env = {
                **environment,
                'CONTAINER_TYPE': 'student_lab',
                'LAB_MANAGER_HOST': 'lab-manager:8006',
                'CREATED_BY': 'course-creator-lab-manager'
            }
            
            # Create container with specific configuration for main VM deployment
            container = self.client.containers.create(
                image=image_name,
                name=container_name,
                ports=port_bindings,
                volumes=volume_mounts,
                environment=student_env,
                detach=True,
                network_mode='bridge',  # Use bridge network for main VM access
                cpu_period=100000,
                cpu_quota=int(float(cpu_limit) * 100000),
                mem_limit=memory_limit,
                restart_policy={"Name": "unless-stopped"},
                labels={
                    'created_by': 'course-creator-lab-manager',
                    'container_type': 'student_lab',
                    'lab_session': container_name
                },
                # Security options for lab containers
                security_opt=['no-new-privileges:true'],
                # Prevent container from accessing Docker socket
                tmpfs={'/tmp': 'rw,noexec,nosuid,size=100m'}
            )
            
            container.start()
            
            # Get the actual port mappings after start
            container.reload()
            actual_ports = {}
            if container.ports:
                for container_port, host_bindings in container.ports.items():
                    if host_bindings:
                        actual_ports[container_port] = host_bindings[0]['HostPort']
            
            self.logger.info(f"Student lab container {container_name} created and started on main VM")
            self.logger.info(f"Container ID: {container.id[:12]}")
            self.logger.info(f"Port mappings: {actual_ports}")
            
            return container.id
            
        except APIError as e:
            self.logger.error(f"Failed to create student lab container {container_name}: {e}")
            raise Exception(f"Container creation failed: {e}")
    
    def stop_container(self, container_name: str, timeout: int = 10) -> bool:
        """Stop a Docker container."""
        try:
            container = self.client.containers.get(container_name)
            container.stop(timeout=timeout)
            self.logger.info(f"Container {container_name} stopped")
            return True
        except NotFound:
            self.logger.warning(f"Container {container_name} not found")
            return False
        except APIError as e:
            self.logger.error(f"Failed to stop container {container_name}: {e}")
            return False
    
    def remove_container(self, container_name: str, force: bool = False) -> bool:
        """Remove a Docker container."""
        try:
            container = self.client.containers.get(container_name)
            container.remove(force=force)
            self.logger.info(f"Container {container_name} removed")
            return True
        except NotFound:
            self.logger.warning(f"Container {container_name} not found")
            return False
        except APIError as e:
            self.logger.error(f"Failed to remove container {container_name}: {e}")
            return False
    
    def get_container_status(self, container_name: str) -> Optional[str]:
        """Get container status."""
        try:
            container = self.client.containers.get(container_name)
            return container.status
        except NotFound:
            return None
        except APIError as e:
            self.logger.error(f"Failed to get status for {container_name}: {e}")
            return None
    
    def build_custom_image(self, 
                          dockerfile_content: str,
                          image_name: str,
                          build_args: Optional[Dict[str, str]] = None) -> bool:
        """Build a custom Docker image from Dockerfile content."""
        try:
            # Create temporary directory for build context
            with tempfile.TemporaryDirectory() as build_dir:
                dockerfile_path = Path(build_dir) / "Dockerfile"
                dockerfile_path.write_text(dockerfile_content)
                
                # Build image
                self.client.images.build(
                    path=build_dir,
                    tag=image_name,
                    buildargs=build_args or {},
                    rm=True
                )
                
                self.logger.info(f"Custom image {image_name} built successfully")
                return True
                
        except APIError as e:
            self.logger.error(f"Failed to build image {image_name}: {e}")
            return False
    
    def list_containers(self, all_containers: bool = True) -> List[Dict]:
        """List all containers."""
        try:
            containers = self.client.containers.list(all=all_containers)
            return [
                {
                    'id': container.id[:12],
                    'name': container.name,
                    'status': container.status,
                    'image': container.image.tags[0] if container.image.tags else 'unknown',
                    'created': container.attrs['Created']
                }
                for container in containers
            ]
        except APIError as e:
            self.logger.error(f"Failed to list containers: {e}")
            return []
    
    def get_container_logs(self, container_name: str, tail: int = 100) -> str:
        """Get container logs."""
        try:
            container = self.client.containers.get(container_name)
            logs = container.logs(tail=tail, timestamps=True)
            return logs.decode('utf-8', errors='replace')
        except NotFound:
            return "Container not found"
        except APIError as e:
            self.logger.error(f"Failed to get logs for {container_name}: {e}")
            return f"Error retrieving logs: {e}"
    
    def _is_port_available(self, port: int) -> bool:
        """Check if a port is available."""
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            return result != 0
    
    def _find_available_port(self, start_port: int, max_attempts: int = 100) -> int:
        """Find an available port starting from start_port."""
        for port in range(start_port, start_port + max_attempts):
            if self._is_port_available(port):
                return port
        raise RuntimeError(f"No available ports found starting from {start_port}")
    
    def cleanup_stopped_containers(self, max_age_hours: int = 24) -> int:
        """Clean up stopped containers older than max_age_hours."""
        cleaned = 0
        try:
            containers = self.client.containers.list(all=True, 
                                                    filters={'status': 'exited'})
            
            cutoff_time = time.time() - (max_age_hours * 3600)
            
            for container in containers:
                created_time = container.attrs['Created']
                # Parse ISO format timestamp
                from datetime import datetime
                created_dt = datetime.fromisoformat(created_time.replace('Z', '+00:00'))
                
                if created_dt.timestamp() < cutoff_time:
                    container.remove()
                    cleaned += 1
                    self.logger.info(f"Cleaned up old container: {container.name}")
            
            return cleaned
            
        except APIError as e:
            self.logger.error(f"Failed to cleanup containers: {e}")
            return 0