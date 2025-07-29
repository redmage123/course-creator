"""
Test utilities for handling imports from services with hyphens in their names
"""
import importlib
import sys
from pathlib import Path

def add_service_to_path(service_name: str):
    """
    Add a service directory to sys.path to enable direct imports
    
    Args:
        service_name: Name of service (e.g., 'course-management')
    """
    service_dir = Path(__file__).parent.parent / 'services' / service_name
    if str(service_dir) not in sys.path:
        sys.path.insert(0, str(service_dir))

def import_from_service(service_name: str, module_path: str):
    """
    Import a module from a service with hyphens in the name
    
    Args:
        service_name: Name of service (e.g., 'course-management')
        module_path: Path within service (e.g., 'infrastructure.container')
    
    Returns:
        The imported module
    """
    # Add the service directory to Python path
    add_service_to_path(service_name)
    
    # Import the module directly
    return importlib.import_module(module_path)

def import_class_from_service(service_name: str, module_path: str, class_name: str):
    """
    Import a specific class from a service with hyphens in the name
    
    Args:
        service_name: Name of service (e.g., 'course-management')
        module_path: Path within service (e.g., 'infrastructure.container')
        class_name: Name of class to import (e.g., 'Container')
    
    Returns:
        The imported class
    """
    module = import_from_service(service_name, module_path)
    return getattr(module, class_name)