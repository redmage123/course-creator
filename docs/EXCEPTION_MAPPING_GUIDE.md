# Exception Mapping Guide for Course Creator Platform

## Overview

This guide provides the definitive mapping from generic `except Exception` handlers to specific custom exceptions. The Course Creator platform has **200+ files with generic exception handlers** that violate CLAUDE.md requirements. This document shows exactly which specific exceptions to catch instead.

**Critical Requirement**: All code must use specific exception types from `shared.exceptions` module instead of generic `except Exception` patterns.

**Custom Exception Classes Available**: See `/home/bbrelin/course-creator/shared/exceptions.py` and `/home/bbrelin/course-creator/shared/exceptions/__init__.py` for the complete exception hierarchy.

---

## Table of Contents

1. [Database Exceptions (asyncpg)](#database-exceptions-asyncpg)
2. [HTTP Client Exceptions (httpx)](#http-client-exceptions-httpx)
3. [File System Exceptions](#file-system-exceptions)
4. [JSON/Pydantic Exceptions](#jsonpydantic-exceptions)
5. [LLM Provider Exceptions](#llm-provider-exceptions)
6. [Email Service Exceptions](#email-service-exceptions)
7. [Decorator Pattern for Common Cases](#decorator-pattern-for-common-cases)
8. [Pre-Commit Hook Implementation](#pre-commit-hook-implementation)
9. [Migration Checklist](#migration-checklist)

---

## Database Exceptions (asyncpg)

### Connection Errors

```python
# ❌ BEFORE (Generic - BAD)
import asyncpg

try:
    pool = await asyncpg.create_pool(...)
except Exception as e:
    raise DatabaseException(...)

# ✅ AFTER (Specific - GOOD)
import asyncpg
from shared.exceptions import DatabaseException, DAOConnectionException

try:
    pool = await asyncpg.create_pool(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
except asyncpg.InvalidCatalogNameError as e:
    raise DatabaseException(
        message=f"Database '{DB_NAME}' does not exist",
        operation="connect",
        table_name=DB_NAME,
        original_exception=e
    )
except asyncpg.InvalidPasswordError as e:
    raise DAOConnectionException(
        message="Authentication failed: Invalid database credentials",
        host=DB_HOST,
        port=DB_PORT,
        original_exception=e
    )
except asyncpg.ConnectionDoesNotExistError as e:
    raise DAOConnectionException(
        message="Database connection lost",
        host=DB_HOST,
        port=DB_PORT,
        original_exception=e
    )
except asyncpg.CannotConnectNowError as e:
    raise DatabaseException(
        message="Database is starting up or shutting down",
        operation="connect",
        original_exception=e
    )
except asyncpg.TooManyConnectionsError as e:
    raise DatabaseException(
        message="Database connection pool exhausted",
        operation="connect",
        original_exception=e
    )
except (asyncpg.ConnectionFailureError, asyncpg.PostgresConnectionError) as e:
    raise DAOConnectionException(
        message="Failed to connect to database server",
        host=DB_HOST,
        port=DB_PORT,
        original_exception=e
    )
```

### Constraint Violations

```python
# ❌ BEFORE (Generic - BAD)
try:
    await conn.execute("INSERT INTO users (email) VALUES ($1)", email)
except Exception as e:
    raise DatabaseException(...)

# ✅ AFTER (Specific - GOOD)
import asyncpg
from shared.exceptions import (
    ConflictException,
    ValidationException,
    DatabaseException
)

try:
    await conn.execute(
        "INSERT INTO users (email, username) VALUES ($1, $2)",
        email, username
    )
except asyncpg.UniqueViolationError as e:
    # Extract constraint name to provide specific error message
    constraint_name = e.constraint_name if hasattr(e, 'constraint_name') else 'unique'

    if 'email' in str(e):
        raise ConflictException(
            message=f"User with email '{email}' already exists",
            resource_type="user",
            conflicting_field="email",
            existing_value=email,
            original_exception=e
        )
    elif 'username' in str(e):
        raise ConflictException(
            message=f"Username '{username}' is already taken",
            resource_type="user",
            conflicting_field="username",
            existing_value=username,
            original_exception=e
        )
    else:
        raise ConflictException(
            message="Duplicate record detected",
            resource_type="user",
            original_exception=e
        )

except asyncpg.ForeignKeyViolationError as e:
    # Determine which foreign key failed
    detail = str(e)
    if 'organization_id' in detail:
        raise ValidationException(
            message="Referenced organization does not exist",
            field_name="organization_id",
            original_exception=e
        )
    elif 'course_id' in detail:
        raise ValidationException(
            message="Referenced course does not exist",
            field_name="course_id",
            original_exception=e
        )
    else:
        raise ValidationException(
            message="Referenced record does not exist",
            original_exception=e
        )

except asyncpg.NotNullViolationError as e:
    # Extract column name from error
    column_name = e.column_name if hasattr(e, 'column_name') else 'unknown'
    raise ValidationException(
        message=f"Required field '{column_name}' cannot be null",
        field_name=column_name,
        original_exception=e
    )

except asyncpg.CheckViolationError as e:
    # Extract constraint name to provide business rule context
    constraint_name = e.constraint_name if hasattr(e, 'constraint_name') else 'check'
    raise ValidationException(
        message=f"Data violates business rule: {constraint_name}",
        original_exception=e
    )

except asyncpg.ExclusionViolationError as e:
    raise ConflictException(
        message="Record conflicts with existing data (exclusion constraint)",
        resource_type="record",
        original_exception=e
    )
```

### Query Errors

```python
# ❌ BEFORE (Generic - BAD)
try:
    rows = await conn.fetch("SELECT * FROM users WHERE id = $1", user_id)
except Exception as e:
    raise DatabaseException(...)

# ✅ AFTER (Specific - GOOD)
import asyncpg
from shared.exceptions import DatabaseException, DAOQueryException

try:
    rows = await conn.fetch(
        "SELECT * FROM users WHERE id = $1",
        user_id
    )
except asyncpg.PostgresSyntaxError as e:
    raise DatabaseException(
        message="Invalid SQL query syntax",
        operation="query",
        table_name="users",
        original_exception=e
    )

except asyncpg.UndefinedTableError as e:
    raise DatabaseException(
        message="Table does not exist in database",
        operation="query",
        table_name=e.table_name if hasattr(e, 'table_name') else 'unknown',
        original_exception=e
    )

except asyncpg.UndefinedColumnError as e:
    raise DatabaseException(
        message="Column does not exist in table",
        operation="query",
        original_exception=e
    )

except asyncpg.QueryCanceledError as e:
    raise DatabaseException(
        message="Query execution timeout (query cancelled by database)",
        operation="query",
        table_name="users",
        original_exception=e
    )

except asyncpg.DeadlockDetectedError as e:
    raise DatabaseException(
        message="Database deadlock detected - transaction aborted",
        operation="query",
        original_exception=e
    )

except asyncpg.LockNotAvailableError as e:
    raise DatabaseException(
        message="Resource locked by another transaction",
        operation="query",
        original_exception=e
    )

except asyncpg.TooManyRowsError as e:
    raise DatabaseException(
        message="Query returned more rows than expected",
        operation="query",
        table_name="users",
        original_exception=e
    )

except asyncpg.InsufficientPrivilegeError as e:
    raise DatabaseException(
        message="Database user lacks required privileges for this operation",
        operation="query",
        original_exception=e
    )

except asyncpg.PostgresError as e:
    # Catch-all for other PostgreSQL errors
    raise DatabaseException(
        message=f"Database operation failed: {str(e)}",
        operation="query",
        table_name="users",
        original_exception=e
    )
```

### Transaction Errors

```python
# ❌ BEFORE (Generic - BAD)
async with conn.transaction():
    try:
        await conn.execute(...)
        await conn.execute(...)
    except Exception as e:
        raise DatabaseException(...)

# ✅ AFTER (Specific - GOOD)
import asyncpg
from shared.exceptions import DatabaseException

try:
    async with conn.transaction():
        await conn.execute("INSERT INTO courses (...) VALUES (...)")
        await conn.execute("INSERT INTO course_modules (...) VALUES (...)")
        await conn.execute("INSERT INTO course_lessons (...) VALUES (...)")

except asyncpg.InterfaceError as e:
    raise DatabaseException(
        message="Transaction interface error - connection may be closed",
        operation="transaction",
        original_exception=e
    )

except asyncpg.TransactionRollbackError as e:
    raise DatabaseException(
        message="Transaction rolled back due to error",
        operation="transaction",
        original_exception=e
    )

except asyncpg.SerializationError as e:
    raise DatabaseException(
        message="Transaction serialization failure - concurrent modification detected",
        operation="transaction",
        original_exception=e
    )

except asyncpg.DeadlockDetectedError as e:
    raise DatabaseException(
        message="Deadlock detected - transaction aborted",
        operation="transaction",
        original_exception=e
    )
```

---

## HTTP Client Exceptions (httpx)

### Network and Timeout Errors

```python
# ❌ BEFORE (Generic - BAD)
import httpx

try:
    response = await client.get(url)
except Exception as e:
    raise ServiceException(...)

# ✅ AFTER (Specific - GOOD)
import httpx
from shared.exceptions import (
    ServiceException,
    ConfigurationException,
    AuthenticationException,
    AuthorizationException,
    NotFoundException,
    RateLimitException
)

try:
    response = await client.get(
        f"https://api.example.com/endpoint",
        timeout=10.0
    )
    response.raise_for_status()

except httpx.NetworkError as e:
    raise ServiceException(
        message="Network connection failed",
        target_service="example-api",
        operation="GET /endpoint",
        original_exception=e
    )

except httpx.ConnectTimeout as e:
    raise ServiceException(
        message="Connection timeout - service may be unavailable",
        target_service="example-api",
        operation="GET /endpoint",
        original_exception=e
    )

except httpx.ReadTimeout as e:
    raise ServiceException(
        message="Read timeout - service response too slow",
        target_service="example-api",
        operation="GET /endpoint",
        original_exception=e
    )

except httpx.WriteTimeout as e:
    raise ServiceException(
        message="Write timeout - request too large or connection slow",
        target_service="example-api",
        operation="GET /endpoint",
        original_exception=e
    )

except httpx.PoolTimeout as e:
    raise ServiceException(
        message="Connection pool exhausted - too many concurrent requests",
        target_service="example-api",
        operation="GET /endpoint",
        original_exception=e
    )

except httpx.TimeoutException as e:
    # Generic timeout catch-all
    raise ServiceException(
        message="Request timeout",
        target_service="example-api",
        operation="GET /endpoint",
        original_exception=e
    )

except httpx.ConnectError as e:
    raise ServiceException(
        message="Failed to connect to service",
        target_service="example-api",
        operation="GET /endpoint",
        original_exception=e
    )

except httpx.RemoteProtocolError as e:
    raise ServiceException(
        message="Remote server protocol error",
        target_service="example-api",
        operation="GET /endpoint",
        original_exception=e
    )

except httpx.LocalProtocolError as e:
    raise ServiceException(
        message="Local HTTP protocol error",
        target_service="example-api",
        operation="GET /endpoint",
        original_exception=e
    )

except httpx.ProxyError as e:
    raise ConfigurationException(
        message="Proxy configuration error",
        config_key="HTTP_PROXY",
        original_exception=e
    )

except httpx.UnsupportedProtocol as e:
    raise ConfigurationException(
        message="Unsupported protocol in URL",
        config_key="SERVICE_URL",
        original_exception=e
    )
```

### HTTP Status Code Errors

```python
# ❌ BEFORE (Generic - BAD)
try:
    response = await client.post(url, json=data)
    response.raise_for_status()
except Exception as e:
    raise ServiceException(...)

# ✅ AFTER (Specific - GOOD)
import httpx
from shared.exceptions import (
    ServiceException,
    AuthenticationException,
    AuthorizationException,
    NotFoundException,
    ConflictException,
    ValidationException,
    RateLimitException
)

try:
    response = await client.post(
        "https://api.example.com/resource",
        json={"key": "value"},
        timeout=10.0
    )
    response.raise_for_status()

except httpx.HTTPStatusError as e:
    status_code = e.response.status_code

    # 4xx Client Errors
    if status_code == 400:
        raise ValidationException(
            message=f"Bad request: {e.response.text}",
            original_exception=e
        )

    elif status_code == 401:
        raise AuthenticationException(
            message="Authentication failed - invalid or expired credentials",
            auth_method="api_key",
            reason="unauthorized",
            original_exception=e
        )

    elif status_code == 403:
        raise AuthorizationException(
            message="Access forbidden - insufficient permissions",
            resource="api_resource",
            original_exception=e
        )

    elif status_code == 404:
        raise NotFoundException(
            message=f"Resource not found: {e.request.url}",
            resource_type="api_resource",
            original_exception=e
        )

    elif status_code == 409:
        raise ConflictException(
            message="Resource conflict - duplicate or version mismatch",
            resource_type="api_resource",
            original_exception=e
        )

    elif status_code == 422:
        raise ValidationException(
            message=f"Unprocessable entity: {e.response.text}",
            original_exception=e
        )

    elif status_code == 429:
        # Extract retry-after header if available
        retry_after = e.response.headers.get('Retry-After')
        raise RateLimitException(
            message="API rate limit exceeded",
            retry_after=int(retry_after) if retry_after else None,
            original_exception=e
        )

    # 5xx Server Errors
    elif status_code >= 500:
        raise ServiceException(
            message=f"Service error: HTTP {status_code}",
            target_service="example-api",
            operation="POST /resource",
            status_code=status_code,
            original_exception=e
        )

    else:
        # Other HTTP errors
        raise ServiceException(
            message=f"HTTP error: {status_code}",
            target_service="example-api",
            operation="POST /resource",
            status_code=status_code,
            original_exception=e
        )

except httpx.RequestError as e:
    # Catch-all for request errors not covered above
    raise ServiceException(
        message=f"Request failed: {str(e)}",
        target_service="example-api",
        operation="POST /resource",
        original_exception=e
    )
```

---

## File System Exceptions

```python
# ❌ BEFORE (Generic - BAD)
try:
    with open(filepath, 'r') as f:
        content = f.read()
except Exception as e:
    raise FileStorageException(...)

# ✅ AFTER (Specific - GOOD)
from shared.exceptions import (
    NotFoundException,
    AuthorizationException,
    FileStorageException,
    ValidationException
)

try:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

except FileNotFoundError as e:
    raise NotFoundException(
        message=f"File not found: {filepath}",
        resource_type="file",
        resource_id=filepath,
        original_exception=e
    )

except PermissionError as e:
    raise AuthorizationException(
        message=f"Permission denied: {filepath}",
        resource="file_system",
        required_permission="read",
        original_exception=e
    )

except IsADirectoryError as e:
    raise ValidationException(
        message=f"Path is a directory, not a file: {filepath}",
        field_name="filepath",
        field_value=filepath,
        original_exception=e
    )

except OSError as e:
    if e.errno == 28:  # ENOSPC - No space left on device
        raise FileStorageException(
            message="Disk space exhausted - cannot write file",
            original_exception=e
        )
    elif e.errno == 30:  # EROFS - Read-only file system
        raise AuthorizationException(
            message="File system is read-only",
            resource="file_system",
            required_permission="write",
            original_exception=e
        )
    elif e.errno == 122:  # EDQUOT - Disk quota exceeded
        raise FileStorageException(
            message="Disk quota exceeded",
            original_exception=e
        )
    else:
        raise FileStorageException(
            message=f"File system error: {str(e)}",
            original_exception=e
        )

except UnicodeDecodeError as e:
    raise ValidationException(
        message=f"File encoding error: {filepath} is not valid UTF-8",
        field_name="file_encoding",
        original_exception=e
    )

except IOError as e:
    raise FileStorageException(
        message=f"I/O error reading file: {filepath}",
        original_exception=e
    )
```

### File Upload Handling

```python
# ❌ BEFORE (Generic - BAD)
try:
    file_content = await file.read()
    await save_file(file_content)
except Exception as e:
    raise FileStorageException(...)

# ✅ AFTER (Specific - GOOD)
from shared.exceptions import (
    FileStorageException,
    ValidationException,
    UnsupportedImageFormatException
)
import os

try:
    # Validate file size
    file_size = 0
    chunks = []
    async for chunk in file.stream():
        chunks.append(chunk)
        file_size += len(chunk)

        # Check size limit (e.g., 10MB)
        if file_size > 10 * 1024 * 1024:
            raise ValidationException(
                message="File size exceeds maximum limit of 10MB",
                field_name="file_size",
                field_value=f"{file_size} bytes"
            )

    file_content = b''.join(chunks)

    # Validate file type for images
    if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
        import imghdr
        detected_format = imghdr.what(None, h=file_content[:32])

        if detected_format not in ['png', 'jpeg', 'webp']:
            raise UnsupportedImageFormatException(
                filename=filename,
                detected_format=detected_format or 'unknown',
                supported_formats=['PNG', 'JPG', 'JPEG', 'WEBP']
            )

    # Save file
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, 'wb') as f:
        f.write(file_content)

except MemoryError as e:
    raise FileStorageException(
        message="Insufficient memory to process file upload",
        original_exception=e
    )

except OSError as e:
    if e.errno == 28:  # Disk full
        raise FileStorageException(
            message="Storage capacity exceeded - cannot save file",
            original_exception=e
        )
    else:
        raise FileStorageException(
            message=f"Failed to save uploaded file: {str(e)}",
            original_exception=e
        )
```

---

## JSON/Pydantic Exceptions

### JSON Parsing

```python
# ❌ BEFORE (Generic - BAD)
import json

try:
    data = json.loads(json_string)
except Exception as e:
    raise ValidationException(...)

# ✅ AFTER (Specific - GOOD)
import json
from shared.exceptions import ValidationException

try:
    data = json.loads(json_string)

except json.JSONDecodeError as e:
    raise ValidationException(
        message=f"Invalid JSON format at line {e.lineno}, column {e.colno}: {e.msg}",
        field_name="json_data",
        validation_errors={
            "json": f"Parse error: {e.msg}",
            "line": str(e.lineno),
            "column": str(e.colno)
        },
        original_exception=e
    )

except ValueError as e:
    # Some JSON errors raise ValueError instead of JSONDecodeError
    raise ValidationException(
        message=f"Invalid JSON value: {str(e)}",
        field_name="json_data",
        original_exception=e
    )
```

### Pydantic Validation

```python
# ❌ BEFORE (Generic - BAD)
from pydantic import BaseModel

try:
    course = CourseCreate(**data)
except Exception as e:
    raise ValidationException(...)

# ✅ AFTER (Specific - GOOD)
from pydantic import BaseModel, ValidationError
from shared.exceptions import ValidationException

try:
    course = CourseCreate(**data)

except ValidationError as e:
    # Extract field-level validation errors
    field_errors = {}
    for error in e.errors():
        field_path = '.'.join(str(loc) for loc in error['loc'])
        field_errors[field_path] = error['msg']

    raise ValidationException(
        message="Course data validation failed",
        validation_errors=field_errors,
        original_exception=e
    )

except TypeError as e:
    raise ValidationException(
        message=f"Invalid data type: {str(e)}",
        field_name="request_body",
        original_exception=e
    )
```

---

## LLM Provider Exceptions

### OpenAI/Anthropic Provider Errors

```python
# ❌ BEFORE (Generic - BAD)
import openai

try:
    response = await openai.ChatCompletion.create(...)
except Exception as e:
    raise AIServiceException(...)

# ✅ AFTER (Specific - GOOD)
import openai
from shared.exceptions import (
    LLMProviderException,
    LLMProviderConnectionException,
    LLMProviderAuthenticationException,
    LLMProviderRateLimitException,
    LLMProviderResponseException
)

provider_name = "OpenAI"  # or "Anthropic", "Deepseek", etc.

try:
    response = await openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        timeout=30.0
    )

except openai.AuthenticationError as e:
    raise LLMProviderAuthenticationException(
        provider=provider_name,
        detail="Invalid API key or authentication failed",
        original_exception=e
    )

except openai.PermissionDeniedError as e:
    raise LLMProviderAuthenticationException(
        provider=provider_name,
        detail="API key lacks required permissions for this model",
        original_exception=e
    )

except openai.RateLimitError as e:
    # Extract retry-after if available
    retry_after = getattr(e, 'retry_after', None)
    raise LLMProviderRateLimitException(
        provider=provider_name,
        retry_after=retry_after,
        original_exception=e
    )

except openai.APIConnectionError as e:
    raise LLMProviderConnectionException(
        provider=provider_name,
        operation="chat_completion",
        original_error=str(e),
        original_exception=e
    )

except openai.APITimeoutError as e:
    raise LLMProviderConnectionException(
        provider=provider_name,
        operation="chat_completion",
        original_error="Request timeout",
        original_exception=e
    )

except openai.BadRequestError as e:
    raise LLMProviderResponseException(
        provider=provider_name,
        status_code=400,
        detail=f"Invalid request: {str(e)}",
        original_exception=e
    )

except openai.ConflictError as e:
    raise LLMProviderResponseException(
        provider=provider_name,
        status_code=409,
        detail="Request conflicts with current state",
        original_exception=e
    )

except openai.NotFoundError as e:
    raise LLMProviderResponseException(
        provider=provider_name,
        status_code=404,
        detail="Model or resource not found",
        original_exception=e
    )

except openai.UnprocessableEntityError as e:
    raise LLMProviderResponseException(
        provider=provider_name,
        status_code=422,
        detail=f"Invalid parameters: {str(e)}",
        original_exception=e
    )

except openai.InternalServerError as e:
    raise LLMProviderException(
        message=f"{provider_name} internal server error",
        provider_name=provider_name,
        operation="chat_completion",
        original_exception=e
    )

except openai.APIError as e:
    # Generic OpenAI API error
    raise LLMProviderException(
        message=f"{provider_name} API error: {str(e)}",
        provider_name=provider_name,
        operation="chat_completion",
        original_exception=e
    )
```

### Vision Analysis Errors

```python
# ❌ BEFORE (Generic - BAD)
try:
    analysis = await analyze_screenshot(image_data)
except Exception as e:
    raise VisionAnalysisException(...)

# ✅ AFTER (Specific - GOOD)
from shared.exceptions import (
    VisionAnalysisException,
    ScreenshotAnalysisException,
    UnsupportedImageFormatException,
    LLMProviderException
)

try:
    # Validate image format
    if not filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
        raise UnsupportedImageFormatException(
            filename=filename,
            detected_format=filename.split('.')[-1],
            supported_formats=['PNG', 'JPG', 'JPEG', 'WEBP']
        )

    # Call vision API
    analysis = await llm_provider.analyze_image(
        image_data=image_data,
        prompt="Extract course content from this screenshot"
    )

    if not analysis or 'content' not in analysis:
        raise ScreenshotAnalysisException(
            screenshot_id=screenshot_id,
            reason="Empty or invalid response from vision model",
            provider=provider_name
        )

except LLMProviderException as e:
    # Re-raise LLM provider exceptions with additional context
    raise ScreenshotAnalysisException(
        screenshot_id=screenshot_id,
        reason=f"Vision analysis failed: {str(e)}",
        provider=provider_name,
        original_exception=e
    )

except ValueError as e:
    raise VisionAnalysisException(
        message="Invalid image data or encoding",
        image_hash=screenshot_id,
        provider_name=provider_name,
        original_exception=e
    )
```

---

## Email Service Exceptions

```python
# ❌ BEFORE (Generic - BAD)
import smtplib

try:
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.sendmail(from_addr, to_addr, message)
except Exception as e:
    logger.error(f"Email failed: {e}")

# ✅ AFTER (Specific - GOOD)
import smtplib
import socket
from shared.exceptions import (
    ServiceException,
    AuthenticationException,
    ConfigurationException
)

try:
    server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)

    if use_tls:
        server.starttls()

    if smtp_user and smtp_password:
        server.login(smtp_user, smtp_password)

    server.sendmail(from_email, to_email, message.as_string())
    server.quit()

except smtplib.SMTPAuthenticationError as e:
    raise AuthenticationException(
        message="SMTP authentication failed - invalid credentials",
        auth_method="smtp",
        reason="invalid_credentials",
        original_exception=e
    )

except smtplib.SMTPSenderRefused as e:
    raise ConfigurationException(
        message=f"SMTP sender refused: {from_email}",
        config_key="EMAIL_FROM_ADDRESS",
        original_exception=e
    )

except smtplib.SMTPRecipientsRefused as e:
    raise ValidationException(
        message=f"SMTP recipients refused: {to_email}",
        field_name="to_email",
        field_value=to_email,
        original_exception=e
    )

except smtplib.SMTPDataError as e:
    raise ServiceException(
        message="SMTP data error - message rejected by server",
        target_service="smtp",
        operation="sendmail",
        original_exception=e
    )

except smtplib.SMTPConnectError as e:
    raise ServiceException(
        message=f"Failed to connect to SMTP server: {smtp_server}:{smtp_port}",
        target_service="smtp",
        operation="connect",
        original_exception=e
    )

except smtplib.SMTPServerDisconnected as e:
    raise ServiceException(
        message="SMTP server disconnected unexpectedly",
        target_service="smtp",
        operation="sendmail",
        original_exception=e
    )

except socket.timeout as e:
    raise ServiceException(
        message="SMTP connection timeout",
        target_service="smtp",
        operation="connect",
        original_exception=e
    )

except socket.gaierror as e:
    raise ConfigurationException(
        message=f"SMTP server hostname resolution failed: {smtp_server}",
        config_key="SMTP_SERVER",
        original_exception=e
    )

except OSError as e:
    raise ServiceException(
        message=f"SMTP network error: {str(e)}",
        target_service="smtp",
        operation="sendmail",
        original_exception=e
    )
```

---

## Decorator Pattern for Common Cases

### Database Operation Decorator

```python
"""
Database operation decorator for automatic exception handling.

Usage:
    @handle_database_exceptions("create_course", "courses")
    async def create_course(self, course: Course) -> Course:
        async with self.db_pool.acquire() as conn:
            # Clean business logic without try/except
            return await conn.execute(...)
"""

import functools
import asyncpg
from typing import Callable, Optional
from shared.exceptions import (
    DatabaseException,
    ConflictException,
    ValidationException,
    DAOConnectionException
)


def handle_database_exceptions(
    operation: str,
    table_name: Optional[str] = None,
    service_name: Optional[str] = None
):
    """
    Decorator to handle database exceptions for DAO methods.

    Args:
        operation: Description of the operation (e.g., "create_course", "get_user")
        table_name: Name of the database table involved
        service_name: Name of the service for logging context
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)

            except asyncpg.UniqueViolationError as e:
                raise ConflictException(
                    message=f"Duplicate record in {table_name or 'table'}",
                    resource_type=table_name,
                    conflicting_field=_extract_field_from_error(e),
                    original_exception=e,
                    service_name=service_name
                )

            except asyncpg.ForeignKeyViolationError as e:
                raise ValidationException(
                    message=f"Invalid reference in {table_name or 'table'}",
                    field_name=_extract_field_from_error(e),
                    original_exception=e,
                    service_name=service_name
                )

            except asyncpg.NotNullViolationError as e:
                column = e.column_name if hasattr(e, 'column_name') else 'unknown'
                raise ValidationException(
                    message=f"Required field '{column}' cannot be null",
                    field_name=column,
                    original_exception=e,
                    service_name=service_name
                )

            except asyncpg.CheckViolationError as e:
                raise ValidationException(
                    message="Data violates business rules",
                    original_exception=e,
                    service_name=service_name
                )

            except (asyncpg.ConnectionFailureError, asyncpg.PostgresConnectionError) as e:
                raise DAOConnectionException(
                    message="Database connection failed",
                    original_exception=e,
                    service_name=service_name
                )

            except asyncpg.QueryCanceledError as e:
                raise DatabaseException(
                    message="Query execution timeout",
                    operation=operation,
                    table_name=table_name,
                    original_exception=e,
                    service_name=service_name
                )

            except asyncpg.PostgresError as e:
                raise DatabaseException(
                    message=f"Database operation failed: {operation}",
                    operation=operation,
                    table_name=table_name,
                    original_exception=e,
                    service_name=service_name
                )

        return wrapper
    return decorator


def _extract_field_from_error(error: Exception) -> Optional[str]:
    """Extract field name from database error message."""
    error_str = str(error)

    # Try to extract constraint name
    if hasattr(error, 'constraint_name'):
        return error.constraint_name

    # Try to extract from error message
    if 'Key (' in error_str:
        start = error_str.find('Key (') + 5
        end = error_str.find(')', start)
        return error_str[start:end]

    return None


# Example usage:
class CourseDAO:
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool

    @handle_database_exceptions("create_course", "courses", "course-management")
    async def create_course(self, course: Course) -> Course:
        """Create a new course - no exception handling needed!"""
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO courses (id, title, instructor_id)
                   VALUES ($1, $2, $3)""",
                course.id, course.title, course.instructor_id
            )
            return course

    @handle_database_exceptions("get_course", "courses", "course-management")
    async def get_by_id(self, course_id: str) -> Optional[Course]:
        """Get course by ID - no exception handling needed!"""
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM courses WHERE id = $1",
                course_id
            )
            return self._row_to_course(row) if row else None
```

### HTTP Client Decorator

```python
"""
HTTP client decorator for automatic exception handling.

Usage:
    @handle_http_exceptions("course-generator", "POST /generate")
    async def call_course_generator(self, data: dict) -> dict:
        async with httpx.AsyncClient() as client:
            # Clean business logic without try/except
            response = await client.post(url, json=data)
            response.raise_for_status()
            return response.json()
"""

import functools
import httpx
from typing import Callable
from shared.exceptions import (
    ServiceException,
    AuthenticationException,
    AuthorizationException,
    NotFoundException,
    ValidationException,
    RateLimitException,
    ConfigurationException
)


def handle_http_exceptions(
    target_service: str,
    operation: str
):
    """
    Decorator to handle HTTP exceptions for service-to-service calls.

    Args:
        target_service: Name of the target service (e.g., "course-generator")
        operation: HTTP operation (e.g., "POST /generate")
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)

            except httpx.HTTPStatusError as e:
                status_code = e.response.status_code

                if status_code == 400:
                    raise ValidationException(
                        message=f"Bad request to {target_service}: {e.response.text}",
                        original_exception=e
                    )
                elif status_code == 401:
                    raise AuthenticationException(
                        message=f"Authentication failed for {target_service}",
                        auth_method="api_key",
                        original_exception=e
                    )
                elif status_code == 403:
                    raise AuthorizationException(
                        message=f"Access forbidden to {target_service}",
                        resource=target_service,
                        original_exception=e
                    )
                elif status_code == 404:
                    raise NotFoundException(
                        message=f"Resource not found in {target_service}",
                        resource_type="api_resource",
                        original_exception=e
                    )
                elif status_code == 429:
                    retry_after = e.response.headers.get('Retry-After')
                    raise RateLimitException(
                        message=f"Rate limit exceeded for {target_service}",
                        retry_after=int(retry_after) if retry_after else None,
                        original_exception=e
                    )
                else:
                    raise ServiceException(
                        message=f"{target_service} returned HTTP {status_code}",
                        target_service=target_service,
                        operation=operation,
                        status_code=status_code,
                        original_exception=e
                    )

            except httpx.TimeoutException as e:
                raise ServiceException(
                    message=f"Request timeout to {target_service}",
                    target_service=target_service,
                    operation=operation,
                    original_exception=e
                )

            except httpx.NetworkError as e:
                raise ServiceException(
                    message=f"Network error connecting to {target_service}",
                    target_service=target_service,
                    operation=operation,
                    original_exception=e
                )

            except httpx.ProxyError as e:
                raise ConfigurationException(
                    message="HTTP proxy configuration error",
                    config_key="HTTP_PROXY",
                    original_exception=e
                )

            except httpx.RequestError as e:
                raise ServiceException(
                    message=f"Request failed to {target_service}: {str(e)}",
                    target_service=target_service,
                    operation=operation,
                    original_exception=e
                )

        return wrapper
    return decorator


# Example usage:
class CourseGeneratorClient:

    @handle_http_exceptions("course-generator", "POST /generate")
    async def generate_course(self, prompt: str) -> dict:
        """Generate course content - no exception handling needed!"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://course-generator:8001/generate",
                json={"prompt": prompt},
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
```

---

## Pre-Commit Hook Implementation

### Install Pre-Commit Hook

Create `.pre-commit-config.yaml` in repository root:

```yaml
# Course Creator Platform - Pre-Commit Configuration
# Enforces code quality standards including exception handling requirements

repos:
  - repo: local
    hooks:
      # Check for generic exception handlers (CLAUDE.md requirement)
      - id: check-generic-exceptions
        name: Check for generic exception handlers
        description: Ensures all Python files use specific exceptions, not generic 'except Exception'
        entry: python scripts/check_exceptions.py
        language: python
        types: [python]
        pass_filenames: true
        stages: [commit]
        verbose: true

      # Run tests before commit
      - id: pytest-check
        name: Run pytest tests
        description: Runs unit tests before allowing commit
        entry: pytest
        language: system
        types: [python]
        pass_filenames: false
        stages: [commit]

      # Check Python syntax
      - id: python-syntax-check
        name: Check Python syntax
        description: Validates Python syntax using py_compile
        entry: python -m py_compile
        language: system
        types: [python]
        pass_filenames: true

  # Standard pre-commit hooks
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: ['--maxkb=1000']
      - id: check-json
      - id: check-toml
      - id: mixed-line-ending

  # Python code formatting
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3.11

  # Import sorting
  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort
        args: ['--profile', 'black']
```

### Exception Checker Script

Create `scripts/check_exceptions.py`:

```python
#!/usr/bin/env python3
"""
Pre-Commit Hook: Generic Exception Handler Checker

This script enforces the CLAUDE.md requirement that all code must use
specific custom exceptions instead of generic 'except Exception' handlers.

Exit Codes:
    0: All files pass (no generic exception handlers)
    1: One or more files have generic exception handlers
"""

import re
import sys
import os
from pathlib import Path
from typing import List, Tuple, Dict


# Patterns to detect generic exception handlers
GENERIC_EXCEPTION_PATTERNS = [
    # Matches: except Exception as e:
    r'except\s+Exception\s+as\s+\w+\s*:',

    # Matches: except Exception:
    r'except\s+Exception\s*:',

    # Matches: except BaseException as e:
    r'except\s+BaseException\s+as\s+\w+\s*:',
]

# Files/directories to exclude from checking
EXCLUDE_PATTERNS = [
    'tests/unit/test_exception_handling.py',  # Test file for exceptions
    'shared/exceptions.py',  # Exception definitions
    'shared/exceptions/__init__.py',  # Exception exports
    '.venv/',
    'venv/',
    '__pycache__/',
    '.git/',
    'node_modules/',
]


def is_excluded(filepath: str) -> bool:
    """Check if file should be excluded from checking."""
    for pattern in EXCLUDE_PATTERNS:
        if pattern in filepath:
            return True
    return False


def find_generic_exceptions(filepath: str) -> List[Tuple[int, str, str]]:
    """
    Find all generic exception handlers in a Python file.

    Returns:
        List of tuples: (line_number, line_content, pattern_matched)
    """
    matches = []

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for line_num, line in enumerate(lines, start=1):
            # Skip comments
            if line.strip().startswith('#'):
                continue

            # Check each pattern
            for pattern in GENERIC_EXCEPTION_PATTERNS:
                if re.search(pattern, line):
                    matches.append((line_num, line.strip(), pattern))

    except Exception as e:
        print(f"ERROR: Failed to read {filepath}: {e}", file=sys.stderr)

    return matches


def get_suggestion(pattern: str) -> str:
    """Get suggested replacement for generic exception pattern."""
    suggestions = {
        'except Exception as e:': '''
Suggested fix:
    # Import specific exceptions
    from shared.exceptions import (
        DatabaseException,
        ValidationException,
        ServiceException
    )

    # Use specific exception handlers
    try:
        # your code
    except asyncpg.UniqueViolationError as e:
        raise ConflictException(...)
    except asyncpg.PostgresError as e:
        raise DatabaseException(...)
''',
        'except BaseException as e:': '''
Suggested fix:
    # Use Exception (or more specific) instead of BaseException
    # BaseException catches system exits and keyboard interrupts
''',
    }

    for key in suggestions:
        if key in pattern:
            return suggestions[key]

    return "See docs/EXCEPTION_MAPPING_GUIDE.md for specific exception types."


def check_file(filepath: str) -> bool:
    """
    Check a single file for generic exception handlers.

    Returns:
        True if file passes (no generic handlers), False otherwise
    """
    if is_excluded(filepath):
        return True

    matches = find_generic_exceptions(filepath)

    if matches:
        print(f"\n❌ {filepath}:")
        print(f"   Found {len(matches)} generic exception handler(s)")

        for line_num, line, pattern in matches:
            print(f"   Line {line_num}: {line}")

        print(get_suggestion(pattern))
        return False

    return True


def main():
    """Main entry point for pre-commit hook."""
    if len(sys.argv) < 2:
        print("Usage: check_exceptions.py <file1.py> [file2.py] ...", file=sys.stderr)
        sys.exit(1)

    files_to_check = sys.argv[1:]

    # Filter to only Python files
    python_files = [f for f in files_to_check if f.endswith('.py')]

    if not python_files:
        print("✅ No Python files to check")
        sys.exit(0)

    print(f"\n🔍 Checking {len(python_files)} Python file(s) for generic exception handlers...")
    print("=" * 80)

    all_passed = True
    failed_files = []

    for filepath in python_files:
        if not check_file(filepath):
            all_passed = False
            failed_files.append(filepath)

    print("\n" + "=" * 80)

    if all_passed:
        print(f"✅ All {len(python_files)} file(s) passed - no generic exception handlers")
        sys.exit(0)
    else:
        print(f"\n❌ {len(failed_files)} file(s) failed:")
        for filepath in failed_files:
            print(f"   - {filepath}")

        print("\n📖 Remediation:")
        print("   1. Read docs/EXCEPTION_MAPPING_GUIDE.md")
        print("   2. Replace generic 'except Exception' with specific exceptions")
        print("   3. Import from shared.exceptions module")
        print("   4. Re-run git commit\n")

        sys.exit(1)


if __name__ == '__main__':
    main()
```

Make the script executable:

```bash
chmod +x scripts/check_exceptions.py
```

### Install Pre-Commit

```bash
# Install pre-commit package
pip install pre-commit

# Install the git hook scripts
pre-commit install

# (Optional) Run against all files
pre-commit run --all-files
```

---

## Migration Checklist

### Phase 1: Preparation (Week 1)

- [ ] Review exception mapping guide thoroughly
- [ ] Install pre-commit hooks (`pre-commit install`)
- [ ] Run exception checker to identify all violations:
  ```bash
  python scripts/check_exceptions.py $(find . -name "*.py" -not -path "./.venv/*")
  ```
- [ ] Create prioritized file list (DAOs first, then services, then endpoints)
- [ ] Set up branch for exception refactoring work

### Phase 2: DAO Layer (Weeks 2-3)

**Priority**: Fix all Data Access Objects first as they are used by multiple services.

- [ ] Fix all `*_dao.py` files in `services/*/data_access/`
- [ ] Run unit tests for each DAO after fixing
- [ ] Example files:
  - [ ] `services/course-management/data_access/course_dao.py` (24 violations)
  - [ ] `services/organization-management/organization_management/data_access/llm_config_dao.py`
  - [ ] `services/analytics/data_access/dashboard_dao.py` (52 violations)
  - [ ] `services/user-management/data_access/user_dao.py`

### Phase 3: Service Layer (Weeks 3-4)

**Priority**: Fix application/business logic services.

- [ ] Fix all `*_service.py` files in `services/*/application/services/`
- [ ] Run integration tests for each service after fixing
- [ ] Example files:
  - [ ] `services/course-management/course_management/application/services/adaptive_learning_service.py`
  - [ ] `services/organization-management/organization_management/application/services/organization_service.py`
  - [ ] `services/ai-assistant-service/ai_assistant_service/application/services/rag_service.py`

### Phase 4: API Endpoints (Week 4)

**Priority**: Fix all API endpoint handlers.

- [ ] Fix all `*_endpoints.py` files in `services/*/api/`
- [ ] Run API integration tests after fixing
- [ ] Example files:
  - [ ] `services/course-management/api/course_endpoints.py`
  - [ ] `services/organization-management/api/llm_config_endpoints.py`
  - [ ] `services/analytics/api/routes.py`

### Phase 5: Infrastructure (Week 5)

**Priority**: Fix infrastructure components (email, caching, middleware).

- [ ] Fix email service files:
  - [ ] `services/course-management/email_service.py`
  - [ ] `services/user-management/services/email_service.py`
- [ ] Fix caching services:
  - [ ] `shared/cache/redis_cache.py`
  - [ ] `shared/cache/organization_redis_cache.py`
- [ ] Fix middleware:
  - [ ] `shared/auth/organization_middleware.py`
  - [ ] `services/*/auth/jwt_middleware.py`

### Phase 6: Testing & Verification (Week 6)

- [ ] Run full test suite: `pytest tests/ -v`
- [ ] Run pre-commit on all files: `pre-commit run --all-files`
- [ ] Fix any remaining violations
- [ ] Verify Docker infrastructure tests pass
- [ ] Run E2E tests for critical user journeys
- [ ] Update documentation with exception handling examples

### Daily Workflow

For each file being fixed:

1. **Before changes:**
   ```bash
   # Count violations in file
   python scripts/check_exceptions.py <filepath>
   ```

2. **Make changes:**
   - Read relevant section of EXCEPTION_MAPPING_GUIDE.md
   - Replace generic handlers with specific ones
   - Add imports from `shared.exceptions`
   - Use decorator patterns where appropriate

3. **After changes:**
   ```bash
   # Verify no violations remain
   python scripts/check_exceptions.py <filepath>

   # Run related tests
   pytest tests/unit/<service>/ -k <test_name> -v
   ```

4. **Commit:**
   ```bash
   git add <filepath>
   git commit -m "fix: Replace generic exceptions in <filename>"
   # Pre-commit hook will verify automatically
   ```

### Metrics Tracking

Track progress using this template:

```markdown
# Exception Refactoring Progress

## Overall Status
- **Total Files**: 432 files with violations
- **Files Fixed**: X / 432
- **Violations Remaining**: Y
- **Completion**: Z%

## By Category
- DAO Layer: X / 50 files (priority 1)
- Service Layer: X / 150 files (priority 2)
- API Endpoints: X / 80 files (priority 3)
- Infrastructure: X / 30 files (priority 4)
- Tests: X / 122 files (priority 5)

## This Week
- Files fixed: X
- Tests passing: Y / Y
- Blockers: None
```

---

## Exception Type Quick Reference

### When to Use Each Exception Type

| Scenario | Exception Type | Example |
|----------|---------------|---------|
| Duplicate database record | `ConflictException` | User email already exists |
| Missing database record | `NotFoundException` | Course ID not found |
| Invalid input data | `ValidationException` | Email format invalid |
| Database connection failed | `DAOConnectionException` | Cannot connect to PostgreSQL |
| Database query error | `DatabaseException` | SQL syntax error |
| HTTP 401 response | `AuthenticationException` | Invalid API key |
| HTTP 403 response | `AuthorizationException` | Insufficient permissions |
| HTTP 404 response | `NotFoundException` | Resource not found |
| HTTP 429 response | `RateLimitException` | Too many requests |
| HTTP 5xx response | `ServiceException` | Service unavailable |
| File not found | `NotFoundException` | File path invalid |
| Permission denied | `AuthorizationException` | Cannot write to directory |
| Disk full | `FileStorageException` | No space left on device |
| Invalid JSON | `ValidationException` | JSON parse error |
| Pydantic validation | `ValidationException` | Field type mismatch |
| LLM auth failure | `LLMProviderAuthenticationException` | Invalid API key |
| LLM rate limit | `LLMProviderRateLimitException` | Quota exceeded |
| LLM network error | `LLMProviderConnectionException` | Connection timeout |
| Vision analysis failure | `VisionAnalysisException` | Image processing error |
| Unsupported image format | `UnsupportedImageFormatException` | BMP not supported |
| SMTP auth failure | `AuthenticationException` | Invalid SMTP credentials |
| Email send failure | `ServiceException` | SMTP server unavailable |

---

## Resources

- **Exception Definitions**: `/home/bbrelin/course-creator/shared/exceptions.py`
- **Exception Exports**: `/home/bbrelin/course-creator/shared/exceptions/__init__.py`
- **CLAUDE.md Requirements**: `/home/bbrelin/course-creator/CLAUDE.md`
- **12-Week Roadmap**: See memory fact ID 680 (exception handling is Q1 priority)

---

## Questions?

If you encounter a scenario not covered in this guide:

1. Check existing exception definitions in `shared/exceptions.py`
2. Look for similar patterns in recently refactored files
3. Consult CLAUDE.md for architectural guidance
4. Add new exception types if needed (following existing patterns)

**Remember**: The goal is **zero generic exception handlers** in production code. Every `except Exception` must be replaced with specific exception types that provide meaningful error context.
