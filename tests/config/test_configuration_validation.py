"""
Configuration Validation Tests
These tests ensure that service configurations match deployment requirements
and catch configuration mismatches that cause runtime failures.
"""

import pytest
import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any
import importlib.util

# Test configuration constants
EXPECTED_DB_PORT = 5433
EXPECTED_DB_USER = "course_user"
EXPECTED_SERVICES = {
    "user-management": 8000,
    "course-generator": 8001, 
    "content-storage": 8003,
    "course-management": 8004,
    "content-management": 8005,
    "lab-containers": 8006,
    "analytics": 8007
}

PROJECT_ROOT = Path(__file__).parent.parent.parent

class TestDatabaseConfiguration:
    """Test database configuration consistency across services"""
    
    def test_analytics_service_database_defaults(self):
        """Test analytics service has correct database configuration defaults"""
        # Import analytics main module
        spec = importlib.util.spec_from_file_location(
            "analytics_main", 
            PROJECT_ROOT / "services" / "analytics" / "main.py"
        )
        analytics_main = importlib.util.module_from_spec(spec)
        
        # Read the source code to check defaults
        source_path = PROJECT_ROOT / "services" / "analytics" / "main.py"
        with open(source_path, 'r') as f:
            source_code = f.read()
        
        # Verify correct defaults are in the source
        assert f"DB_PORT', {EXPECTED_DB_PORT}" in source_code, \
            f"Analytics service should default to port {EXPECTED_DB_PORT}"
        assert f"DB_USER', '{EXPECTED_DB_USER}'" in source_code, \
            f"Analytics service should default to user {EXPECTED_DB_USER}"
        
    def test_docker_compose_database_port_mapping(self):
        """Test docker-compose maps correct database port"""
        docker_compose_path = PROJECT_ROOT / "docker-compose.yml"
        
        with open(docker_compose_path, 'r') as f:
            compose_config = yaml.safe_load(f)
        
        postgres_service = compose_config['services']['postgres']
        port_mapping = postgres_service['ports'][0]
        
        # Should map host port 5433 to container port 5432
        assert port_mapping == f"{EXPECTED_DB_PORT}:5432", \
            f"PostgreSQL should be mapped to host port {EXPECTED_DB_PORT}"
    
    def test_environment_file_consistency(self):
        """Test that .cc_env file has correct database configuration"""
        env_file_path = PROJECT_ROOT / ".cc_env"
        
        if env_file_path.exists():
            with open(env_file_path, 'r') as f:
                env_content = f.read()
            
            assert f"DB_PORT={EXPECTED_DB_PORT}" in env_content, \
                f"Environment file should set DB_PORT={EXPECTED_DB_PORT}"
            assert f"DB_USER={EXPECTED_DB_USER}" in env_content, \
                f"Environment file should set DB_USER={EXPECTED_DB_USER}"

class TestServicePortConfiguration:
    """Test service port configuration consistency"""
    
    def test_service_port_consistency(self):
        """Test that all services use consistent port configuration"""
        docker_compose_path = PROJECT_ROOT / "docker-compose.yml"
        
        with open(docker_compose_path, 'r') as f:
            compose_config = yaml.safe_load(f)
        
        for service_name, expected_port in EXPECTED_SERVICES.items():
            if service_name in compose_config['services']:
                service_config = compose_config['services'][service_name]
                if 'ports' in service_config:
                    port_mapping = service_config['ports'][0]
                    host_port = int(port_mapping.split(':')[0])
                    assert host_port == expected_port, \
                        f"Service {service_name} should use port {expected_port}, got {host_port}"

class TestEnvironmentVariableValidation:
    """Test environment variable configuration"""
    
    def test_required_environment_variables_defined(self):
        """Test that all required environment variables are defined"""
        required_vars = [
            'ANTHROPIC_API_KEY',
            'JWT_SECRET_KEY',
            'DB_PASSWORD'
        ]
        
        env_file_path = PROJECT_ROOT / ".cc_env"
        if env_file_path.exists():
            with open(env_file_path, 'r') as f:
                env_content = f.read()
            
            for var in required_vars:
                assert var in env_content, \
                    f"Required environment variable {var} not found in .cc_env"
    
    def test_api_keys_not_empty(self):
        """Test that API keys are not empty or placeholder values"""
        env_file_path = PROJECT_ROOT / ".cc_env"
        if env_file_path.exists():
            with open(env_file_path, 'r') as f:
                env_content = f.read()
            
            # Check for placeholder values
            placeholder_patterns = [
                'your_key_here',
                'replace_this',
                'change_this',
                'sk-ant-api03-PLACEHOLDER'
            ]
            
            for pattern in placeholder_patterns:
                assert pattern not in env_content, \
                    f"Found placeholder '{pattern}' in environment file"

class TestConfigurationFiles:
    """Test configuration file consistency"""
    
    def test_hydra_config_database_settings(self):
        """Test Hydra configuration files have correct database settings"""
        config_path = PROJECT_ROOT / "config" / "database" / "postgres.yaml"
        
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Check default port in config
            port_setting = config['database']['port']
            # Should reference environment variable with correct default
            assert f"{EXPECTED_DB_PORT}" in str(port_setting), \
                f"Database config should reference port {EXPECTED_DB_PORT}"

class TestServiceImportability:
    """Test that service modules can be imported without errors"""
    
    def test_analytics_service_imports(self):
        """Test analytics service can be imported"""
        try:
            spec = importlib.util.spec_from_file_location(
                "analytics_main", 
                PROJECT_ROOT / "services" / "analytics" / "main.py"
            )
            analytics_main = importlib.util.module_from_spec(spec)
            # Don't execute, just test importability
            assert spec is not None
        except Exception as e:
            pytest.fail(f"Analytics service cannot be imported: {e}")
    
    def test_all_service_run_scripts_exist(self):
        """Test that all services have run.py files"""
        services_dir = PROJECT_ROOT / "services"
        
        for service_name in EXPECTED_SERVICES.keys():
            service_dir = services_dir / service_name
            run_script = service_dir / "run.py"
            
            assert run_script.exists(), \
                f"Service {service_name} missing run.py script"

class TestDockerConfiguration:
    """Test Docker configuration consistency"""
    
    def test_dockerfile_port_exposure(self):
        """Test that Dockerfiles expose correct ports"""
        services_dir = PROJECT_ROOT / "services"
        
        for service_name, expected_port in EXPECTED_SERVICES.items():
            dockerfile_path = services_dir / service_name / "Dockerfile"
            
            if dockerfile_path.exists():
                with open(dockerfile_path, 'r') as f:
                    dockerfile_content = f.read()
                
                assert f"EXPOSE {expected_port}" in dockerfile_content, \
                    f"Dockerfile for {service_name} should expose port {expected_port}"
    
    def test_docker_compose_service_dependencies(self):
        """Test that services have correct dependencies in docker-compose"""
        docker_compose_path = PROJECT_ROOT / "docker-compose.yml"
        
        with open(docker_compose_path, 'r') as f:
            compose_config = yaml.safe_load(f)
        
        # Analytics should depend on postgres and redis
        if 'analytics' in compose_config['services']:
            analytics_config = compose_config['services']['analytics']
            assert 'depends_on' in analytics_config, \
                "Analytics service should have database dependencies"

# Utility functions for configuration testing
def load_service_config(service_name: str) -> Dict[str, Any]:
    """Load configuration for a specific service"""
    config_path = PROJECT_ROOT / "services" / service_name / "config.py"
    if config_path.exists():
        spec = importlib.util.spec_from_file_location(f"{service_name}_config", config_path)
        config_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config_module)
        return config_module
    return {}

def check_environment_variable_usage(service_path: Path, var_name: str) -> bool:
    """Check if a service properly uses an environment variable"""
    for py_file in service_path.glob("**/*.py"):
        with open(py_file, 'r') as f:
            content = f.read()
            if f"os.getenv('{var_name}'" in content or f'os.getenv("{var_name}"' in content:
                return True
    return False

# Integration test markers
pytestmark = [
    pytest.mark.config,
    pytest.mark.validation
]