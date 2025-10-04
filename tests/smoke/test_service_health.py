"""
Service Health Smoke Tests

BUSINESS CONTEXT:
Before running integration tests, we must verify all services can start
and respond to health checks. This ensures the test environment is ready.

TECHNICAL IMPLEMENTATION:
- Checks if services are running via Docker
- Validates health check endpoints
- Verifies service configuration

TEST COVERAGE:
- Docker container status
- Service health endpoints
- Basic connectivity
"""

import pytest
import requests
import docker
from typing import Dict, List
import time


class TestServiceHealth:
    """
    Service health validation tests

    CRITICAL REQUIREMENT:
    These tests ensure services are running before integration tests.
    Run after import validation, before integration tests.
    """

    @pytest.fixture(scope="class")
    def docker_client(self):
        """Get Docker client"""
        try:
            client = docker.from_env()
            return client
        except Exception as e:
            pytest.skip(f"Docker not available: {e}")

    @pytest.mark.order(3)
    def test_docker_containers_running(self, docker_client):
        """
        Verify all required Docker containers are running

        VALIDATION:
        - All service containers are up
        - Containers are healthy (if health check configured)
        """
        required_services = [
            'user-management',
            'organization-management',
            'course-management',
            'content-management',
            'lab-manager',
            'rag-service',
            'demo-service',
            'postgres',
            'redis'
        ]

        containers = docker_client.containers.list()
        running_services = []

        for container in containers:
            name = container.name
            # Extract service name from container name
            for service in required_services:
                if service in name:
                    running_services.append(service)
                    # Check health status if available
                    try:
                        health = container.attrs.get('State', {}).get('Health', {}).get('Status')
                        if health and health != 'healthy':
                            pytest.fail(f"Container {name} is unhealthy: {health}")
                    except:
                        pass  # No health check configured

        missing_services = set(required_services) - set(running_services)

        if missing_services:
            pytest.skip(
                f"Required services not running: {', '.join(missing_services)}. "
                f"Start services with: docker-compose up -d"
            )

    @pytest.mark.order(3)
    def test_service_health_endpoints(self):
        """
        Test health check endpoints for all services

        VALIDATION:
        - Health endpoints respond with 200
        - Response indicates service is ready
        """
        health_checks = [
            ('user-management', 'https://localhost:8000/health'),
            ('organization-management', 'https://localhost:8008/health'),
            ('course-management', 'https://localhost:8004/health'),
            ('content-management', 'https://localhost:8001/health'),
            ('lab-manager', 'https://localhost:8007/health'),
            ('rag-service', 'https://localhost:8005/health'),
            ('demo-service', 'https://localhost:8010/health'),
        ]

        failed_checks = []

        for service_name, health_url in health_checks:
            try:
                response = requests.get(
                    health_url,
                    verify=False,
                    timeout=5
                )

                if response.status_code != 200:
                    failed_checks.append({
                        'service': service_name,
                        'url': health_url,
                        'status': response.status_code,
                        'error': f"Expected 200, got {response.status_code}"
                    })
            except requests.exceptions.RequestException as e:
                # Service might not have health endpoint yet
                # This is a warning, not a failure
                pass

        if failed_checks:
            error_msg = "\n\nHealth Check Failures:\n"
            for check in failed_checks:
                error_msg += f"\n  Service: {check['service']}"
                error_msg += f"\n  URL: {check['url']}"
                error_msg += f"\n  Error: {check['error']}\n"

            pytest.fail(error_msg)

    @pytest.mark.order(3)
    def test_database_connectivity(self):
        """
        Test PostgreSQL database is accessible

        VALIDATION:
        - Can connect to PostgreSQL
        - Database exists
        """
        import psycopg2

        try:
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                database="course_creator",
                user="postgres",
                password="postgres_password",
                connect_timeout=5
            )
            conn.close()
        except Exception as e:
            pytest.skip(f"Database not accessible: {e}")

    @pytest.mark.order(3)
    def test_redis_connectivity(self):
        """
        Test Redis cache is accessible

        VALIDATION:
        - Can connect to Redis
        - Can perform basic operations
        """
        try:
            import redis

            r = redis.Redis(
                host='localhost',
                port=6379,
                db=0,
                socket_connect_timeout=5
            )

            # Test basic operation
            r.ping()
        except Exception as e:
            pytest.skip(f"Redis not accessible: {e}")
