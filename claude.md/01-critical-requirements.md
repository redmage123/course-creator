# Critical Requirements

## 1. Python Import Requirements

**ABSOLUTE IMPORTS ONLY**: Claude Code must NEVER write relative import statements in this application. All Python imports must be absolute imports only.

**FORBIDDEN**:
```python
from ..module import something          # NEVER
from .module import something           # NEVER
from ...parent.module import something  # NEVER
```

**REQUIRED**:
```python
from module import something            # ALWAYS
from package.module import something    # ALWAYS
from services.package.module import something  # ALWAYS
```

This directive overrides all other coding conventions and must be followed without exception to prevent Docker container import failures.

## 2. Exception Handling Requirements

**CUSTOM EXCEPTIONS MANDATORY**: Never use generic `except Exception as e` handlers. Use structured custom exceptions with f-strings for error messages.

**FORBIDDEN**:
```python
try:
    # some operation
except Exception as e:  # NEVER - too generic
    print(f"Error: {e}")
```

**REQUIRED**:
```python
try:
    # some operation
except SpecificServiceError as e:  # ALWAYS - specific exceptions
    logger.error(f"Service operation failed: {e}")
except DatabaseConnectionError as e:
    logger.error(f"Database connection failed: {e}")
except ValidationError as e:
    logger.error(f"Input validation failed: {e}")
```

## 3. File Editing Efficiency

**CRITICAL**: When making multiple related edits to files, batch them up and complete them all at once instead of asking permission for each individual edit. This improves efficiency and reduces interruptions during systematic updates like:
- Adding logging configuration to multiple services
- Updating environment variables across services  
- Adding volume mounts to Docker Compose services
- Applying consistent changes across multiple files

Use MultiEdit or multiple single Edit calls in one response to complete all related changes efficiently.

## 4. File Type-Specific Comment Syntax

When adding documentation, use the appropriate comment syntax for each file type:

- **Python**: `"""multiline strings"""` for docstrings and module documentation
- **JavaScript**: `//` for single line, `/* */` for multiline
- **CSS**: `/* */` for all comments
- **HTML**: `<!-- -->` for all comments
- **YAML**: `#` for all comments
- **SQL**: `--` for single line, `/* */` for multiline
- **Bash**: `#` for all comments

## 5. Always Edit Existing Files

**NEVER create files unless they're absolutely necessary for achieving your goal. ALWAYS prefer editing an existing file to creating a new one.**

This applies especially to:
- Configuration files (prefer editing existing config over creating new)
- Documentation files (prefer editing existing docs over creating new)
- Service files (prefer editing existing services over creating new)
- Frontend files (prefer editing existing components over creating new)

---

**COMPLIANCE REQUIREMENT**: All code must adhere to these critical directives without exception.