"""
Course Generator Namespace Exceptions

TECHNICAL NOTE:
This module re-exports URL-related exceptions from the service root exceptions.py
to provide a properly namespaced import path. This uses importlib.util to explicitly
load from the correct file path, preventing import collisions when running tests
with all services in sys.path.

USAGE:
```python
from course_generator.exceptions import URLValidationException, URLConnectionException
```
"""

import importlib.util
from pathlib import Path

# Get the absolute path to the service's exceptions.py
_service_root = Path(__file__).parent.parent
_exceptions_path = _service_root / "exceptions.py"

# Load the exceptions module from the explicit file path
_spec = importlib.util.spec_from_file_location("cg_exceptions", _exceptions_path)
_exceptions_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_exceptions_module)

# Re-export all URL-related exceptions
URLFetchException = _exceptions_module.URLFetchException
URLValidationException = _exceptions_module.URLValidationException
URLConnectionException = _exceptions_module.URLConnectionException
URLTimeoutException = _exceptions_module.URLTimeoutException
URLAccessDeniedException = _exceptions_module.URLAccessDeniedException
URLNotFoundException = _exceptions_module.URLNotFoundException
ContentParsingException = _exceptions_module.ContentParsingException
HTMLParsingException = _exceptions_module.HTMLParsingException
ContentExtractionException = _exceptions_module.ContentExtractionException
ContentTooLargeException = _exceptions_module.ContentTooLargeException
UnsupportedContentTypeException = _exceptions_module.UnsupportedContentTypeException
RobotsDisallowedException = _exceptions_module.RobotsDisallowedException
CourseCreatorBaseException = _exceptions_module.CourseCreatorBaseException
RAGException = _exceptions_module.RAGException
AIServiceException = _exceptions_module.AIServiceException

# Alias for backwards compatibility
CourseGeneratorException = CourseCreatorBaseException

__all__ = [
    'URLFetchException',
    'URLValidationException',
    'URLConnectionException',
    'URLTimeoutException',
    'URLAccessDeniedException',
    'URLNotFoundException',
    'ContentParsingException',
    'HTMLParsingException',
    'ContentExtractionException',
    'ContentTooLargeException',
    'UnsupportedContentTypeException',
    'RobotsDisallowedException',
    'CourseCreatorBaseException',
    'CourseGeneratorException',
    'RAGException',
    'AIServiceException',
]
