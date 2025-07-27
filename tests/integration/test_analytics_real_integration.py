"""
Real Analytics Integration Tests
These tests use actual database connections and real service startup
to catch configuration bugs that mocks would hide.
"""

import pytest
import asyncio
import asyncpg
import os
import time
import requests
import subprocess
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path

# Test configuration
TEST_DB_CONFIG = {
    'host': 'localhost',
    'port': 5434,  # Test database port
    'database': 'course_creator_test',
    'user': 'course_user',
    'password': 'test_password'
}

PROJECT_ROOT = Path(__file__).parent.parent.parent

class TestRealDatabaseConnection:
    """Test real database connections without mocking"""
    
    @pytest.fixture(scope="class")
    async def real_db_pool(self):
        """Create real database connection pool for testing"""
        try:
            # Create test user if it doesn't exist
            admin_pool = await asyncpg.create_pool(
                host=TEST_DB_CONFIG['host'],
                port=TEST_DB_CONFIG['port'],
                database=TEST_DB_CONFIG['database'],
                user='postgres',
                password='test_password'
            )
            
            async with admin_pool.acquire() as conn:
                # Create test user
                try:
                    await conn.execute(f"""
                        CREATE USER {TEST_DB_CONFIG['user']} 
                        WITH PASSWORD '{TEST_DB_CONFIG['password']}'
                    """)
                    await conn.execute(f"""
                        GRANT ALL PRIVILEGES ON DATABASE {TEST_DB_CONFIG['database']} 
                        TO {TEST_DB_CONFIG['user']}
                    """)
                except asyncpg.DuplicateObjectError:
                    pass  # User already exists
            
            await admin_pool.close()
            
            # Create pool with test user
            pool = await asyncpg.create_pool(**TEST_DB_CONFIG, min_size=2, max_size=5)
            yield pool
            await pool.close()
            
        except Exception as e:
            pytest.skip(f"Cannot connect to test database: {e}")
    
    @pytest.mark.asyncio
    async def test_database_connection_real(self, real_db_pool):
        """Test that we can actually connect to the database"""
        async with real_db_pool.acquire() as conn:
            result = await conn.fetchval("SELECT 1")
            assert result == 1
    
    @pytest.mark.asyncio
    async def test_analytics_tables_creation(self, real_db_pool):
        """Test that analytics tables can be created"""
        async with real_db_pool.acquire() as conn:
            # Create test analytics tables
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS student_activities (
                    id SERIAL PRIMARY KEY,
                    student_id VARCHAR(255) NOT NULL,
                    activity_type VARCHAR(100) NOT NULL,
                    course_id VARCHAR(255),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata JSONB
                )
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS lab_usage_metrics (
                    id SERIAL PRIMARY KEY,
                    student_id VARCHAR(255) NOT NULL,
                    lab_id VARCHAR(255) NOT NULL,
                    session_start TIMESTAMP NOT NULL,
                    session_end TIMESTAMP,
                    ide_type VARCHAR(50),
                    activities JSONB
                )
            """)
            
            # Verify tables exist
            tables = await conn.fetch("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name IN ('student_activities', 'lab_usage_metrics')
            """)
            
            table_names = [row['table_name'] for row in tables]
            assert 'student_activities' in table_names
            assert 'lab_usage_metrics' in table_names

class TestAnalyticsServiceRealStartup:
    """Test analytics service actually starts with real configuration"""
    
    @pytest.fixture(scope="class")
    def test_environment(self):
        """Set up test environment variables"""
        test_env = os.environ.copy()
        test_env.update({
            'DB_HOST': 'localhost',
            'DB_PORT': '5434',
            'DB_USER': 'course_user',
            'DB_PASSWORD': 'test_password',
            'DB_NAME': 'course_creator_test',
            'ANALYTICS_PORT': '8008',
            'ENVIRONMENT': 'test'
        })
        return test_env
    
    def test_analytics_service_starts_with_real_config(self, test_environment):
        """Test that analytics service actually starts with correct configuration"""
        # Start the analytics service as a subprocess
        analytics_script = PROJECT_ROOT / "services" / "analytics" / "run.py"
        
        try:
            # Start service
            process = subprocess.Popen(
                ['python', str(analytics_script)],
                env=test_environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for service to start
            time.sleep(10)
            
            # Test health endpoint
            try:
                response = requests.get('http://localhost:8008/health', timeout=5)
                assert response.status_code == 200
                
                health_data = response.json()
                assert health_data['status'] == 'healthy'
                assert health_data['service'] == 'analytics'
                assert 'database_status' in health_data
                
            finally:
                process.terminate()
                process.wait(timeout=5)
                
        except subprocess.TimeoutExpired:
            pytest.fail("Analytics service failed to start within timeout")
        except requests.RequestException as e:
            pytest.fail(f"Analytics service not responding: {e}")

class TestServiceConfigurationConsistency:
    """Test that service configurations are consistent with deployment"""
    
    def test_analytics_config_matches_docker_compose(self):
        """Test analytics config matches docker-compose configuration"""
        import yaml
        
        # Read docker-compose.yml
        compose_path = PROJECT_ROOT / "docker-compose.yml"
        with open(compose_path) as f:
            compose_config = yaml.safe_load(f)
        
        # Check analytics service configuration
        analytics_service = compose_config['services']['analytics']
        
        # Verify port mapping
        port_mapping = analytics_service['ports'][0]
        assert '8007:8007' == port_mapping, \
            f"Analytics port mapping should be 8007:8007, got {port_mapping}"
        
        # Verify environment variables
        env_vars = analytics_service['environment']
        db_url = next((var for var in env_vars if var.startswith('DATABASE_URL=')), None)
        assert db_url is not None, "DATABASE_URL should be set in docker-compose"
        
        # Verify database URL uses correct port
        assert 'postgres:5432' in db_url, \
            "DATABASE_URL should reference postgres container on port 5432"
    
    def test_all_services_have_health_checks(self):
        """Test that all services have health check endpoints"""
        import yaml
        
        compose_path = PROJECT_ROOT / "docker-compose.yml"
        with open(compose_path) as f:
            compose_config = yaml.safe_load(f)
        
        services_without_health_checks = []
        
        for service_name, service_config in compose_config['services'].items():
            if 'healthcheck' not in service_config and service_name not in ['postgres', 'redis']:
                services_without_health_checks.append(service_name)
        
        assert len(services_without_health_checks) == 0, \
            f"Services without health checks: {services_without_health_checks}"

class TestDatabaseMigrationConsistency:
    """Test database schema consistency"""
    
    @pytest.mark.asyncio
    async def test_database_schema_matches_expectations(self):
        """Test that database schema matches what analytics service expects"""
        try:
            pool = await asyncpg.create_pool(**TEST_DB_CONFIG)
            
            async with pool.acquire() as conn:
                # Test basic connection
                await conn.fetchval("SELECT 1")
                
                # Check if we can create analytics-related tables
                # This tests that the database user has correct permissions
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS test_analytics_permissions (
                        id SERIAL PRIMARY KEY,
                        test_data TEXT
                    )
                """)
                
                # Test insert/select operations
                await conn.execute("""
                    INSERT INTO test_analytics_permissions (test_data) VALUES ('test')
                """)
                
                result = await conn.fetchval("""
                    SELECT test_data FROM test_analytics_permissions LIMIT 1
                """)
                
                assert result == 'test'
                
                # Clean up
                await conn.execute("DROP TABLE test_analytics_permissions")
            
            await pool.close()
            
        except Exception as e:
            pytest.fail(f"Database schema test failed: {e}")

class TestEnvironmentSpecificConfiguration:
    """Test environment-specific configuration handling"""
    
    def test_production_vs_test_config_differences(self):
        """Test that test and production configs have appropriate differences"""
        import yaml
        
        # Load production docker-compose
        prod_compose_path = PROJECT_ROOT / "docker-compose.yml"
        with open(prod_compose_path) as f:
            prod_config = yaml.safe_load(f)
        
        # Load test docker-compose
        test_compose_path = PROJECT_ROOT / "docker-compose.test.yml"
        with open(test_compose_path) as f:
            test_config = yaml.safe_load(f)
        
        # Test database should use different port
        prod_db_port = prod_config['services']['postgres']['ports'][0]
        test_db_port = test_config['services']['postgres-test']['ports'][0]
        
        assert prod_db_port != test_db_port, \
            "Test and production databases should use different ports"
        
        # Verify test environment uses test database
        if 'analytics-test' in test_config['services']:
            test_analytics = test_config['services']['analytics-test']
            test_env_vars = test_analytics['environment']
            
            db_host_var = next((var for var in test_env_vars if var.startswith('DB_HOST=')), None)
            assert 'postgres-test' in db_host_var, \
                "Test analytics should connect to test database"

# Test execution helpers
class TestExecutionHelpers:
    """Helper methods for test execution"""
    
    @staticmethod
    def wait_for_service_health(url: str, timeout: int = 30) -> bool:
        """Wait for service to be healthy"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{url}/health", timeout=2)
                if response.status_code == 200:
                    return True
            except requests.RequestException:
                pass
            time.sleep(1)
        return False
    
    @staticmethod
    def start_test_database() -> subprocess.Popen:
        """Start test database container"""
        return subprocess.Popen([
            'docker-compose', '-f', 'docker-compose.test.yml', 
            'up', '-d', 'postgres-test'
        ])
    
    @staticmethod
    def stop_test_database():
        """Stop test database container"""
        subprocess.run([
            'docker-compose', '-f', 'docker-compose.test.yml', 
            'down'
        ])

# Pytest configuration
pytestmark = [
    pytest.mark.integration,
    pytest.mark.real_db,
    pytest.mark.slow
]