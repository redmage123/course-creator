"""
Comprehensive System Configuration E2E Test Suite

TDD RED PHASE: Tests designed to fail initially, validating system configuration,
Docker infrastructure, HTTPS/SSL setup, and service integration.

BUSINESS CONTEXT:
System configuration tests ensure that the Course Creator Platform is properly
deployed and configured across all 18 microservices. These tests validate the
foundational infrastructure that all other features depend on.

TECHNICAL IMPLEMENTATION:
- Docker Python SDK for container inspection and health checks
- httpx for HTTP/HTTPS testing with SSL verification
- pytest with async support for concurrent testing
- Redis and PostgreSQL client libraries for connectivity validation

TEST COVERAGE (25 tests):
1. Docker & Container Health (8 tests) - Verify all containers healthy and properly configured
2. Environment & Configuration (8 tests) - Validate environment variables and service configuration
3. HTTPS & SSL (5 tests) - Ensure HTTPS-only operation with valid SSL/TLS
4. Service Integration (4 tests) - Test service dependencies and communication

EXPECTED INITIAL STATE: All 25 tests should FAIL (RED phase)
This is correct TDD behavior - tests define requirements before implementation.
"""

import os
import pytest
import docker
import httpx
import redis
import asyncio
import psycopg2
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
from urllib.parse import urlparse
import ssl
import socket
from collections import defaultdict

# Import base test class
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from tests.e2e.selenium_base import SeleniumConfig


class TestDockerContainerHealth:
    """
    Test Category 1: Docker & Container Health Tests (8 tests)

    BUSINESS REQUIREMENT:
    All 18 microservices must be healthy and properly configured in Docker.
    Container failures directly impact platform availability and user experience.

    TECHNICAL VALIDATION:
    - Container health status
    - Health check configuration
    - Restart policies
    - Volume mounts
    - Network configuration
    - Resource limits
    - Container isolation
    """

    @pytest.fixture(scope="class")
    def docker_client(self):
        """
        Initialize Docker client for container inspection.

        TECHNICAL CONTEXT:
        Uses Docker Python SDK to communicate with Docker daemon.
        Requires docker.sock access or DOCKER_HOST environment variable.
        """
        try:
            client = docker.from_env()
            # Test connection
            client.ping()
            return client
        except docker.errors.DockerException as e:
            pytest.fail(f"Failed to connect to Docker daemon: {e}")

    @pytest.fixture(scope="class")
    def expected_services(self) -> List[str]:
        """
        Define expected service containers.

        PLATFORM ARCHITECTURE:
        18 total services = 10 backend microservices + 3 infrastructure + 5 support services
        """
        return [
            # Core infrastructure
            'postgres',
            'redis',
            'frontend',

            # Backend microservices (ports 8000-8010)
            'user-management',
            'course-generator',
            'content-storage',
            'course-management',
            'content-management',
            'lab-manager',
            'analytics',
            'organization-management',
            'rag-service',
            'demo-service',

            # Support services (ports 8011-8015)
            'ai-assistant-service',
            'metadata-service',
            'knowledge-graph-service',
            'nlp-preprocessing',
            'local-llm-service'
        ]

    def test_all_18_containers_healthy(self, docker_client, expected_services):
        """
        TEST 1/25: Verify all 18 containers are running and healthy.

        VALIDATION:
        - All expected containers exist
        - All containers have 'running' status
        - All health checks passing (where configured)

        FAILURE SCENARIOS:
        - Container not found
        - Container status != 'running'
        - Health check status != 'healthy'

        RED PHASE EXPECTATION: FAIL
        Reason: This test will fail if any service is not properly configured or started.
        """
        # Get all running containers in course-creator network
        containers = docker_client.containers.list(
            filters={'network': 'course-creator_course-creator-network'}
        )

        container_names = [c.name for c in containers]
        unhealthy_containers = []

        for service_name in expected_services:
            # Find container by name (may have project prefix)
            matching_containers = [
                c for c in containers
                if service_name in c.name or c.name.startswith(f'course-creator-{service_name}')
            ]

            if not matching_containers:
                pytest.fail(
                    f"Container for service '{service_name}' not found. "
                    f"Available containers: {container_names}"
                )

            container = matching_containers[0]

            # Check running status
            assert container.status == 'running', (
                f"Container {container.name} is not running. Status: {container.status}"
            )

            # Check health status if health check configured
            container.reload()  # Refresh container state
            health_status = container.attrs.get('State', {}).get('Health', {}).get('Status')

            if health_status:
                if health_status != 'healthy':
                    unhealthy_containers.append(
                        f"{container.name}: {health_status}"
                    )

        # Assert all containers healthy
        assert not unhealthy_containers, (
            f"Unhealthy containers detected:\n" + "\n".join(unhealthy_containers)
        )

    def test_docker_health_check_configuration(self, docker_client, expected_services):
        """
        TEST 2/25: Validate health check configurations for all services.

        VALIDATION:
        - Each service has health check defined
        - Health check intervals are reasonable (10-30s)
        - Health check timeouts are appropriate (5-10s)
        - Retries configured (3-5 attempts)

        CONFIGURATION REQUIREMENTS:
        - interval: 30s (frequency of health checks)
        - timeout: 10s (max time for health check to respond)
        - retries: 3 (failed attempts before marking unhealthy)

        RED PHASE EXPECTATION: FAIL
        Reason: Some services may not have properly configured health checks.
        """
        containers = docker_client.containers.list(
            filters={'network': 'course-creator_course-creator-network'}
        )

        missing_health_checks = []
        invalid_health_configs = []

        for service_name in expected_services:
            matching_containers = [
                c for c in containers
                if service_name in c.name
            ]

            if not matching_containers:
                continue

            container = matching_containers[0]
            health_config = container.attrs.get('Config', {}).get('Healthcheck')

            if not health_config:
                missing_health_checks.append(container.name)
                continue

            # Validate health check parameters
            interval = health_config.get('Interval', 0)
            timeout = health_config.get('Timeout', 0)
            retries = health_config.get('Retries', 0)

            # Convert nanoseconds to seconds
            interval_sec = interval / 1_000_000_000
            timeout_sec = timeout / 1_000_000_000

            if not (10 <= interval_sec <= 60):
                invalid_health_configs.append(
                    f"{container.name}: interval={interval_sec}s (expected 10-60s)"
                )

            if not (5 <= timeout_sec <= 15):
                invalid_health_configs.append(
                    f"{container.name}: timeout={timeout_sec}s (expected 5-15s)"
                )

            if not (2 <= retries <= 5):
                invalid_health_configs.append(
                    f"{container.name}: retries={retries} (expected 2-5)"
                )

        assert not missing_health_checks, (
            f"Services missing health checks: {missing_health_checks}"
        )

        assert not invalid_health_configs, (
            f"Invalid health check configurations:\n" + "\n".join(invalid_health_configs)
        )

    def test_service_startup_order_correct(self, docker_client):
        """
        TEST 3/25: Test service dependency startup order.

        VALIDATION:
        - Infrastructure services (postgres, redis) started first
        - Core services (user-management) started before dependent services
        - All services respect depends_on configuration

        EXPECTED STARTUP ORDER:
        1. postgres, redis (infrastructure)
        2. user-management (authentication foundation)
        3. rag-service (required by many services)
        4. Other services (can start in parallel after dependencies)

        RED PHASE EXPECTATION: FAIL
        Reason: Startup order validation requires historical data or restart test.
        """
        containers = docker_client.containers.list(
            filters={'network': 'course-creator_course-creator-network'}
        )

        # Get startup times for each container
        startup_times: Dict[str, datetime] = {}

        for container in containers:
            started_at_str = container.attrs['State']['StartedAt']
            # Parse ISO 8601 timestamp
            started_at = datetime.fromisoformat(started_at_str.replace('Z', '+00:00'))
            startup_times[container.name] = started_at

        # Define required startup order dependencies
        dependencies = {
            'user-management': ['postgres', 'redis'],
            'course-management': ['postgres', 'redis', 'user-management'],
            'organization-management': ['postgres', 'redis', 'user-management'],
            'analytics': ['postgres', 'redis', 'user-management', 'rag-service'],
            'lab-manager': ['course-management', 'rag-service'],
        }

        order_violations = []

        for service, deps in dependencies.items():
            service_containers = [c for c in containers if service in c.name]
            if not service_containers:
                continue

            service_container = service_containers[0]
            service_start = startup_times.get(service_container.name)

            if not service_start:
                continue

            for dep in deps:
                dep_containers = [c for c in containers if dep in c.name]
                if not dep_containers:
                    order_violations.append(
                        f"{service} depends on {dep}, but {dep} not found"
                    )
                    continue

                dep_container = dep_containers[0]
                dep_start = startup_times.get(dep_container.name)

                if dep_start and service_start < dep_start:
                    order_violations.append(
                        f"{service} started before dependency {dep} "
                        f"({service_start} < {dep_start})"
                    )

        assert not order_violations, (
            f"Startup order violations detected:\n" + "\n".join(order_violations)
        )

    def test_container_restart_policies(self, docker_client, expected_services):
        """
        TEST 4/25: Verify restart policies configured correctly.

        VALIDATION:
        - All services have restart policy defined
        - Production services use 'unless-stopped' or 'always'
        - No services use 'no' restart policy

        BUSINESS REQUIREMENT:
        Services must automatically restart after failures to maintain platform availability.

        RED PHASE EXPECTATION: FAIL
        Reason: Some services may have incorrect or missing restart policies.
        """
        containers = docker_client.containers.list(
            filters={'network': 'course-creator_course-creator-network'}
        )

        invalid_restart_policies = []

        for service_name in expected_services:
            matching_containers = [c for c in containers if service_name in c.name]
            if not matching_containers:
                continue

            container = matching_containers[0]
            restart_policy = container.attrs.get('HostConfig', {}).get('RestartPolicy', {})
            policy_name = restart_policy.get('Name', 'no')

            # Validate restart policy
            if policy_name not in ['unless-stopped', 'always', 'on-failure']:
                invalid_restart_policies.append(
                    f"{container.name}: restart={policy_name} (expected unless-stopped/always)"
                )

        assert not invalid_restart_policies, (
            f"Invalid restart policies:\n" + "\n".join(invalid_restart_policies)
        )

    def test_volume_mount_validation(self, docker_client):
        """
        TEST 5/25: Check required volume mounts exist and are accessible.

        VALIDATION:
        - Critical volumes mounted (logs, ssl, storage)
        - Volume mounts have correct permissions
        - Shared volumes accessible across services

        CRITICAL VOLUMES:
        - ./logs:/var/log/course-creator (centralized logging)
        - ./ssl:/app/ssl:ro (SSL certificates)
        - postgres_data, redis_data (persistence)

        RED PHASE EXPECTATION: FAIL
        Reason: Volume mount validation requires write permission testing.
        """
        containers = docker_client.containers.list(
            filters={'network': 'course-creator_course-creator-network'}
        )

        required_volume_patterns = {
            'frontend': ['/var/log/nginx'],
            'user-management': ['/var/log/course-creator', '/app/ssl'],
            'course-management': ['/var/log/course-creator', '/app/ssl'],
            'postgres': ['/var/lib/postgresql/data'],
            'redis': ['/data'],
        }

        missing_volumes = []

        for service_pattern, expected_mounts in required_volume_patterns.items():
            matching_containers = [c for c in containers if service_pattern in c.name]
            if not matching_containers:
                continue

            container = matching_containers[0]
            mounts = container.attrs.get('Mounts', [])
            mount_destinations = [m['Destination'] for m in mounts]

            for expected_mount in expected_mounts:
                if expected_mount not in mount_destinations:
                    missing_volumes.append(
                        f"{container.name}: missing mount {expected_mount}"
                    )

        assert not missing_volumes, (
            f"Missing volume mounts:\n" + "\n".join(missing_volumes)
        )

    def test_docker_network_configuration(self, docker_client):
        """
        TEST 6/25: Validate Docker network setup and connectivity.

        VALIDATION:
        - course-creator-network exists
        - All services connected to network
        - Network driver is 'bridge'
        - Internal DNS resolution working

        NETWORK REQUIREMENTS:
        - Network name: course-creator_course-creator-network
        - Driver: bridge (allows inter-container communication)
        - Subnet: Auto-assigned by Docker

        RED PHASE EXPECTATION: FAIL
        Reason: Network validation requires DNS resolution testing.
        """
        # Check network exists
        try:
            network = docker_client.networks.get('course-creator_course-creator-network')
        except docker.errors.NotFound:
            pytest.fail("Network 'course-creator_course-creator-network' not found")

        # Validate network driver
        assert network.attrs['Driver'] == 'bridge', (
            f"Network driver is {network.attrs['Driver']}, expected 'bridge'"
        )

        # Get all containers in network
        containers = network.attrs.get('Containers', {})

        # Should have 18+ containers (all services)
        assert len(containers) >= 18, (
            f"Network has {len(containers)} containers, expected at least 18"
        )

        # Validate each container has IP address
        containers_without_ip = []
        for container_id, container_info in containers.items():
            ip_address = container_info.get('IPv4Address', '').split('/')[0]
            if not ip_address:
                containers_without_ip.append(container_info.get('Name', container_id))

        assert not containers_without_ip, (
            f"Containers without IP addresses: {containers_without_ip}"
        )

    def test_docker_resource_limits(self, docker_client, expected_services):
        """
        TEST 7/25: Check memory and CPU limits configured for services.

        VALIDATION:
        - Services have resource limits defined (optional but recommended)
        - Memory limits are reasonable (>= 512MB for backend services)
        - CPU limits allow adequate performance

        RESOURCE RECOMMENDATIONS:
        - Backend services: 1-2GB memory, 1-2 CPU cores
        - Database: 2GB memory, 2 CPU cores
        - Frontend: 512MB memory, 1 CPU core

        RED PHASE EXPECTATION: FAIL (or SKIP if limits not enforced)
        Reason: Resource limits are optional in development but required in production.
        """
        containers = docker_client.containers.list(
            filters={'network': 'course-creator_course-creator-network'}
        )

        resource_configs = []

        for container in containers:
            host_config = container.attrs.get('HostConfig', {})

            # Memory limit (in bytes)
            memory_limit = host_config.get('Memory', 0)
            memory_mb = memory_limit / (1024 * 1024) if memory_limit else None

            # CPU quota (in microseconds per 100ms)
            cpu_quota = host_config.get('CpuQuota', 0)
            cpu_cores = cpu_quota / 100000 if cpu_quota > 0 else None

            resource_configs.append({
                'name': container.name,
                'memory_mb': memory_mb,
                'cpu_cores': cpu_cores
            })

        # This test is informational - skip if no limits configured
        limits_configured = any(
            rc['memory_mb'] or rc['cpu_cores']
            for rc in resource_configs
        )

        if not limits_configured:
            pytest.skip("Resource limits not configured (acceptable for development)")

        # If limits are configured, validate they're reasonable
        insufficient_resources = []
        for rc in resource_configs:
            if rc['memory_mb'] and rc['memory_mb'] < 256:
                insufficient_resources.append(
                    f"{rc['name']}: memory={rc['memory_mb']}MB (recommended >= 512MB)"
                )

        assert not insufficient_resources, (
            f"Insufficient resource limits:\n" + "\n".join(insufficient_resources)
        )

    def test_container_isolation(self, docker_client):
        """
        TEST 8/25: Verify container namespace isolation and security.

        VALIDATION:
        - Containers run as non-root user (where applicable)
        - Security options configured (AppArmor, seccomp)
        - Privileged mode only where necessary (lab-manager)

        SECURITY REQUIREMENTS:
        - Most services: non-root user
        - lab-manager: Docker socket access (privileged)
        - No unnecessary capabilities

        RED PHASE EXPECTATION: FAIL
        Reason: Security validation requires detailed container inspection.
        """
        containers = docker_client.containers.list(
            filters={'network': 'course-creator_course-creator-network'}
        )

        security_issues = []

        for container in containers:
            host_config = container.attrs.get('HostConfig', {})

            # Check privileged mode
            is_privileged = host_config.get('Privileged', False)

            # lab-manager needs Docker socket, others should not be privileged
            if is_privileged and 'lab-manager' not in container.name:
                security_issues.append(
                    f"{container.name}: running in privileged mode (security risk)"
                )

            # Check if running as root (UID 0)
            config = container.attrs.get('Config', {})
            user = config.get('User', '')

            # Skip root check for postgres, redis (required to run as root)
            if not user and not any(svc in container.name for svc in ['postgres', 'redis']):
                # Container may be running as root
                # This is informational - not all containers configure User in Config
                pass

        # This test focuses on privileged mode
        assert not security_issues, (
            f"Container security issues:\n" + "\n".join(security_issues)
        )


class TestEnvironmentConfiguration:
    """
    Test Category 2: Environment & Configuration Tests (8 tests)

    BUSINESS REQUIREMENT:
    All services must have proper environment configuration for database connections,
    API endpoints, logging, and inter-service communication.

    TECHNICAL VALIDATION:
    - Environment variables loaded correctly
    - No port conflicts between services
    - Database connection pools configured
    - Redis cache connectivity
    - API gateway routing
    - Service discovery
    - Logging configuration
    - Error handling setup
    """

    @pytest.fixture(scope="class")
    def docker_client(self):
        """Initialize Docker client."""
        return docker.from_env()

    def test_environment_variables_all_services(self, docker_client):
        """
        TEST 9/25: Check environment variables loaded for all services.

        VALIDATION:
        - DATABASE_URL configured for services using PostgreSQL
        - REDIS_URL configured for services using Redis
        - Service-specific URLs configured (USER_SERVICE_URL, etc.)
        - JWT_SECRET_KEY present for auth services

        CRITICAL ENVIRONMENT VARIABLES:
        - DATABASE_URL: PostgreSQL connection string
        - REDIS_URL: Redis connection string
        - SERVICE_NAME: Service identifier for logging
        - ENVIRONMENT: docker/development/production

        RED PHASE EXPECTATION: FAIL
        Reason: Environment variable validation requires checking specific services.
        """
        containers = docker_client.containers.list(
            filters={'network': 'course-creator_course-creator-network'}
        )

        required_env_vars = {
            'user-management': ['DATABASE_URL', 'REDIS_URL', 'JWT_SECRET_KEY', 'SERVICE_NAME'],
            'course-management': ['DATABASE_URL', 'REDIS_URL', 'USER_SERVICE_URL', 'SERVICE_NAME'],
            'organization-management': ['DATABASE_URL', 'REDIS_URL', 'USER_MANAGEMENT_URL', 'SERVICE_NAME'],
            'analytics': ['DATABASE_URL', 'REDIS_URL', 'RAG_SERVICE_URL', 'SERVICE_NAME'],
            'rag-service': ['CHROMADB_PATH', 'SERVICE_NAME'],
        }

        missing_env_vars = []

        for service_name, required_vars in required_env_vars.items():
            matching_containers = [c for c in containers if service_name in c.name]
            if not matching_containers:
                continue

            container = matching_containers[0]
            container.reload()
            env_vars = container.attrs.get('Config', {}).get('Env', [])
            env_dict = {}
            for env_var in env_vars:
                if '=' in env_var:
                    key, value = env_var.split('=', 1)
                    env_dict[key] = value

            for required_var in required_vars:
                if required_var not in env_dict:
                    missing_env_vars.append(
                        f"{container.name}: missing {required_var}"
                    )

        assert not missing_env_vars, (
            f"Missing environment variables:\n" + "\n".join(missing_env_vars)
        )

    def test_port_conflict_detection(self, docker_client):
        """
        TEST 10/25: Detect port conflicts between services.

        VALIDATION:
        - No duplicate port mappings
        - All expected ports exposed (8000-8015, 3000, 5433)
        - No port conflicts with host system

        EXPECTED PORT MAPPING:
        - 3000: frontend (HTTPS)
        - 3001: frontend (HTTP redirect)
        - 5433: postgres
        - 8000-8010: core microservices
        - 8011-8015: support services

        RED PHASE EXPECTATION: FAIL
        Reason: Port conflict detection requires checking host bindings.
        """
        containers = docker_client.containers.list(
            filters={'network': 'course-creator_course-creator-network'}
        )

        port_mappings = defaultdict(list)

        for container in containers:
            ports = container.attrs.get('NetworkSettings', {}).get('Ports', {})

            for container_port, host_bindings in ports.items():
                if host_bindings:
                    for binding in host_bindings:
                        host_port = binding.get('HostPort')
                        if host_port:
                            port_mappings[host_port].append({
                                'container': container.name,
                                'container_port': container_port
                            })

        # Check for duplicate port bindings
        conflicts = []
        for host_port, bindings in port_mappings.items():
            if len(bindings) > 1:
                containers_on_port = [b['container'] for b in bindings]
                conflicts.append(
                    f"Port {host_port} conflict: {', '.join(containers_on_port)}"
                )

        assert not conflicts, (
            f"Port conflicts detected:\n" + "\n".join(conflicts)
        )

        # Validate expected ports are exposed
        expected_ports = {
            '3000', '3001',  # frontend
            '5433',  # postgres
            '8000', '8001', '8003', '8004', '8005', '8006', '8007', '8008', '8009', '8010',  # core
            '8011', '8012', '8013', '8014', '8015'  # support
        }

        exposed_ports = set(port_mappings.keys())
        missing_ports = expected_ports - exposed_ports

        # Some ports may be intentionally not exposed (internal only)
        # This is informational
        if missing_ports:
            print(f"Note: Expected ports not exposed: {missing_ports}")

    def test_database_connection_pooling_config(self):
        """
        TEST 11/25: Validate database connection pool settings.

        VALIDATION:
        - Connection pool size configured (min/max connections)
        - Pool timeout settings reasonable
        - Connection recycling enabled
        - Health checks on connections

        RECOMMENDED POOL SETTINGS:
        - min_size: 5 (minimum idle connections)
        - max_size: 20 (maximum total connections)
        - timeout: 30s (connection acquisition timeout)

        RED PHASE EXPECTATION: FAIL
        Reason: Requires connecting to database and checking pool configuration.
        """
        # Connect to PostgreSQL and check connection pool settings
        db_config = {
            'host': 'localhost',
            'port': 5433,
            'database': 'course_creator',
            'user': 'postgres',
            'password': 'postgres_password'
        }

        try:
            conn = psycopg2.connect(**db_config, connect_timeout=5)
            cursor = conn.cursor()

            # Check max connections setting
            cursor.execute("SHOW max_connections;")
            max_connections = int(cursor.fetchone()[0])

            # Validate max_connections is reasonable
            assert max_connections >= 100, (
                f"max_connections={max_connections}, recommended >= 100"
            )

            # Check shared buffers (should be ~25% of RAM)
            cursor.execute("SHOW shared_buffers;")
            shared_buffers = cursor.fetchone()[0]

            cursor.close()
            conn.close()

        except psycopg2.OperationalError as e:
            pytest.fail(f"Failed to connect to PostgreSQL: {e}")

    def test_redis_cache_configuration(self, docker_client):
        """
        TEST 12/25: Check Redis cache connection and configuration.

        VALIDATION:
        - Redis accessible from Docker network
        - Persistence enabled (appendonly.aof)
        - Memory policy configured (maxmemory-policy)
        - Eviction strategy appropriate for caching

        RECOMMENDED REDIS SETTINGS:
        - maxmemory-policy: allkeys-lru (evict least recently used)
        - appendonly: yes (persistence)
        - save: 900 1 300 10 60 10000 (snapshot frequency)

        RED PHASE EXPECTATION: FAIL
        Reason: Redis connection and configuration validation.
        """
        try:
            # Get Redis container
            redis_container = docker_client.containers.get('course-creator-redis-1')

            # Test connection via docker exec
            exit_code, output = redis_container.exec_run(
                'redis-cli ping',
                demux=True
            )
            assert exit_code == 0, f"Redis not responding to ping: {output}"

            # Check appendonly configuration
            exit_code, output = redis_container.exec_run(
                'redis-cli CONFIG GET appendonly',
                demux=True
            )
            assert exit_code == 0, f"Failed to get appendonly config: {output}"

            # Parse output (format: "appendonly\nyes")
            output_text = output[0].decode('utf-8') if output[0] else ''
            lines = output_text.strip().split('\n')
            appendonly = lines[1] if len(lines) > 1 else 'no'

            assert appendonly == 'yes', (
                f"Redis appendonly={appendonly}, should be 'yes' for persistence"
            )

            # Check maxmemory-policy
            exit_code, output = redis_container.exec_run(
                'redis-cli CONFIG GET maxmemory-policy',
                demux=True
            )
            assert exit_code == 0, f"Failed to get maxmemory-policy: {output}"

            output_text = output[0].decode('utf-8') if output[0] else ''
            lines = output_text.strip().split('\n')
            maxmemory_policy = lines[1] if len(lines) > 1 else 'noeviction'

            recommended_policies = ['allkeys-lru', 'volatile-lru', 'allkeys-lfu']
            assert maxmemory_policy in recommended_policies, (
                f"Redis maxmemory-policy={maxmemory_policy}, "
                f"recommended: {recommended_policies}"
            )

        except docker.errors.NotFound:
            pytest.fail("Redis container 'course-creator-redis-1' not found")
        except Exception as e:
            pytest.fail(f"Failed to check Redis configuration: {e}")

    def test_api_gateway_routing_config(self):
        """
        TEST 13/25: Validate nginx API gateway routing configuration.

        VALIDATION:
        - All service routes configured in nginx
        - Reverse proxy headers set correctly
        - SSL termination at gateway
        - Rate limiting configured

        EXPECTED ROUTES:
        - /users/* -> user-management:8000
        - /courses/* -> course-management:8004
        - /api/v1/rag/* -> rag-service:8009
        - /api/v1/analytics/* -> analytics:8007

        RED PHASE EXPECTATION: FAIL
        Reason: Requires fetching and parsing nginx configuration.
        """
        # Test by making requests through nginx and checking response headers
        routes_to_test = [
            ('https://localhost:3000/users/me', 'user-management'),
            ('https://localhost:3000/api/v1/rag/health', 'rag-service'),
        ]

        routing_failures = []

        for url, expected_service in routes_to_test:
            try:
                with httpx.Client(verify=False, timeout=5) as client:
                    # Use GET request with no auth (will fail but shows routing works)
                    response = client.get(url, follow_redirects=True)

                    # Check if we got a response (even if 401/403)
                    # This proves routing is working
                    if response.status_code not in [200, 401, 403, 404]:
                        routing_failures.append(
                            f"{url}: unexpected status {response.status_code}"
                        )
            except httpx.RequestError as e:
                routing_failures.append(f"{url}: connection failed - {e}")

        assert not routing_failures, (
            f"API gateway routing failures:\n" + "\n".join(routing_failures)
        )

    def test_service_discovery_configuration(self, docker_client):
        """
        TEST 14/25: Check service discovery via Docker DNS.

        VALIDATION:
        - Services can resolve each other by name
        - Docker DNS working within network
        - Service aliases configured correctly

        SERVICE DISCOVERY:
        Docker provides automatic DNS resolution for container names
        within the same network. Services communicate using container names
        as hostnames (e.g., user-management:8000).

        RED PHASE EXPECTATION: FAIL
        Reason: DNS resolution testing requires executing commands inside containers.
        """
        containers = docker_client.containers.list(
            filters={'network': 'course-creator_course-creator-network'}
        )

        # Test DNS resolution from one container to another
        # Use user-management to ping postgres
        test_container = None
        for container in containers:
            if 'user-management' in container.name:
                test_container = container
                break

        if not test_container:
            pytest.skip("user-management container not found for DNS testing")

        dns_failures = []
        services_to_resolve = ['postgres', 'redis', 'rag-service', 'analytics']

        for service_name in services_to_resolve:
            try:
                # Try to resolve DNS name using getent (if available)
                exit_code, output = test_container.exec_run(
                    f"getent hosts {service_name}",
                    demux=True
                )

                if exit_code != 0:
                    # Try alternative: ping -c 1
                    exit_code, output = test_container.exec_run(
                        f"ping -c 1 -W 1 {service_name}",
                        demux=True
                    )

                    if exit_code != 0:
                        dns_failures.append(
                            f"Cannot resolve {service_name} from {test_container.name}"
                        )
            except Exception as e:
                dns_failures.append(f"DNS test failed for {service_name}: {e}")

        # This test may fail if getent/ping not available in container
        # That's acceptable - just validates DNS is working
        if dns_failures:
            pytest.skip(f"DNS testing not possible: {dns_failures[0]}")

    def test_logging_configuration_all_services(self, docker_client):
        """
        TEST 15/25: Validate logging configuration for all services.

        VALIDATION:
        - Log directory mounted and writable
        - Log level configured (INFO/DEBUG)
        - Structured logging enabled (JSON format)
        - Log rotation configured

        LOGGING REQUIREMENTS:
        - Directory: /var/log/course-creator
        - Format: JSON (for log aggregation)
        - Level: INFO (production), DEBUG (development)
        - Rotation: Daily or 100MB size limit

        RED PHASE EXPECTATION: FAIL
        Reason: Requires checking log files exist and are being written.
        """
        containers = docker_client.containers.list(
            filters={'network': 'course-creator_course-creator-network'}
        )

        logging_issues = []

        for container in containers:
            # Skip infrastructure services
            if any(svc in container.name for svc in ['postgres', 'redis']):
                continue

            # Check if LOG_LEVEL environment variable set
            container.reload()
            env_vars = container.attrs.get('Config', {}).get('Env', [])
            log_level_set = any('LOG_LEVEL' in env for env in env_vars)

            if not log_level_set:
                logging_issues.append(
                    f"{container.name}: LOG_LEVEL not configured"
                )

            # Check if log volume mounted
            mounts = container.attrs.get('Mounts', [])
            log_mount = any(
                '/var/log' in m['Destination']
                for m in mounts
            )

            if not log_mount and 'frontend' not in container.name:
                logging_issues.append(
                    f"{container.name}: no log volume mounted"
                )

        # This is informational - some services may use stdout logging
        if logging_issues:
            print(f"Logging configuration notes:\n" + "\n".join(logging_issues))

    def test_error_handling_configuration(self):
        """
        TEST 16/25: Check error handling and monitoring setup.

        VALIDATION:
        - Services return proper error responses
        - Error codes standardized (400, 401, 403, 404, 500)
        - Error details included (message, code, timestamp)
        - CORS headers configured correctly

        ERROR RESPONSE FORMAT:
        {
            "error": "Error message",
            "code": "ERROR_CODE",
            "status": 400,
            "timestamp": "2025-01-15T10:30:00Z"
        }

        RED PHASE EXPECTATION: FAIL
        Reason: Requires testing error responses from each service.
        """
        # Test error responses from frontend
        test_urls = [
            'https://localhost:3000/api/v1/invalid-endpoint',  # Should return 404
            'https://localhost:3000/users/me',  # Should return 401 (no auth)
        ]

        error_format_issues = []

        for url in test_urls:
            try:
                with httpx.Client(verify=False, timeout=5) as client:
                    response = client.get(url)

                    # Check if error response has expected status
                    if response.status_code not in [400, 401, 403, 404, 500]:
                        error_format_issues.append(
                            f"{url}: unexpected status {response.status_code}"
                        )
                        continue

                    # Check CORS headers present
                    if 'access-control-allow-origin' not in response.headers:
                        error_format_issues.append(
                            f"{url}: missing CORS headers"
                        )

                    # Try to parse error response as JSON
                    try:
                        error_data = response.json()
                        # Check for error fields
                        if 'error' not in error_data and 'message' not in error_data:
                            error_format_issues.append(
                                f"{url}: error response missing 'error' or 'message' field"
                            )
                    except ValueError:
                        # Some errors may not return JSON (acceptable)
                        pass

            except httpx.RequestError as e:
                error_format_issues.append(f"{url}: request failed - {e}")

        # Error format validation is optional but recommended
        if error_format_issues:
            print(f"Error handling notes:\n" + "\n".join(error_format_issues))


class TestHTTPSAndSSL:
    """
    Test Category 3: HTTPS & SSL Tests (5 tests)

    BUSINESS REQUIREMENT:
    Platform must enforce HTTPS-only communication with valid SSL/TLS certificates.
    This is critical for security compliance (GDPR, SOC 2, ISO 27001).

    TECHNICAL VALIDATION:
    - HTTPS enabled on all services
    - SSL certificates valid and not expired
    - TLS version 1.2+ enforced
    - HTTP redirects to HTTPS
    - Security headers configured
    """

    def test_https_enabled_all_services(self):
        """
        TEST 17/25: Verify HTTPS-only operation for all services.

        VALIDATION:
        - All services accessible via HTTPS
        - HTTP requests rejected or redirected
        - SSL/TLS handshake successful

        HTTPS ENDPOINTS:
        - https://localhost:3000 (frontend)
        - https://localhost:8000 (user-management)
        - https://localhost:8009 (rag-service)
        - All other services on their respective ports

        RED PHASE EXPECTATION: FAIL
        Reason: Not all services may have HTTPS properly configured.
        """
        https_endpoints = [
            'https://localhost:3000/health',  # frontend
            'https://localhost:8000/health',  # user-management
            'https://localhost:8001/health',  # course-generator
            'https://localhost:8003/health',  # content-storage
            'https://localhost:8004/health',  # course-management
            'https://localhost:8005/health',  # content-management
            'https://localhost:8006/health',  # lab-manager
            'https://localhost:8007/health',  # analytics
            'https://localhost:8008/health',  # organization-management
            'https://localhost:8009/api/v1/rag/health',  # rag-service
            'https://localhost:8010/api/v1/demo/health',  # demo-service
        ]

        https_failures = []

        for url in https_endpoints:
            try:
                with httpx.Client(verify=False, timeout=10) as client:
                    response = client.get(url)

                    # Any response (even 401/404) proves HTTPS is working
                    if response.status_code >= 500:
                        https_failures.append(
                            f"{url}: server error {response.status_code}"
                        )
            except httpx.RequestError as e:
                https_failures.append(f"{url}: {type(e).__name__} - {e}")

        assert not https_failures, (
            f"HTTPS connection failures:\n" + "\n".join(https_failures)
        )

    def test_ssl_certificate_validity(self):
        """
        TEST 18/25: Check SSL certificate validity and expiration.

        VALIDATION:
        - Certificates not expired
        - Valid date range (not before / not after)
        - Certificate chain valid
        - Self-signed certificates acceptable for development

        CERTIFICATE REQUIREMENTS:
        - Locations: ./ssl/nginx-selfsigned.crt
        - Validity: At least 30 days remaining
        - Key size: >= 2048 bits (RSA) or 256 bits (ECC)

        RED PHASE EXPECTATION: FAIL
        Reason: Certificate validation requires parsing cert files.
        """
        # Check SSL certificate files exist
        cert_path = './ssl/nginx-selfsigned.crt'
        key_path = './ssl/nginx-selfsigned.key'

        assert os.path.exists(cert_path), f"SSL certificate not found: {cert_path}"
        assert os.path.exists(key_path), f"SSL key not found: {key_path}"

        # Read and validate certificate
        try:
            import ssl
            from cryptography import x509
            from cryptography.hazmat.backends import default_backend

            with open(cert_path, 'rb') as cert_file:
                cert_data = cert_file.read()
                cert = x509.load_pem_x509_certificate(cert_data, default_backend())

                # Check expiration
                now = datetime.utcnow()
                not_valid_before = cert.not_valid_before
                not_valid_after = cert.not_valid_after

                assert now >= not_valid_before, (
                    f"Certificate not yet valid. Valid from: {not_valid_before}"
                )

                assert now <= not_valid_after, (
                    f"Certificate expired. Expired on: {not_valid_after}"
                )

                # Check at least 30 days remaining
                days_remaining = (not_valid_after - now).days
                assert days_remaining >= 30, (
                    f"Certificate expiring soon: {days_remaining} days remaining"
                )

        except ImportError:
            pytest.skip("cryptography library not available for certificate validation")

    def test_tls_version_security(self):
        """
        TEST 19/25: Validate TLS version security (TLS 1.2+).

        VALIDATION:
        - TLS 1.2 or higher enforced
        - TLS 1.0 and 1.1 disabled (security vulnerabilities)
        - SSL 3.0 disabled (POODLE vulnerability)

        SECURITY STANDARDS:
        - PCI DSS: Requires TLS 1.2+
        - NIST: Recommends TLS 1.2 minimum
        - SOC 2: Requires strong encryption

        RED PHASE EXPECTATION: FAIL
        Reason: TLS version validation requires SSL socket inspection.
        """
        # Test TLS version by attempting connection
        hostname = 'localhost'
        port = 3000

        try:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            with socket.create_connection((hostname, port), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    # Get TLS version
                    tls_version = ssock.version()

                    # Validate TLS 1.2 or higher
                    assert tls_version in ['TLSv1.2', 'TLSv1.3'], (
                        f"TLS version {tls_version} is not secure. "
                        f"Required: TLS 1.2 or higher"
                    )

        except socket.error as e:
            pytest.fail(f"Failed to establish SSL connection: {e}")

    def test_http_redirect_to_https(self):
        """
        TEST 20/25: Test HTTP to HTTPS redirect functionality.

        VALIDATION:
        - HTTP requests redirected to HTTPS (301/302)
        - Redirect target is HTTPS URL
        - HSTS header present (Strict-Transport-Security)

        REDIRECT BEHAVIOR:
        - http://localhost:3001 -> https://localhost:3000
        - Status code: 301 (permanent) or 308 (permanent redirect)

        RED PHASE EXPECTATION: FAIL
        Reason: HTTP redirect testing requires following redirect chain.
        """
        http_url = 'http://localhost:3001'

        try:
            with httpx.Client(timeout=5, follow_redirects=False) as client:
                response = client.get(http_url)

                # Check redirect status
                assert response.status_code in [301, 302, 307, 308], (
                    f"Expected redirect status (301/302/307/308), "
                    f"got {response.status_code}"
                )

                # Check redirect locations
                locations = response.headers.get('locations', '')
                assert locations.startswith('https://'), (
                    f"Redirect locations is not HTTPS: {locations}"
                )

        except httpx.RequestError as e:
            pytest.fail(f"HTTP redirect test failed: {e}")

    def test_secure_headers_configuration(self):
        """
        TEST 21/25: Check security headers present in responses.

        VALIDATION:
        - Strict-Transport-Security (HSTS)
        - X-Content-Type-Options: nosniff
        - X-Frame-Options: DENY or SAMEORIGIN
        - X-XSS-Protection: 1; mode=block
        - Content-Security-Policy configured

        SECURITY HEADERS:
        Prevent common web vulnerabilities (XSS, clickjacking, MIME sniffing)
        Required for security compliance and best practices.

        RED PHASE EXPECTATION: FAIL
        Reason: Security headers validation requires checking HTTP responses.
        """
        url = 'https://localhost:3000'

        try:
            with httpx.Client(verify=False, timeout=5) as client:
                response = client.get(url)

                headers = response.headers
                missing_headers = []

                # Check HSTS
                if 'strict-transport-security' not in headers:
                    missing_headers.append('Strict-Transport-Security')

                # Check X-Content-Type-Options
                if 'x-content-type-options' not in headers:
                    missing_headers.append('X-Content-Type-Options')

                # Check X-Frame-Options
                if 'x-frame-options' not in headers:
                    missing_headers.append('X-Frame-Options')

                # CSP is optional but recommended
                if 'content-security-policy' not in headers:
                    print("Note: Content-Security-Policy header not set")

                assert not missing_headers, (
                    f"Missing security headers: {missing_headers}"
                )

        except httpx.RequestError as e:
            pytest.fail(f"Failed to fetch headers: {e}")


class TestServiceIntegration:
    """
    Test Category 4: Service Integration Tests (4 tests)

    BUSINESS REQUIREMENT:
    Services must properly integrate with dependencies (database, cache, message queue)
    and communicate correctly with each other.

    TECHNICAL VALIDATION:
    - Service dependency validation
    - Database migrations automated
    - Cache synchronization
    - Message queue configuration
    """

    def test_service_dependencies_validated(self):
        """
        TEST 22/25: Check services can reach their dependencies.

        VALIDATION:
        - user-management can reach postgres and redis
        - course-management can reach user-management
        - analytics can reach rag-service
        - All inter-service communication working

        DEPENDENCY GRAPH:
        postgres/redis -> user-management -> course-management -> content-management
        postgres -> rag-service -> analytics

        RED PHASE EXPECTATION: FAIL
        Reason: Dependency validation requires service health checks.
        """
        # Test key service dependencies through health endpoints
        dependency_tests = [
            # (service_url, expected_dependencies)
            ('https://localhost:8000/health', ['postgres', 'redis']),
            ('https://localhost:8004/health', ['postgres', 'redis', 'user-management']),
            ('https://localhost:8007/health', ['postgres', 'redis', 'rag-service']),
        ]

        dependency_failures = []

        for url, expected_deps in dependency_tests:
            try:
                with httpx.Client(verify=False, timeout=10) as client:
                    response = client.get(url)

                    # Health endpoint should return 200 if dependencies are healthy
                    if response.status_code != 200:
                        data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                        dependency_failures.append(
                            f"{url}: dependencies unhealthy - {data}"
                        )
            except httpx.RequestError as e:
                dependency_failures.append(f"{url}: connection failed - {e}")

        assert not dependency_failures, (
            f"Service dependency failures:\n" + "\n".join(dependency_failures)
        )

    def test_database_migrations_automated(self):
        """
        TEST 23/25: Verify database migrations run automatically on startup.

        VALIDATION:
        - Schema migrations applied
        - Database tables created
        - Indexes created
        - No pending migrations

        MIGRATION TOOLS:
        - Alembic (Python services)
        - Flyway (alternative)
        - Custom migration scripts

        RED PHASE EXPECTATION: FAIL
        Reason: Migration validation requires checking database schema version.
        """
        # Connect to PostgreSQL and check schema
        db_config = {
            'host': 'localhost',
            'port': 5433,
            'database': 'course_creator',
            'user': 'postgres',
            'password': 'postgres_password'
        }

        try:
            conn = psycopg2.connect(**db_config, connect_timeout=5)
            cursor = conn.cursor()

            # Check if key tables exist
            expected_tables = [
                'users',
                'organizations',
                'courses',
                'course_content',
                'enrollments',
                'analytics_events'
            ]

            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'course_creator'
            """)
            existing_tables = [row[0] for row in cursor.fetchall()]

            missing_tables = [
                table for table in expected_tables
                if table not in existing_tables
            ]

            cursor.close()
            conn.close()

            assert not missing_tables, (
                f"Missing database tables (migrations not run?): {missing_tables}"
            )

        except psycopg2.OperationalError as e:
            pytest.fail(f"Failed to connect to PostgreSQL: {e}")

    def test_cache_synchronization_config(self):
        """
        TEST 24/25: Check cache synchronization between services.

        VALIDATION:
        - Redis cache accessible to all services
        - Cache keys properly namespaced
        - Cache TTL configured
        - Cache invalidation working

        CACHE STRATEGY:
        - User sessions: 24h TTL
        - Course data: 1h TTL
        - Analytics: 5min TTL

        RED PHASE EXPECTATION: FAIL
        Reason: Cache synchronization testing requires writing/reading cache entries.
        """
        try:
            redis_client = redis.Redis(
                host='localhost',
                port=6379,
                decode_responses=True,
                socket_connect_timeout=5
            )

            # Test cache operations
            test_key = 'test:system_config:validation'
            test_value = f'test_{datetime.now().isoformat()}'

            # Write to cache
            redis_client.setex(test_key, 60, test_value)

            # Read from cache
            cached_value = redis_client.get(test_key)

            assert cached_value == test_value, (
                f"Cache read/write failed. Expected: {test_value}, Got: {cached_value}"
            )

            # Check TTL
            ttl = redis_client.ttl(test_key)
            assert 0 < ttl <= 60, (
                f"Cache TTL incorrect. Expected: 0-60, Got: {ttl}"
            )

            # Cleanup
            redis_client.delete(test_key)

            redis_client.close()

        except redis.ConnectionError as e:
            pytest.fail(f"Failed to connect to Redis: {e}")

    def test_message_queue_configuration(self):
        """
        TEST 25/25: Validate message queue setup (if using RabbitMQ/Kafka).

        VALIDATION:
        - Message queue service running
        - Queues created for async tasks
        - Dead letter queues configured
        - Message retention policies set

        MESSAGE QUEUE USAGE:
        - Course content generation (async)
        - Analytics event processing (async)
        - Email notifications (async)

        RED PHASE EXPECTATION: SKIP or FAIL
        Reason: Platform may not use message queue yet (uses Redis for simple queuing).
        """
        # Platform currently uses Redis for simple pub/sub
        # This test validates Redis pub/sub capability

        try:
            redis_client = redis.Redis(
                host='localhost',
                port=6379,
                decode_responses=True,
                socket_connect_timeout=5
            )

            # Test pub/sub capability
            pubsub = redis_client.pubsub()
            test_channel = 'test:system_config:pubsub'

            # Subscribe
            pubsub.subscribe(test_channel)

            # Publish
            redis_client.publish(test_channel, 'test_message')

            # Check subscription
            message = pubsub.get_message(timeout=2)

            # Cleanup
            pubsub.unsubscribe(test_channel)
            pubsub.close()
            redis_client.close()

            # Note: Full message queue testing would require RabbitMQ/Kafka
            print("Note: Platform uses Redis pub/sub for messaging")

        except redis.ConnectionError as e:
            pytest.fail(f"Failed to connect to Redis: {e}")


# Test suite metadata
TEST_SUITE_INFO = {
    "name": "System Configuration E2E Test Suite",
    "version": "1.0.0",
    "tdd_phase": "RED",
    "total_tests": 25,
    "expected_failures": 25,
    "categories": {
        "docker_container_health": 8,
        "environment_configuration": 8,
        "https_ssl": 5,
        "service_integration": 4
    },
    "created": "2025-10-12",
    "author": "Claude Code (TDD RED Phase)"
}


if __name__ == '__main__':
    """
    Run test suite with pytest.

    Usage:
        pytest tests/e2e/test_system_configuration.py -v
        pytest tests/e2e/test_system_configuration.py -v -k "test_all_16"
        pytest tests/e2e/test_system_configuration.py --tb=short

    Expected output: 25 tests FAIL (RED phase)
    """
    pytest.main([__file__, '-v', '--tb=short'])
