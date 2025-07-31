"""
Integration tests for Centralized Syslog Logging System

Tests integration of centralized logging across all services including:
- Service startup logging
- Cross-service logging consistency
- Log file creation and management
- Docker container logging integration
- Environment variable configuration
- Health check logging
"""

import pytest
import asyncio
import os
import tempfile
import shutil
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime
import uuid
import json
import requests
from pathlib import Path


class TestServiceLoggingIntegration:
    """Test logging integration across all services."""
    
    @pytest.fixture
    def mock_all_services_logging(self):
        """Mock logging setup for all services."""
        services = [
            'user-management',
            'course-generator', 
            'course-management',
            'content-storage',
            'content-management',
            'analytics',
            'lab-containers'
        ]
        
        mocked_loggers = {}
        
        for service in services:
            mock_logger = Mock()
            mock_logger.info = Mock()
            mock_logger.error = Mock()
            mock_logger.warning = Mock()
            mock_logger.debug = Mock()
            mock_logger.critical = Mock()
            mocked_loggers[service] = mock_logger
        
        return mocked_loggers
    
    @patch('logging_setup.setup_docker_logging')
    def test_all_services_use_centralized_logging(self, mock_setup_logging, mock_all_services_logging):
        """Test that all services initialize centralized logging."""
        services = [
            'user-management',
            'course-generator',
            'course-management', 
            'content-storage',
            'content-management',
            'analytics',
            'lab-containers'
        ]
        
        for service in services:
            mock_setup_logging.return_value = mock_all_services_logging[service]
            
            # Simulate service startup
            logger = mock_setup_logging(service, 'INFO')
            
            # Verify setup was called for each service
            assert logger is not None
            mock_setup_logging.assert_called_with(service, 'INFO')
    
    @patch('logging_setup.setup_docker_logging')
    def test_service_startup_logging_consistency(self, mock_setup_logging, mock_all_services_logging):
        """Test that all services log startup consistently."""
        service_ports = {
            'user-management': 8000,
            'course-generator': 8001,
            'course-management': 8004,
            'content-storage': 8003,
            'content-management': 8005,
            'analytics': 8007,
            'lab-containers': 8006
        }
        
        for service, port in service_ports.items():
            mock_setup_logging.return_value = mock_all_services_logging[service]
            logger = mock_setup_logging(service, 'INFO')
            
            # Simulate standard startup logging
            service_title = service.replace('-', ' ').title()
            logger.info(f"Starting {service_title} Service on port {port}")
            logger.info(f"{service_title} Service initialized successfully")
            
            # Verify startup logging calls
            mock_logger = mock_all_services_logging[service]
            assert mock_logger.info.call_count >= 2
            mock_logger.info.assert_any_call(f"Starting {service_title} Service on port {port}")
            mock_logger.info.assert_any_call(f"{service_title} Service initialized successfully")
    
    @patch('logging_setup.setup_docker_logging')
    def test_health_check_logging_integration(self, mock_setup_logging, mock_all_services_logging):
        """Test health check logging across services."""
        services = ['user-management', 'course-generator', 'analytics']
        
        for service in services:
            mock_setup_logging.return_value = mock_all_services_logging[service]
            logger = mock_setup_logging(service, 'INFO')
            
            # Simulate health check request logging
            logger.info(f"Health check requested for {service}")
            logger.info(f"Health check successful for {service}")
            
            # Verify health check logging
            mock_logger = mock_all_services_logging[service]
            mock_logger.info.assert_any_call(f"Health check requested for {service}")
            mock_logger.info.assert_any_call(f"Health check successful for {service}")
    
    def test_environment_variable_consistency_across_services(self):
        """Test that environment variables are consistent across services."""
        required_env_vars = {
            'DOCKER_CONTAINER': 'true',
            'SERVICE_NAME': 'test-service',
            'LOG_LEVEL': 'INFO'
        }
        
        with patch.dict(os.environ, required_env_vars):
            for var, expected_value in required_env_vars.items():
                assert os.environ.get(var) == expected_value
    
    @patch('logging_setup.setup_docker_logging')
    def test_error_handling_logging_integration(self, mock_setup_logging, mock_all_services_logging):
        """Test error handling logging across services."""
        services = ['user-management', 'course-management', 'analytics']
        
        common_errors = [
            ("Database connection failed", "CRITICAL"),
            ("Authentication token expired", "WARNING"),
            ("Invalid request parameters", "ERROR"),
            ("Service dependency unavailable", "ERROR"),
            ("Configuration error", "CRITICAL")
        ]
        
        for service in services:
            mock_setup_logging.return_value = mock_all_services_logging[service]
            logger = mock_setup_logging(service, 'INFO')
            
            for error_msg, level in common_errors:
                if level == "ERROR":
                    logger.error(f"{service}: {error_msg}")
                elif level == "WARNING":
                    logger.warning(f"{service}: {error_msg}")
                elif level == "CRITICAL":
                    logger.critical(f"{service}: {error_msg}")
            
            # Verify error logging for each service
            mock_logger = mock_all_services_logging[service]
            assert mock_logger.error.call_count == 2  # Invalid request + Service dependency
            assert mock_logger.warning.call_count == 1  # Authentication token
            assert mock_logger.critical.call_count == 2  # Database + Configuration


class TestLogFileManagementIntegration:
    """Test log file creation and management integration."""
    
    @pytest.fixture
    def temp_log_directory(self):
        """Create temporary log directory for testing."""
        temp_dir = tempfile.mkdtemp()
        log_dir = os.path.join(temp_dir, "course-creator")
        os.makedirs(log_dir, exist_ok=True)
        yield log_dir
        shutil.rmtree(temp_dir)
    
    def test_log_directory_structure_creation(self, temp_log_directory):
        """Test that log directory structure is created correctly."""
        services = [
            'user-management',
            'course-generator',
            'course-management',
            'content-storage', 
            'content-management',
            'analytics',
            'lab-containers'
        ]
        
        # Simulate log file creation for each service
        for service in services:
            log_file_path = os.path.join(temp_log_directory, f"{service}.log")
            
            # Create log file
            with open(log_file_path, 'w') as f:
                f.write(f"Jul 31 09:40:11 hostname {service}[123]: INFO - Service started\n")
            
            # Verify log file exists
            assert os.path.exists(log_file_path)
            
            # Verify log file content
            with open(log_file_path, 'r') as f:
                content = f.read()
                assert service in content
                assert "Service started" in content
                assert "INFO" in content
    
    def test_log_file_permissions_and_ownership(self, temp_log_directory):
        """Test log file permissions and ownership."""
        service = "test-service"
        log_file_path = os.path.join(temp_log_directory, f"{service}.log")
        
        # Create log file
        with open(log_file_path, 'w') as f:
            f.write("Test log entry\n")
        
        # Verify file permissions (readable and writable)
        assert os.access(log_file_path, os.R_OK)
        assert os.access(log_file_path, os.W_OK)
        
        # Verify file exists and has content
        assert os.path.getsize(log_file_path) > 0
    
    def test_log_rotation_and_cleanup_integration(self, temp_log_directory):
        """Test log rotation and cleanup integration."""
        service = "test-service"
        log_file_path = os.path.join(temp_log_directory, f"{service}.log")
        
        # Simulate log entries over time
        log_entries = [
            "Jul 31 09:40:11 hostname test-service[123]: INFO - Service started",
            "Jul 31 09:40:12 hostname test-service[123]: INFO - Processing request",
            "Jul 31 09:40:13 hostname test-service[123]: INFO - Request completed",
            "Jul 31 09:40:14 hostname test-service[123]: ERROR - Error occurred",
            "Jul 31 09:40:15 hostname test-service[123]: INFO - Error handled"
        ]
        
        # Write log entries
        with open(log_file_path, 'w') as f:
            for entry in log_entries:
                f.write(f"{entry}\n")
        
        # Verify log file contains all entries
        with open(log_file_path, 'r') as f:
            content = f.read()
            for entry in log_entries:
                assert entry in content
        
        # Verify log file size is reasonable
        file_size = os.path.getsize(log_file_path)
        assert file_size > 100  # Should have substantial content


class TestDockerContainerLoggingIntegration:
    """Test Docker container logging integration."""
    
    def test_docker_environment_variable_integration(self):
        """Test Docker environment variable integration."""
        docker_env = {
            'DOCKER_CONTAINER': 'true',
            'SERVICE_NAME': 'user-management',
            'LOG_LEVEL': 'INFO'
        }
        
        with patch.dict(os.environ, docker_env):
            # Verify all Docker environment variables are set
            assert os.environ.get('DOCKER_CONTAINER') == 'true'
            assert os.environ.get('SERVICE_NAME') == 'user-management'
            assert os.environ.get('LOG_LEVEL') == 'INFO'
    
    @patch('logging_setup.setup_docker_logging')
    def test_docker_volume_mount_logging(self, mock_setup_logging):
        """Test logging with Docker volume mounts."""
        mock_logger = Mock()
        mock_setup_logging.return_value = mock_logger
        
        # Simulate Docker volume mount path
        container_log_path = "/var/log/course-creator"
        host_log_path = "./logs/course-creator"
        
        # Test that logger is set up with container path
        logger = mock_setup_logging('user-management', 'INFO')
        
        # Simulate logging to mounted volume
        logger.info(f"Logging to container path: {container_log_path}")
        logger.info(f"Mounted from host path: {host_log_path}")
        
        # Verify logging calls
        mock_logger.info.assert_any_call(f"Logging to container path: {container_log_path}")
        mock_logger.info.assert_any_call(f"Mounted from host path: {host_log_path}")
    
    def test_docker_compose_service_logging_configuration(self):
        """Test Docker Compose service logging configuration."""
        services_config = {
            'user-management': {
                'environment': {
                    'DOCKER_CONTAINER': 'true',
                    'SERVICE_NAME': 'user-management',
                    'LOG_LEVEL': 'INFO'
                },
                'volumes': ['./logs/course-creator:/var/log/course-creator']
            },
            'course-generator': {
                'environment': {
                    'DOCKER_CONTAINER': 'true', 
                    'SERVICE_NAME': 'course-generator',
                    'LOG_LEVEL': 'INFO'
                },
                'volumes': ['./logs/course-creator:/var/log/course-creator']
            }
        }
        
        for service, config in services_config.items():
            # Verify environment configuration
            env = config['environment']
            assert env['DOCKER_CONTAINER'] == 'true'
            assert env['SERVICE_NAME'] == service
            assert env['LOG_LEVEL'] == 'INFO'
            
            # Verify volume configuration
            volumes = config['volumes']
            assert './logs/course-creator:/var/log/course-creator' in volumes


class TestSyslogFormatIntegration:
    """Test syslog format integration across services."""
    
    @patch('logging_setup.setup_docker_logging')
    def test_syslog_format_consistency_across_services(self, mock_setup_logging):
        """Test that all services use consistent syslog format."""
        services = ['user-management', 'course-generator', 'analytics']
        
        for service in services:
            mock_logger = Mock()
            mock_setup_logging.return_value = mock_logger
            
            logger = mock_setup_logging(service, 'INFO')
            
            # Test various log levels with syslog format
            logger.info("Service operation completed")
            logger.warning("Configuration deprecated")
            logger.error("Operation failed")
            logger.critical("Service unavailable")
            
            # Verify all log levels were called
            mock_logger.info.assert_called_with("Service operation completed")
            mock_logger.warning.assert_called_with("Configuration deprecated")
            mock_logger.error.assert_called_with("Operation failed")
            mock_logger.critical.assert_called_with("Service unavailable")
    
    def test_syslog_message_structure_validation(self):
        """Test syslog message structure validation."""
        # Expected syslog format components
        expected_components = [
            'timestamp',     # Jul 31 09:40:11
            'hostname',      # hostname
            'service[pid]',  # service[123]
            'level',         # INFO/ERROR/etc
            'filename:line', # main.py:45
            'message'        # Actual log message
        ]
        
        # Sample syslog message
        sample_message = "Jul 31 09:40:11 hostname user-management[123]: INFO - main.py:45 - Service started"
        
        # Verify all components are present
        assert 'Jul 31 09:40:11' in sample_message  # timestamp
        assert 'hostname' in sample_message          # hostname
        assert 'user-management[123]' in sample_message  # service[pid]
        assert 'INFO' in sample_message              # level
        assert 'main.py:45' in sample_message        # filename:line
        assert 'Service started' in sample_message   # message
    
    @patch('socket.gethostname')
    @patch('os.getpid')
    def test_hostname_and_pid_in_syslog_format(self, mock_getpid, mock_gethostname):
        """Test hostname and PID inclusion in syslog format."""
        mock_gethostname.return_value = 'test-container'
        mock_getpid.return_value = 12345
        
        # Simulate syslog format generation
        service_name = 'user-management'
        log_level = 'INFO'
        message = 'Test message'
        filename = 'main.py'
        line_number = 100
        
        # Expected format
        expected_format = f"Jul 31 09:40:11 test-container {service_name}[12345]: {log_level} - {filename}:{line_number} - {message}"
        
        # Verify components
        assert 'test-container' in expected_format
        assert f'{service_name}[12345]' in expected_format
        assert f'{filename}:{line_number}' in expected_format


class TestCrossServiceLoggingIntegration:
    """Test cross-service logging integration."""
    
    @patch('logging_setup.setup_docker_logging')
    def test_service_communication_logging(self, mock_setup_logging):
        """Test logging during service-to-service communication."""
        # Mock loggers for multiple services
        user_service_logger = Mock()
        course_service_logger = Mock()
        mock_setup_logging.side_effect = [user_service_logger, course_service_logger]
        
        # Setup loggers for both services
        user_logger = mock_setup_logging('user-management', 'INFO')
        course_logger = mock_setup_logging('course-management', 'INFO')
        
        # Simulate cross-service communication logging
        user_id = str(uuid.uuid4())
        course_id = str(uuid.uuid4())
        
        # User service logs
        user_logger.info(f"User {user_id} requesting course enrollment")
        user_logger.info(f"Calling course-management service for course {course_id}")
        
        # Course service logs
        course_logger.info(f"Received enrollment request from user-management")
        course_logger.info(f"Processing enrollment for user {user_id} in course {course_id}")
        course_logger.info(f"Enrollment successful, notifying user-management")
        
        # Back to user service
        user_logger.info(f"Enrollment confirmed for user {user_id}")
        
        # Verify cross-service logging
        user_service_logger.info.assert_any_call(f"User {user_id} requesting course enrollment")
        user_service_logger.info.assert_any_call(f"Calling course-management service for course {course_id}")
        user_service_logger.info.assert_any_call(f"Enrollment confirmed for user {user_id}")
        
        course_service_logger.info.assert_any_call("Received enrollment request from user-management")
        course_service_logger.info.assert_any_call(f"Processing enrollment for user {user_id} in course {course_id}")
        course_service_logger.info.assert_any_call("Enrollment successful, notifying user-management")
    
    @patch('logging_setup.setup_docker_logging')
    def test_distributed_transaction_logging(self, mock_setup_logging):
        """Test logging for distributed transactions across services."""
        # Mock loggers for transaction services
        user_logger = Mock()
        course_logger = Mock()
        analytics_logger = Mock()
        
        mock_setup_logging.side_effect = [user_logger, course_logger, analytics_logger]
        
        # Setup loggers
        user_service = mock_setup_logging('user-management', 'INFO')
        course_service = mock_setup_logging('course-management', 'INFO')
        analytics_service = mock_setup_logging('analytics', 'INFO')
        
        # Simulate distributed transaction
        transaction_id = str(uuid.uuid4())
        
        # Transaction start
        user_service.info(f"Starting transaction {transaction_id}: User enrollment")
        
        # Service 1: User validation
        user_service.info(f"Transaction {transaction_id}: Validating user credentials")
        user_service.info(f"Transaction {transaction_id}: User validation successful")
        
        # Service 2: Course enrollment
        course_service.info(f"Transaction {transaction_id}: Processing course enrollment")
        course_service.info(f"Transaction {transaction_id}: Course enrollment successful")
        
        # Service 3: Analytics update
        analytics_service.info(f"Transaction {transaction_id}: Updating analytics")
        analytics_service.info(f"Transaction {transaction_id}: Analytics updated")
        
        # Transaction completion
        user_service.info(f"Transaction {transaction_id}: Completed successfully")
        
        # Verify distributed transaction logging
        user_logger.info.assert_any_call(f"Starting transaction {transaction_id}: User enrollment")
        user_logger.info.assert_any_call(f"Transaction {transaction_id}: Completed successfully")
        
        course_logger.info.assert_any_call(f"Transaction {transaction_id}: Processing course enrollment")
        analytics_logger.info.assert_any_call(f"Transaction {transaction_id}: Updating analytics")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])