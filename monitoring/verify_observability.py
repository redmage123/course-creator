#!/usr/bin/env python3
"""
Observability Verification Script

This script verifies that the observability infrastructure is properly configured:
1. Checks that Prometheus configuration is valid
2. Verifies Grafana provisioning files exist
3. Tests structured logging module
4. Validates monitoring directory structure

Usage:
    python3 monitoring/verify_observability.py
"""

import os
import sys
import yaml
import json
from pathlib import Path


def print_status(message: str, success: bool):
    """Print colored status message."""
    if success:
        print(f"✅ {message}")
    else:
        print(f"❌ {message}")


def verify_prometheus_config():
    """Verify Prometheus configuration file."""
    print("\n📊 Verifying Prometheus Configuration...")

    config_path = Path(__file__).parent / "prometheus.yml"

    if not config_path.exists():
        print_status("prometheus.yml not found", False)
        return False

    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        # Check required sections
        required_sections = ['global', 'scrape_configs']
        for section in required_sections:
            if section not in config:
                print_status(f"Missing required section: {section}", False)
                return False

        # Count scrape jobs
        jobs = config.get('scrape_configs', [])
        print_status(f"Found {len(jobs)} scrape job configurations", True)

        # List services
        services = [job.get('job_name') for job in jobs]
        print(f"   Configured services: {', '.join(services)}")

        return True

    except yaml.YAMLError as e:
        print_status(f"Invalid YAML in prometheus.yml: {e}", False)
        return False
    except Exception as e:
        print_status(f"Error reading prometheus.yml: {e}", False)
        return False


def verify_grafana_config():
    """Verify Grafana provisioning configuration."""
    print("\n📈 Verifying Grafana Configuration...")

    base_path = Path(__file__).parent / "grafana"

    # Check provisioning directory structure
    required_dirs = [
        base_path / "provisioning" / "datasources",
        base_path / "provisioning" / "dashboards",
        base_path / "dashboards"
    ]

    all_exist = True
    for dir_path in required_dirs:
        exists = dir_path.exists()
        print_status(f"Directory exists: {dir_path.relative_to(base_path.parent)}", exists)
        all_exist = all_exist and exists

    # Check datasource configuration
    datasource_file = base_path / "provisioning" / "datasources" / "prometheus.yml"
    if datasource_file.exists():
        try:
            with open(datasource_file, 'r') as f:
                datasource_config = yaml.safe_load(f)
            print_status("Prometheus datasource configuration valid", True)
        except Exception as e:
            print_status(f"Invalid datasource config: {e}", False)
            all_exist = False
    else:
        print_status("Prometheus datasource configuration missing", False)
        all_exist = False

    # Check dashboard provisioning
    dashboard_prov_file = base_path / "provisioning" / "dashboards" / "default.yml"
    if dashboard_prov_file.exists():
        try:
            with open(dashboard_prov_file, 'r') as f:
                dashboard_config = yaml.safe_load(f)
            print_status("Dashboard provisioning configuration valid", True)
        except Exception as e:
            print_status(f"Invalid dashboard provisioning config: {e}", False)
            all_exist = False
    else:
        print_status("Dashboard provisioning configuration missing", False)
        all_exist = False

    # Check for dashboard files
    dashboards_dir = base_path / "dashboards"
    if dashboards_dir.exists():
        dashboards = list(dashboards_dir.glob("*.json"))
        print_status(f"Found {len(dashboards)} dashboard(s)", len(dashboards) > 0)
        for dashboard in dashboards:
            try:
                with open(dashboard, 'r') as f:
                    json.load(f)
                print(f"   ✓ {dashboard.name} is valid JSON")
            except json.JSONDecodeError as e:
                print(f"   ✗ {dashboard.name} has invalid JSON: {e}")
                all_exist = False

    return all_exist


def verify_observability_module():
    """Verify structured logging module."""
    print("\n📝 Verifying Observability Module...")

    shared_path = Path(__file__).parent.parent / "shared"
    module_path = shared_path / "observability.py"

    if not module_path.exists():
        print_status("observability.py not found in shared/", False)
        return False

    print_status("observability.py exists", True)

    # Try to import and check exports
    sys.path.insert(0, str(shared_path.parent))

    try:
        from shared.observability import (
            setup_logging,
            get_logger,
            track_operation,
            log_request,
            set_correlation_id,
            generate_correlation_id
        )
        print_status("All required functions can be imported", True)

        # Test basic functionality
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")

            # Setup logging
            setup_logging(
                service_name="test-service",
                log_level="INFO",
                log_file=log_file,
                enable_console=False,
                enable_json=True
            )

            # Get logger
            logger = get_logger(__name__)

            # Log a test message
            logger.info("Test message", extra={'extra_fields': {'test': True}})

            # Check log file was created
            if os.path.exists(log_file):
                print_status("Structured logging writes to file successfully", True)

                # Check log format
                with open(log_file, 'r') as f:
                    log_line = f.readline()
                    try:
                        log_entry = json.loads(log_line)
                        required_fields = ['timestamp', 'level', 'logger', 'message', 'service']
                        has_all_fields = all(field in log_entry for field in required_fields)
                        print_status("Log entries are properly formatted JSON", has_all_fields)
                    except json.JSONDecodeError:
                        print_status("Log entries are not valid JSON", False)
                        return False
            else:
                print_status("Structured logging failed to create log file", False)
                return False

        return True

    except ImportError as e:
        print_status(f"Failed to import observability module: {e}", False)
        return False
    except Exception as e:
        print_status(f"Error testing observability module: {e}", False)
        return False


def verify_docker_compose():
    """Verify docker-compose.yml contains monitoring services."""
    print("\n🐳 Verifying Docker Compose Configuration...")

    compose_path = Path(__file__).parent.parent / "docker-compose.yml"

    if not compose_path.exists():
        print_status("docker-compose.yml not found", False)
        return False

    try:
        with open(compose_path, 'r') as f:
            compose_config = yaml.safe_load(f)

        services = compose_config.get('services', {})

        # Check for monitoring services
        monitoring_services = ['prometheus', 'grafana']
        all_present = True

        for service in monitoring_services:
            if service in services:
                print_status(f"{service} service configured", True)

                # Check ports
                service_config = services[service]
                if 'ports' in service_config:
                    ports = service_config['ports']
                    print(f"   Ports: {', '.join(ports)}")
            else:
                print_status(f"{service} service not found", False)
                all_present = False

        # Check for volumes
        volumes = compose_config.get('volumes', {})
        required_volumes = ['prometheus_data', 'grafana_data']

        for volume in required_volumes:
            if volume in volumes:
                print_status(f"{volume} volume configured", True)
            else:
                print_status(f"{volume} volume not found", False)
                all_present = False

        return all_present

    except yaml.YAMLError as e:
        print_status(f"Invalid YAML in docker-compose.yml: {e}", False)
        return False
    except Exception as e:
        print_status(f"Error reading docker-compose.yml: {e}", False)
        return False


def verify_directory_structure():
    """Verify monitoring directory structure."""
    print("\n📁 Verifying Directory Structure...")

    base_path = Path(__file__).parent

    required_paths = [
        base_path / "prometheus.yml",
        base_path / "grafana" / "provisioning" / "datasources",
        base_path / "grafana" / "provisioning" / "dashboards",
        base_path / "grafana" / "dashboards",
        base_path / "examples",
        base_path / "README.md"
    ]

    all_exist = True
    for path in required_paths:
        exists = path.exists()
        relative_path = path.relative_to(base_path.parent)
        print_status(f"{relative_path} exists", exists)
        all_exist = all_exist and exists

    return all_exist


def main():
    """Run all verification checks."""
    print("=" * 70)
    print("Course Creator Platform - Observability Verification")
    print("=" * 70)

    results = {
        "Directory Structure": verify_directory_structure(),
        "Prometheus Config": verify_prometheus_config(),
        "Grafana Config": verify_grafana_config(),
        "Observability Module": verify_observability_module(),
        "Docker Compose": verify_docker_compose()
    }

    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)

    for check, result in results.items():
        print_status(f"{check}: {'PASSED' if result else 'FAILED'}", result)

    all_passed = all(results.values())

    if all_passed:
        print("\n✅ All verification checks passed!")
        print("\nNext steps:")
        print("1. Start monitoring services: docker-compose up -d prometheus grafana")
        print("2. Access Prometheus: http://localhost:9090")
        print("3. Access Grafana: http://localhost:3002 (admin/admin)")
        print("4. Integrate observability.py into your services")
        return 0
    else:
        print("\n❌ Some verification checks failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
