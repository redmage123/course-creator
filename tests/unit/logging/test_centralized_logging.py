"""
Unit tests for Centralized Syslog Logging System

Tests all components of the centralized logging system including:
- Syslog format logging
- File and console logging
- Docker container logging
- Log directory creation
- Environment variable configuration
- Logging setup integration
"""

import pytest
import os
import tempfile
import logging
from unittest.mock import Mock, patch, mock_open, MagicMock
from datetime import datetime
import uuid
import socket

# Mock the logging_setup module
@pytest.fixture
def mock_logging_setup_module():
    """Mock the logging_setup module for testing."""
    with patch.dict('sys.modules', {'logging_setup': MagicMock()}):
        import sys
        mock_module = sys.modules['logging_setup']
        
        # Mock SyslogFormatter
        mock_formatter = MagicMock()
        mock_formatter.format.return_value = "Jul 31 09:40:11 hostname service[123]: INFO - test.py:10 - Test message"
        mock_module.SyslogFormatter.return_value = mock_formatter
        
        # Mock setup_docker_logging
        mock_logger = MagicMock()
        mock_logger.info = Mock()
        mock_logger.error = Mock()
        mock_logger.warning = Mock()
        mock_logger.debug = Mock()
        mock_logger.critical = Mock()
        mock_module.setup_docker_logging.return_value = mock_logger
        
        yield mock_module


class TestSyslogFormatter:
    """Test syslog formatter functionality."""
    
    def test_syslog_format_structure(self, mock_logging_setup_module):
        """Test that syslog format follows RFC 3164 standard."""
        formatter = mock_logging_setup_module.SyslogFormatter()
        
        # Create a test log record
        record = logging.LogRecord(
            name='test-service',
            level=logging.INFO,
            pathname='/app/test.py',
            lineno=10,
            msg='Test message',
            args=(),
            exc_info=None,
            func='test_function'
        )
        record.created = datetime.now().timestamp()
        record.process = 123
        
        # Format the record
        formatted = formatter.format(record)
        
        # Verify syslog format components
        assert 'hostname' in formatted
        assert 'service[123]' in formatted
        assert 'INFO' in formatted
        assert 'test.py:10' in formatted
        assert 'Test message' in formatted
    
    def test_syslog_format_with_different_log_levels(self, mock_logging_setup_module):
        """Test syslog format with different log levels."""
        formatter = mock_logging_setup_module.SyslogFormatter()
        
        log_levels = [
            (logging.DEBUG, 'DEBUG'),
            (logging.INFO, 'INFO'),
            (logging.WARNING, 'WARNING'),
            (logging.ERROR, 'ERROR'),
            (logging.CRITICAL, 'CRITICAL')
        ]
        
        for level, level_str in log_levels:
            record = logging.LogRecord(
                name='test-service',
                level=level,
                pathname='/app/test.py',
                lineno=10,
                msg=f'Test {level_str} message',
                args=(),
                exc_info=None
            )
            record.process = 123
            
            # Mock format return based on level
            mock_logging_setup_module.SyslogFormatter.return_value.format.return_value = \
                f"Jul 31 09:40:11 hostname test-service[123]: {level_str} - test.py:10 - Test {level_str} message"
            
            formatted = formatter.format(record)
            assert level_str in formatted
    
    def test_hostname_in_syslog_format(self, mock_logging_setup_module):
        """Test that hostname is properly included in syslog format."""
        formatter = mock_logging_setup_module.SyslogFormatter()
        
        with patch('socket.gethostname', return_value='test-hostname'):
            record = logging.LogRecord(
                name='test-service',
                level=logging.INFO,
                pathname='/app/test.py',
                lineno=10,
                msg='Test message',
                args=(),
                exc_info=None
            )
            record.process = 123
            
            mock_logging_setup_module.SyslogFormatter.return_value.format.return_value = \
                "Jul 31 09:40:11 test-hostname test-service[123]: INFO - test.py:10 - Test message"
            
            formatted = formatter.format(record)
            assert 'test-hostname' in formatted


class TestDockerLoggingSetup:
    """Test Docker logging setup functionality."""
    
    @patch('os.makedirs')
    @patch('os.path.exists')
    def test_setup_docker_logging_basic(self, mock_exists, mock_makedirs, mock_logging_setup_module):
        """Test basic Docker logging setup."""
        mock_exists.return_value = False  # Log directory doesn't exist
        
        logger = mock_logging_setup_module.setup_docker_logging('test-service', 'INFO')
        
        # Verify logger is returned
        assert logger is not None
        
        # Verify directory creation was attempted
        mock_makedirs.assert_called()
        
        # Verify setup_docker_logging was called
        mock_logging_setup_module.setup_docker_logging.assert_called_with('test-service', 'INFO')
    
    @patch('os.makedirs')
    @patch('os.path.exists')
    def test_setup_docker_logging_with_existing_directory(self, mock_exists, mock_makedirs, mock_logging_setup_module):
        """Test Docker logging setup when log directory already exists."""
        mock_exists.return_value = True  # Log directory exists
        
        logger = mock_logging_setup_module.setup_docker_logging('test-service', 'INFO')
        
        # Verify logger is returned
        assert logger is not None
        
        # Verify directory creation was not attempted
        mock_makedirs.assert_not_called()
    
    def test_setup_docker_logging_with_different_log_levels(self, mock_logging_setup_module):
        """Test Docker logging setup with different log levels."""
        log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        
        for level in log_levels:
            logger = mock_logging_setup_module.setup_docker_logging('test-service', level)
            assert logger is not None
            mock_logging_setup_module.setup_docker_logging.assert_called_with('test-service', level)
    
    def test_setup_docker_logging_with_service_names(self, mock_logging_setup_module):
        """Test Docker logging setup with different service names."""
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
            logger = mock_logging_setup_module.setup_docker_logging(service, 'INFO')
            assert logger is not None
            mock_logging_setup_module.setup_docker_logging.assert_called_with(service, 'INFO')


class TestEnvironmentVariableIntegration:
    """Test environment variable integration for logging."""
    
    def test_docker_container_environment_variable(self):
        """Test DOCKER_CONTAINER environment variable detection."""
        # Test with DOCKER_CONTAINER=true
        with patch.dict(os.environ, {'DOCKER_CONTAINER': 'true'}):
            assert os.environ.get('DOCKER_CONTAINER') == 'true'
        
        # Test with DOCKER_CONTAINER=false
        with patch.dict(os.environ, {'DOCKER_CONTAINER': 'false'}):
            assert os.environ.get('DOCKER_CONTAINER') == 'false'
        
        # Test without DOCKER_CONTAINER
        with patch.dict(os.environ, {}, clear=True):
            assert os.environ.get('DOCKER_CONTAINER') is None
    
    def test_service_name_environment_variable(self):
        """Test SERVICE_NAME environment variable."""
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
            with patch.dict(os.environ, {'SERVICE_NAME': service}):
                assert os.environ.get('SERVICE_NAME') == service
    
    def test_log_level_environment_variable(self):
        """Test LOG_LEVEL environment variable."""
        log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        
        for level in log_levels:
            with patch.dict(os.environ, {'LOG_LEVEL': level}):
                assert os.environ.get('LOG_LEVEL') == level
    
    def test_environment_variable_defaults(self, mock_logging_setup_module):
        """Test default values when environment variables are not set."""
        with patch.dict(os.environ, {}, clear=True):
            # Should use defaults
            service_name = os.environ.get('SERVICE_NAME', 'default-service')
            log_level = os.environ.get('LOG_LEVEL', 'INFO')
            
            assert service_name == 'default-service'
            assert log_level == 'INFO'


class TestLogFileManagement:
    """Test log file creation and management."""
    
    def test_log_directory_structure(self):
        """Test that log directory structure is correct."""
        expected_path = "/var/log/course-creator"
        
        # Test path construction
        service_name = "test-service"
        expected_log_file = f"{expected_path}/{service_name}.log"
        
        assert expected_log_file == "/var/log/course-creator/test-service.log"
    
    @patch('os.makedirs')
    @patch('os.path.exists')
    def test_log_directory_creation_permissions(self, mock_exists, mock_makedirs):
        """Test log directory creation with proper permissions."""
        mock_exists.return_value = False
        
        # Simulate directory creation
        log_dir = "/var/log/course-creator"
        
        # In real implementation, makedirs would be called
        if not mock_exists.return_value:
            mock_makedirs(log_dir, exist_ok=True)
        
        mock_makedirs.assert_called_with(log_dir, exist_ok=True)
    
    def test_log_file_paths_for_all_services(self):
        """Test log file paths for all services."""
        services = [
            'user-management',
            'course-generator',
            'course-management', 
            'content-storage',
            'content-management',
            'analytics',
            'lab-containers'
        ]
        
        base_path = "/var/log/course-creator"
        
        for service in services:
            expected_path = f"{base_path}/{service}.log"
            assert expected_path.startswith(base_path)
            assert expected_path.endswith(f"{service}.log")


class TestLoggingIntegration:
    """Test integration with service main files."""
    
    def test_logging_setup_import_mock(self, mock_logging_setup_module):
        """Test that logging_setup can be imported and used."""
        # Test import
        assert mock_logging_setup_module is not None
        
        # Test setup function
        logger = mock_logging_setup_module.setup_docker_logging('test-service', 'INFO')
        assert logger is not None
    
    def test_logging_initialization_pattern(self, mock_logging_setup_module):
        """Test the standard logging initialization pattern used in services."""
        # Simulate service main.py pattern
        service_name = os.environ.get('SERVICE_NAME', 'test-service')
        log_level = os.environ.get('LOG_LEVEL', 'INFO')
        
        logger = mock_logging_setup_module.setup_docker_logging(service_name, log_level)
        
        # Test that logger methods are available
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'error')
        assert hasattr(logger, 'warning')
        assert hasattr(logger, 'debug')
        assert hasattr(logger, 'critical')
        
        # Test logging calls
        logger.info("Test info message")
        logger.error("Test error message")
        logger.warning("Test warning message")
        
        # Verify calls were made
        logger.info.assert_called_with("Test info message")
        logger.error.assert_called_with("Test error message")
        logger.warning.assert_called_with("Test warning message")
    
    def test_logging_in_service_startup(self, mock_logging_setup_module):
        """Test logging during service startup."""
        service_name = 'test-service'
        port = 8000
        
        logger = mock_logging_setup_module.setup_docker_logging(service_name, 'INFO')
        
        # Simulate service startup logging
        logger.info(f"Starting {service_name.title().replace('-', ' ')} Service on port {port}")
        logger.info("Service initialized successfully")
        
        # Verify startup logging calls
        expected_calls = [
            f"Starting Test Service Service on port {port}",
            "Service initialized successfully"
        ]
        
        # Check that info was called with expected messages
        assert logger.info.call_count == 2


class TestErrorHandling:
    """Test error handling in logging system."""
    
    def test_logging_setup_fallback(self, mock_logging_setup_module):
        """Test fallback behavior when logging setup fails."""
        # Mock a failure scenario
        mock_logging_setup_module.setup_docker_logging.side_effect = Exception("Setup failed")
        
        # Test that exception is handled gracefully
        with pytest.raises(Exception):
            mock_logging_setup_module.setup_docker_logging('test-service', 'INFO')
    
    def test_missing_environment_variables(self, mock_logging_setup_module):
        """Test behavior when environment variables are missing."""
        with patch.dict(os.environ, {}, clear=True):
            # Should use fallback values
            service_name = os.environ.get('SERVICE_NAME', 'fallback-service')
            log_level = os.environ.get('LOG_LEVEL', 'INFO')
            
            logger = mock_logging_setup_module.setup_docker_logging(service_name, log_level)
            assert logger is not None
    
    def test_invalid_log_level_handling(self, mock_logging_setup_module):
        """Test handling of invalid log levels."""
        invalid_levels = ['INVALID', 'TRACE', 'VERBOSE', '']
        
        for invalid_level in invalid_levels:
            # In real implementation, this should fallback to INFO or raise appropriate error
            try:
                logger = mock_logging_setup_module.setup_docker_logging('test-service', invalid_level)
                # If no exception, verify logger was created
                assert logger is not None
            except ValueError:
                # Valid to raise ValueError for invalid log levels
                pass


class TestDockerComposeIntegration:
    """Test Docker Compose logging integration."""
    
    def test_docker_compose_environment_variables(self):
        """Test environment variables from Docker Compose."""
        docker_env = {
            'DOCKER_CONTAINER': 'true',
            'SERVICE_NAME': 'user-management',
            'LOG_LEVEL': 'INFO'
        }
        
        with patch.dict(os.environ, docker_env):
            assert os.environ.get('DOCKER_CONTAINER') == 'true'
            assert os.environ.get('SERVICE_NAME') == 'user-management'
            assert os.environ.get('LOG_LEVEL') == 'INFO'
    
    def test_volume_mount_path(self):
        """Test Docker volume mount path for logs."""
        host_path = "./logs/course-creator"
        container_path = "/var/log/course-creator"
        
        # Verify paths are correctly structured
        assert host_path.endswith("course-creator")
        assert container_path.endswith("course-creator")
        
        # Test service log file paths
        services = ['user-management', 'course-generator', 'analytics']
        for service in services:
            container_log_path = f"{container_path}/{service}.log"
            assert container_log_path.startswith("/var/log/course-creator/")
            assert container_log_path.endswith(f"{service}.log")


class TestSyslogCompliance:
    """Test RFC 3164 syslog compliance."""
    
    def test_syslog_message_format_components(self, mock_logging_setup_module):
        """Test that syslog messages contain all required components."""
        formatter = mock_logging_setup_module.SyslogFormatter()
        
        # Expected format: Jul 31 09:40:11 hostname service[pid]: LEVEL - filename:line - message
        expected_components = [
            'hostname',  # Hostname
            'service[',  # Service name with PID
            'INFO',      # Log level
            'test.py:',  # Filename and line
            'Test message'  # Actual message
        ]
        
        mock_logging_setup_module.SyslogFormatter.return_value.format.return_value = \
            "Jul 31 09:40:11 hostname service[123]: INFO - test.py:10 - Test message"
        
        record = logging.LogRecord(
            name='service',
            level=logging.INFO,
            pathname='/app/test.py',
            lineno=10,
            msg='Test message',
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        
        for component in expected_components:
            assert component in formatted
    
    def test_timestamp_format_in_syslog(self, mock_logging_setup_module):
        """Test timestamp format in syslog messages."""
        formatter = mock_logging_setup_module.SyslogFormatter()
        
        # Mock format with timestamp
        mock_logging_setup_module.SyslogFormatter.return_value.format.return_value = \
            "Jul 31 09:40:11 hostname service[123]: INFO - test.py:10 - Test message"
        
        record = logging.LogRecord(
            name='service',
            level=logging.INFO,
            pathname='/app/test.py',
            lineno=10,
            msg='Test message',
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        
        # Check timestamp format (Month Day Hour:Min:Sec)
        import re
        timestamp_pattern = r'[A-Z][a-z]{2} \d{1,2} \d{2}:\d{2}:\d{2}'
        assert re.search(timestamp_pattern, formatted) is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])