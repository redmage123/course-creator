import pytest
from services.service_registry.registry import ServiceRegistry

def test_service_registration():
    registry = ServiceRegistry()
    registry.register_service('test-service', 'localhost', 8000)
    service = registry.get_service('test-service')
    assert service['host'] == 'localhost'
    assert service['port'] == 8000