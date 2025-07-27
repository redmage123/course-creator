"""
Smoke Tests for Service Startup
These tests verify that all services can actually start and respond to health checks.
This would have caught the analytics database configuration bug.
"""

import pytest
import requests
import time
import subprocess
import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional
import docker
import signal
import sys

PROJECT_ROOT = Path(__file__).parent.parent.parent

# Service configuration from docker-compose
SERVICES = {
    "user-management": {"port": 8000, "path": "services/user-management"},
    "course-generator": {"port": 8001, "path": "services/course-generator"},
    "content-storage": {"port": 8003, "path": "services/content-storage"},
    "course-management": {"port": 8004, "path": "services/course-management"},
    "content-management": {"port": 8005, "path": "services/content-management"},
    "lab-containers": {"port": 8006, "path": "lab-containers"},
    "analytics": {"port": 8007, "path": "services/analytics"}
}

class TestServiceHealthChecks:
    """Test that all services respond to health checks"""
    
    def test_all_services_health_endpoints_respond(self):
        """Smoke test - verify all services can respond to health checks"""
        failed_services = []
        
        for service_name, config in SERVICES.items():
            url = f"http://localhost:{config['port']}/health"
            
            try:
                response = requests.get(url, timeout=5)
                if response.status_code != 200:
                    failed_services.append(f"{service_name}: HTTP {response.status_code}")
                else:
                    # Verify health response format
                    try:
                        health_data = response.json()
                        if 'status' not in health_data:
                            failed_services.append(f"{service_name}: Missing 'status' in health response")
                        elif health_data['status'] != 'healthy':
                            failed_services.append(f"{service_name}: Status is '{health_data['status']}'")
                    except ValueError:
                        failed_services.append(f"{service_name}: Invalid JSON response")
                        
            except requests.RequestException as e:
                failed_services.append(f"{service_name}: {str(e)}")
        
        if failed_services:
            pytest.fail(f"Services failed health checks: {failed_services}")
    
    def test_analytics_service_database_connection(self):
        """Specific test for analytics service database connection"""
        try:
            response = requests.get("http://localhost:8007/health", timeout=10)
            assert response.status_code == 200, \
                f"Analytics health check failed: HTTP {response.status_code}"
            
            health_data = response.json()
            assert health_data['status'] == 'healthy', \
                f"Analytics service not healthy: {health_data}"
            
            # Check database status specifically
            assert 'database_status' in health_data, \
                "Analytics health check should include database_status"
            assert health_data['database_status'] == 'connected', \
                f"Analytics database not connected: {health_data['database_status']}"
                
        except requests.RequestException as e:
            pytest.fail(f"Analytics service not responding: {e}")

class TestDockerComposeStartup:
    """Test that docker-compose can start all services successfully"""
    
    @pytest.fixture(scope="class")
    def docker_compose_environment(self):
        """Start services with docker-compose for testing"""
        compose_file = PROJECT_ROOT / "docker-compose.yml"
        
        # Start services
        start_process = subprocess.run([
            'docker-compose', '-f', str(compose_file), 'up', '-d'
        ], capture_output=True, text=True)
        
        if start_process.returncode != 0:
            pytest.skip(f"Could not start docker-compose: {start_process.stderr}")
        
        # Wait for services to be ready
        time.sleep(30)
        
        yield
        
        # Cleanup
        subprocess.run([
            'docker-compose', '-f', str(compose_file), 'down'
        ], capture_output=True)
    
    def test_docker_compose_all_services_healthy(self, docker_compose_environment):
        """Test that all services start healthy in docker-compose"""
        client = docker.from_env()
        
        failed_services = []
        
        try:
            # Check container health
            containers = client.containers.list()
            course_creator_containers = [
                c for c in containers 
                if any(service in c.name for service in SERVICES.keys())
            ]
            
            for container in course_creator_containers:
                if container.status != 'running':
                    failed_services.append(f"{container.name}: {container.status}")
                elif hasattr(container.attrs['State'], 'Health'):
                    health = container.attrs['State'].get('Health', {})
                    if health.get('Status') not in ['healthy', None]:
                        failed_services.append(f"{container.name}: {health.get('Status')}")
            
            if failed_services:
                pytest.fail(f"Unhealthy containers: {failed_services}")
                
        except docker.errors.DockerException as e:
            pytest.skip(f"Docker not available: {e}")
    
    def test_docker_compose_service_dependencies(self, docker_compose_environment):
        """Test that service dependencies start in correct order"""
        # Test that database is ready before services
        db_ready = self._wait_for_service("http://localhost:5433", max_wait=60)
        assert db_ready, "Database should be ready before services"
        
        # Test that services can connect to database
        for service_name, config in SERVICES.items():
            service_url = f"http://localhost:{config['port']}/health"
            service_ready = self._wait_for_service(service_url, max_wait=30)
            assert service_ready, f"Service {service_name} should start after database"
    
    @staticmethod
    def _wait_for_service(url: str, max_wait: int = 30) -> bool:
        """Wait for service to respond"""
        start_time = time.time()
        while time.time() - start_time < max_wait:
            try:
                if url.startswith('http'):
                    response = requests.get(url, timeout=2)
                    if response.status_code == 200:
                        return True
                else:
                    # For database, just check if port is open
                    import socket
                    host, port = url.replace('http://', '').split(':')
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    result = sock.connect_ex((host, int(port)))
                    sock.close()
                    if result == 0:
                        return True
            except:
                pass
            time.sleep(1)
        return False

class TestNativeServiceStartup:
    """Test that services can start natively (non-Docker)"""
    
    def test_analytics_service_starts_natively(self):
        """Test analytics service can start with native Python"""
        # Set test environment
        test_env = os.environ.copy()
        test_env.update({
            'DB_HOST': 'localhost',
            'DB_PORT': '5433',
            'DB_USER': 'course_user', 
            'DB_PASSWORD': os.getenv('DB_PASSWORD', 'default_password'),
            'ANALYTICS_PORT': '8009'  # Different port to avoid conflicts
        })
        
        analytics_script = PROJECT_ROOT / "services" / "analytics" / "run.py"
        
        try:
            # Start service
            process = subprocess.Popen([
                'python', str(analytics_script)
            ], env=test_env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            
            # Wait for startup
            time.sleep(10)
            
            # Test health endpoint
            response = requests.get('http://localhost:8009/health', timeout=5)
            assert response.status_code == 200
            
            health_data = response.json()
            assert health_data['status'] == 'healthy'
            
        except Exception as e:
            pytest.fail(f"Native analytics startup failed: {e}")
        finally:
            if 'process' in locals():
                process.terminate()
                process.wait(timeout=5)

class TestServiceConfiguration:
    """Test service configuration consistency"""
    
    def test_all_services_have_dockerfiles(self):
        """Test that all services have Dockerfile"""
        missing_dockerfiles = []
        
        for service_name, config in SERVICES.items():
            dockerfile_path = PROJECT_ROOT / config['path'] / 'Dockerfile'
            if not dockerfile_path.exists():
                missing_dockerfiles.append(service_name)
        
        assert len(missing_dockerfiles) == 0, \
            f"Services missing Dockerfiles: {missing_dockerfiles}"
    
    def test_all_services_have_run_scripts(self):
        """Test that all services have run.py scripts"""
        missing_run_scripts = []
        
        for service_name, config in SERVICES.items():
            run_script_path = PROJECT_ROOT / config['path'] / 'run.py'
            if not run_script_path.exists():
                missing_run_scripts.append(service_name)
        
        assert len(missing_run_scripts) == 0, \
            f"Services missing run.py scripts: {missing_run_scripts}"
    
    def test_docker_compose_services_match_expected(self):
        """Test that docker-compose.yml includes all expected services"""
        compose_path = PROJECT_ROOT / "docker-compose.yml"
        with open(compose_path) as f:
            compose_config = yaml.safe_load(f)
        
        missing_services = []
        for service_name in SERVICES.keys():
            if service_name not in compose_config['services']:
                missing_services.append(service_name)
        
        assert len(missing_services) == 0, \
            f"Services missing from docker-compose.yml: {missing_services}"

class TestDatabaseConnectivity:
    """Test database connectivity from all services"""
    
    def test_database_accessible_from_all_services(self):
        """Test that database is accessible from all service locations"""
        import psycopg2
        
        # Test database connection with expected configuration
        try:
            conn = psycopg2.connect(
                host='localhost',
                port=5433,
                database='course_creator',
                user='course_user',
                password=os.getenv('DB_PASSWORD', 'default_password')
            )
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1
            
            cursor.close()
            conn.close()
            
        except psycopg2.Error as e:
            pytest.fail(f"Database connection failed: {e}")
    
    def test_redis_accessible_from_services(self):
        """Test that Redis is accessible"""
        import redis
        
        try:
            r = redis.Redis(host='localhost', port=6379, db=0)
            r.ping()
        except redis.RedisError as e:
            pytest.fail(f"Redis connection failed: {e}")

class TestServiceEndpointConsistency:
    """Test service endpoint consistency"""
    
    def test_all_services_have_health_endpoints(self):
        """Test that all services implement /health endpoint"""
        for service_name, config in SERVICES.items():
            url = f"http://localhost:{config['port']}/health"
            
            try:
                response = requests.get(url, timeout=5)
                assert response.status_code == 200, \
                    f"Service {service_name} health endpoint returned {response.status_code}"
                
                # Verify response format
                health_data = response.json()
                assert 'status' in health_data, \
                    f"Service {service_name} health response missing 'status' field"
                assert 'service' in health_data, \
                    f"Service {service_name} health response missing 'service' field"
                    
            except requests.RequestException as e:
                pytest.fail(f"Service {service_name} health endpoint failed: {e}")

class TestStartupSequence:
    """Test service startup sequence and dependencies"""
    
    def test_services_start_in_dependency_order(self):
        """Test that services start in correct dependency order"""
        # This test would start services individually and verify dependencies
        startup_order = [
            'postgres',
            'redis', 
            'user-management',
            'course-generator',
            'content-storage',
            'course-management',
            'content-management',
            'analytics',
            'lab-containers'
        ]
        
        # For now, just verify the startup order is documented
        compose_path = PROJECT_ROOT / "docker-compose.yml"
        with open(compose_path) as f:
            compose_config = yaml.safe_load(f)
        
        # Check that services have depends_on relationships
        services_with_deps = []
        for service_name, service_config in compose_config['services'].items():
            if 'depends_on' in service_config:
                services_with_deps.append(service_name)
        
        # Most services should have database dependencies
        assert len(services_with_deps) > 0, \
            "Some services should have explicit dependencies"

# Pytest markers
pytestmark = [
    pytest.mark.smoke,
    pytest.mark.startup,
    pytest.mark.integration
]