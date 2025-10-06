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
            # Docker API expects port_bindings as dict or list format
            port_bindings = {}
            exposed_ports = []

            for internal_port, external_port in ports.items():
                if self._is_port_available(external_port):
                    port_bindings[internal_port] = external_port
                    exposed_ports.append(internal_port)
                else:
                    # Find alternative port
                    alt_port = self._find_available_port(external_port)
                    port_bindings[internal_port] = alt_port
                    exposed_ports.append(internal_port)
                    self.logger.warning(f"Port {external_port} unavailable, using {alt_port}")
            
            # Prepare volumes - Keep it simple using the high-level API format
            # The high-level client expects: {host_path: {'bind': container_path, 'mode': 'rw'}}
            volume_mounts = {}
            for host_path, volume_config in volumes.items():
                if isinstance(volume_config, dict):
                    container_bind_path = volume_config.get('bind', '/home/student')
                    mode = volume_config.get('mode', 'rw')
                    volume_mounts[host_path] = {'bind': container_bind_path, 'mode': mode}
                else:
                    volume_mounts[host_path] = {'bind': volume_config, 'mode': 'rw'}

            # Add environment variables for student containers
            student_env = {
                **environment,
                'CONTAINER_TYPE': 'student_lab',
                'LAB_MANAGER_HOST': 'lab-manager:8006',
                'CREATED_BY': 'course-creator-lab-manager'
            }

            # DEBUG: Test container creation with minimal parameters first
            # to isolate which parameter causes "unhashable type: 'dict'" error
            self.logger.info(f"DEBUG: Starting container creation for {container_name}")
            self.logger.info(f"DEBUG: image_name type: {type(image_name)}, value: {image_name}")
            self.logger.info(f"DEBUG: port_bindings type: {type(port_bindings)}, value: {port_bindings}")
            self.logger.info(f"DEBUG: volume_mounts type: {type(volume_mounts)}, value: {volume_mounts}")

            try:
                # TEST 1: Absolute minimum - just image and name
                self.logger.info("DEBUG: TEST 1 - Creating with just image and name...")
                container = self.client.containers.create(
                    image=image_name,
                    name=container_name,
                    detach=True
                )
                self.logger.info("DEBUG: TEST 1 PASSED - Basic creation works")

                # If we get here, basic creation works. Now test with each parameter.
                # Remove the test container
                container.remove(force=True)
                self.logger.info("DEBUG: Test container removed, now testing with parameters...")

                # TEST 2: Add environment
                self.logger.info("DEBUG: TEST 2 - Adding environment variables...")
                container = self.client.containers.create(
                    image=image_name,
                    name=container_name,
                    environment=student_env,
                    detach=True
                )
                self.logger.info("DEBUG: TEST 2 PASSED - Environment works")
                container.remove(force=True)

                # TEST 3: Add ports
                self.logger.info("DEBUG: TEST 3 - Adding ports...")
                container = self.client.containers.create(
                    image=image_name,
                    name=container_name,
                    environment=student_env,
                    ports=port_bindings,
                    detach=True
                )
                self.logger.info("DEBUG: TEST 3 PASSED - Ports work")
                container.remove(force=True)

                # TEST 4: Add volumes
                self.logger.info("DEBUG: TEST 4 - Adding volumes...")
                container = self.client.containers.create(
                    image=image_name,
                    name=container_name,
                    environment=student_env,
                    ports=port_bindings,
                    volumes=volume_mounts,
                    detach=True
                )
                self.logger.info("DEBUG: TEST 4 PASSED - Volumes work")
                container.remove(force=True)

                # TEST 5: Add network_mode
                self.logger.info("DEBUG: TEST 5 - Adding network_mode...")
                container = self.client.containers.create(
                    image=image_name,
                    name=container_name,
                    environment=student_env,
                    ports=port_bindings,
                    volumes=volume_mounts,
                    network_mode='bridge',
                    detach=True
                )
                self.logger.info("DEBUG: TEST 5 PASSED - network_mode works")
                container.remove(force=True)

                # TEST 6: Add CPU/memory limits
                self.logger.info("DEBUG: TEST 6 - Adding CPU/memory limits...")
                container = self.client.containers.create(
                    image=image_name,
                    name=container_name,
                    environment=student_env,
                    ports=port_bindings,
                    volumes=volume_mounts,
                    network_mode='bridge',
                    cpu_period=100000,
                    cpu_quota=int(float(cpu_limit) * 100000),
                    mem_limit=memory_limit,
                    detach=True
                )
                self.logger.info("DEBUG: TEST 6 PASSED - CPU/memory limits work")
                container.remove(force=True)

                # TEST 7: Add restart_policy
                self.logger.info("DEBUG: TEST 7 - Adding restart_policy...")
                container = self.client.containers.create(
                    image=image_name,
                    name=container_name,
                    environment=student_env,
                    ports=port_bindings,
                    volumes=volume_mounts,
                    network_mode='bridge',
                    cpu_period=100000,
                    cpu_quota=int(float(cpu_limit) * 100000),
                    mem_limit=memory_limit,
                    restart_policy={"Name": "unless-stopped"},
                    detach=True
                )
                self.logger.info("DEBUG: TEST 7 PASSED - restart_policy works")
                container.remove(force=True)

                # TEST 8: Add security_opt
                self.logger.info("DEBUG: TEST 8 - Adding security_opt...")
                container = self.client.containers.create(
                    image=image_name,
                    name=container_name,
                    environment=student_env,
                    ports=port_bindings,
                    volumes=volume_mounts,
                    network_mode='bridge',
                    cpu_period=100000,
                    cpu_quota=int(float(cpu_limit) * 100000),
                    mem_limit=memory_limit,
                    restart_policy={"Name": "unless-stopped"},
                    security_opt=['no-new-privileges:true'],
                    detach=True
                )
                self.logger.info("DEBUG: TEST 8 PASSED - security_opt works")
                container.remove(force=True)

                # TEST 9: Add tmpfs
                self.logger.info("DEBUG: TEST 9 - Adding tmpfs...")
                container = self.client.containers.create(
                    image=image_name,
                    name=container_name,
                    environment=student_env,
                    ports=port_bindings,
                    volumes=volume_mounts,
                    network_mode='bridge',
                    cpu_period=100000,
                    cpu_quota=int(float(cpu_limit) * 100000),
                    mem_limit=memory_limit,
                    restart_policy={"Name": "unless-stopped"},
                    security_opt=['no-new-privileges:true'],
                    tmpfs={'/tmp': 'rw,noexec,nosuid,size=100m'},
                    detach=True
                )
                self.logger.info("DEBUG: TEST 9 PASSED - tmpfs works")
                container.remove(force=True)

                # TEST 10: Add labels - FINAL TEST
                self.logger.info("DEBUG: TEST 10 - Adding labels (final)...")
                container = self.client.containers.create(
                    image=image_name,
                    name=container_name,
                    environment=student_env,
                    ports=port_bindings,
                    volumes=volume_mounts,
                    network_mode='bridge',
                    cpu_period=100000,
                    cpu_quota=int(float(cpu_limit) * 100000),
                    mem_limit=memory_limit,
                    restart_policy={"Name": "unless-stopped"},
                    security_opt=['no-new-privileges:true'],
                    tmpfs={'/tmp': 'rw,noexec,nosuid,size=100m'},
                    labels={
                        'created_by': 'course-creator-lab-manager',
                        'container_type': 'student_lab',
                        'lab_session': container_name
                    },
                    detach=True
                )
                self.logger.info("DEBUG: TEST 10 PASSED - All parameters work!")

            except Exception as test_error:
                self.logger.error(f"DEBUG: Test failed with error: {test_error}")
                import traceback
                self.logger.error(f"DEBUG: Full traceback: {traceback.format_exc()}")
                raise
            
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
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            raise Exception(f"Container creation failed: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error creating container {container_name}: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    def start_container(self, container_name: str) -> bool:
        """Start an existing Docker container."""
        try:
            container = self.client.containers.get(container_name)
            container.start()
            self.logger.info(f"Container {container_name} started")
            return True
        except NotFound:
            self.logger.warning(f"Container {container_name} not found")
            return False
        except APIError as e:
            self.logger.error(f"Failed to start container {container_name}: {e}")
            return False

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
        """
        Check if a port is available by querying Docker's actual port bindings.

        This method queries all running containers to check if any are using the specified
        host port. This is more reliable than socket checks because:
        1. It works from within containers (no network isolation issues)
        2. It detects ports bound by Docker containers on the host
        3. It avoids false positives from network namespace separation
        """
        try:
            # Get all running containers
            containers = self.client.containers.list()

            for container in containers:
                # Check if container has any port bindings
                if container.ports:
                    for container_port, host_bindings in container.ports.items():
                        if host_bindings:
                            for binding in host_bindings:
                                # Check if this container is using our target host port
                                host_port = binding.get('HostPort')
                                if host_port and int(host_port) == port:
                                    self.logger.debug(f"Port {port} is in use by container {container.name} ({container.id[:12]})")
                                    return False

            # Port is not used by any container
            return True

        except Exception as e:
            self.logger.warning(f"Error checking port availability for {port}: {e}. Assuming unavailable for safety.")
            return False
    
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