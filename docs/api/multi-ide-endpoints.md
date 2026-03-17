# Multi-IDE Lab Container API Documentation

This document describes the API endpoints for managing multi-IDE lab containers in the Course Creator platform.

## Overview

The Multi-IDE Lab Container system allows students and instructors to use different Integrated Development Environments (IDEs) within their lab containers. Supported IDEs include:

- **Terminal**: Traditional command-line interface (xterm.js)
- **VSCode Server**: Full web-based Visual Studio Code
- **JupyterLab**: Interactive notebook environment for data science
- **IntelliJ IDEA**: Professional IDE via JetBrains Projector (optional)

## Base URL

All API endpoints are available at the Lab Container Manager service:
```
http://localhost:8006
```

## Authentication

All endpoints require valid JWT authentication. Include the token in the Authorization header:
```
Authorization: Bearer <your-jwt-token>
```

## Core Lab Management Endpoints

### Create Lab Container with Multi-IDE Support

**POST** `/labs`

Creates a new lab container with multi-IDE capabilities.

**Request Body:**
```json
{
  "user_id": "string",
  "course_id": "string", 
  "lab_type": "string",
  "lab_config": {},
  "timeout_minutes": 60,
  "instructor_mode": false,
  "custom_dockerfile": "string (optional)",
  "preferred_ide": "terminal", // terminal, vscode, jupyter, intellij
  "enable_multi_ide": true
}
```

**Response:**
```json
{
  "lab_id": "string",
  "user_id": "string",
  "course_id": "string",
  "lab_type": "string",
  "container_id": "string",
  "port": 8080,
  "ide_ports": {
    "terminal": 8080,
    "vscode": 8081,
    "jupyter": 8082,
    "intellij": 8083
  },
  "status": "running",
  "created_at": "2025-07-26T10:00:00Z",
  "expires_at": "2025-07-26T11:00:00Z",
  "last_accessed": "2025-07-26T10:00:00Z",
  "instructor_mode": false,
  "storage_path": "/app/lab-storage/user123/course456",
  "access_url": "http://localhost:8080",
  "preferred_ide": "terminal",
  "multi_ide_enabled": true,
  "available_ides": {
    "terminal": {
      "name": "Terminal (xterm.js)",
      "port": 8080,
      "enabled": true,
      "healthy": true,
      "url": "http://localhost:8080"
    },
    "vscode": {
      "name": "VSCode Server", 
      "port": 8081,
      "enabled": true,
      "healthy": true,
      "url": "http://localhost:8081"
    },
    "jupyter": {
      "name": "JupyterLab",
      "port": 8082,
      "enabled": true,
      "healthy": true,
      "url": "http://localhost:8082"
    },
    "intellij": {
      "name": "IntelliJ IDEA",
      "port": 8083,
      "enabled": false,
      "healthy": false,
      "url": "http://localhost:8083"
    }
  }
}
```

## Multi-IDE Management Endpoints

### Get Available IDEs

**GET** `/labs/{lab_id}/ides`

Returns information about available IDEs for a specific lab container.

**Path Parameters:**
- `lab_id` (string): The unique identifier of the lab container

**Response:**
```json
{
  "lab_id": "string",
  "preferred_ide": "terminal",
  "multi_ide_enabled": true,
  "available_ides": {
    "terminal": {
      "name": "Terminal (xterm.js)",
      "port": 8080,
      "enabled": true,
      "healthy": true,
      "url": "http://localhost:8080"
    },
    "vscode": {
      "name": "VSCode Server",
      "port": 8081,
      "enabled": true,
      "healthy": true,
      "url": "http://localhost:8081"
    },
    "jupyter": {
      "name": "JupyterLab",
      "port": 8082,
      "enabled": true,
      "healthy": true,
      "url": "http://localhost:8082"
    }
  },
  "ide_ports": {
    "terminal": 8080,
    "vscode": 8081,
    "jupyter": 8082,
    "intellij": 8083
  }
}
```

### Switch IDE

**POST** `/labs/{lab_id}/ide/switch`

Switches the preferred IDE for a lab container.

**Path Parameters:**
- `lab_id` (string): The unique identifier of the lab container

**Query Parameters:**
- `ide_type` (string): The IDE to switch to (`terminal`, `vscode`, `jupyter`, `intellij`)

**Response:**
```json
{
  "message": "Switched to VSCode Server",
  "lab_id": "string",
  "ide_type": "vscode", 
  "ide_url": "http://localhost:8081"
}
```

**Error Responses:**
- `404` - Lab session not found
- `400` - IDE not available or invalid IDE type

### Get IDE Health Status

**GET** `/labs/{lab_id}/ide/status`

Returns the health status of all IDEs in a lab container.

**Path Parameters:**
- `lab_id` (string): The unique identifier of the lab container

**Response:**
```json
{
  "status": "running",
  "ides": {
    "terminal": {
      "name": "Terminal (xterm.js)",
      "port": 8080,
      "healthy": true,
      "url": "http://localhost:8080"
    },
    "vscode": {
      "name": "VSCode Server",
      "port": 8081,
      "healthy": true,
      "url": "http://localhost:8081"
    },
    "jupyter": {
      "name": "JupyterLab",
      "port": 8082,
      "healthy": true,
      "url": "http://localhost:8082"
    },
    "intellij": {
      "name": "IntelliJ IDEA",
      "port": 8083,
      "healthy": false,
      "url": "http://localhost:8083"
    }
  }
}
```

**Possible Status Values:**
- `running` - Container is running and IDEs are accessible
- `container_not_started` - Container hasn't been started yet
- `container_stopped` - Container is stopped
- `container_not_found` - Container no longer exists
- `error` - Error occurred while checking status

## IDE-Specific Information

### Terminal (xterm.js)
- **Port**: 8080 (main port)
- **Description**: Traditional command-line interface
- **Features**: Full terminal access, file system navigation, command execution
- **Always Available**: Yes

### VSCode Server
- **Port**: 8081
- **Description**: Full web-based Visual Studio Code
- **Features**: 
  - Syntax highlighting and IntelliSense
  - Integrated terminal
  - File explorer
  - Extension support
  - Python debugging capabilities
- **Pre-installed Extensions**: 
  - Python
  - Black Formatter
  - Pylint
  - Jupyter

### JupyterLab
- **Port**: 8082
- **Description**: Interactive notebook environment
- **Features**:
  - Notebook interface with code and markdown cells
  - Rich output display (plots, tables, images)
  - File browser
  - Terminal access
  - Built-in Python kernel
- **Pre-installed Packages**:
  - NumPy, Pandas, Matplotlib, Seaborn
  - Requests, Flask, FastAPI

### IntelliJ IDEA (Optional)
- **Port**: 8083
- **Description**: Professional IDE via JetBrains Projector
- **Features**:
  - Advanced code intelligence
  - Refactoring tools
  - Integrated version control
  - Database tools
- **Availability**: Resource-intensive, may not always be enabled
- **Note**: Requires additional configuration and resources

## Resource Management

### Multi-IDE Resource Allocation

When `enable_multi_ide` is `true`:
- **Memory**: 2GB per container
- **CPU**: 150% of one CPU core
- **Ports**: 4 ports allocated (8080-8083 range)

When `enable_multi_ide` is `false`:
- **Memory**: 1GB per container  
- **CPU**: 100% of one CPU core
- **Ports**: 1 port allocated (8080 only)

### Port Allocation

The system automatically allocates ports for each IDE:
```json
{
  "terminal": "base_port + 0",     // 8080
  "vscode": "base_port + 1",       // 8081
  "jupyter": "base_port + 2",      // 8082
  "intellij": "base_port + 3"      // 8083
}
```

If a port is unavailable, the system will find alternative ports and update the allocation accordingly.

## Error Handling

### Common Error Responses

**404 Not Found**
```json
{
  "detail": "Lab session not found"
}
```

**400 Bad Request**
```json
{
  "detail": "IDE 'invalid_ide' not available. Available IDEs: ['terminal', 'vscode', 'jupyter']"
}
```

**500 Internal Server Error**
```json
{
  "detail": "Failed to create lab: Docker daemon not accessible"
}
```

### IDE Health Check Failures

When IDE health checks fail, the IDE will be marked as `healthy: false` in the status response. Common causes:

1. **Port not accessible**: IDE service not started
2. **Container stopped**: Lab container is paused or stopped
3. **Resource constraints**: Insufficient memory/CPU for IDE
4. **Network issues**: Port conflicts or network connectivity problems

## Usage Examples

### Creating a Multi-IDE Lab

```bash
curl -X POST "http://localhost:8006/labs" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "student123",
    "course_id": "python101", 
    "lab_type": "python",
    "preferred_ide": "vscode",
    "enable_multi_ide": true,
    "timeout_minutes": 120
  }'
```

### Switching to JupyterLab

```bash
curl -X POST "http://localhost:8006/labs/lab-student123-python101-1234567890/ide/switch?ide_type=jupyter" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Checking IDE Status

```bash
curl -X GET "http://localhost:8006/labs/lab-student123-python101-1234567890/ide/status" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Frontend Integration

The multi-IDE frontend interface (`lab-multi-ide.html`) uses these endpoints to:

1. **Initialize IDE tabs**: Call `/labs/{lab_id}/ides` to get available IDEs
2. **Monitor IDE health**: Poll `/labs/{lab_id}/ide/status` every 30 seconds
3. **Switch IDEs**: Call `/labs/{lab_id}/ide/switch` when user clicks IDE tabs
4. **Display status**: Show real-time IDE health indicators

## Best Practices

### For Developers

1. **Always check IDE availability** before allowing users to switch
2. **Handle health check failures gracefully** with user-friendly error messages
3. **Implement retry logic** for transient failures
4. **Cache IDE status** to reduce API calls
5. **Show loading states** during IDE switches

### For System Administrators

1. **Monitor resource usage** for multi-IDE containers
2. **Set appropriate limits** on concurrent multi-IDE labs
3. **Regular health monitoring** of IDE services
4. **Log IDE switching patterns** for usage analytics
5. **Consider disabling IntelliJ** for resource-constrained environments

## Security Considerations

1. **Authentication**: All endpoints require valid JWT tokens
2. **Authorization**: Users can only access their own lab containers
3. **Network isolation**: Lab containers cannot access other services
4. **Resource limits**: Prevent resource exhaustion with container limits
5. **Port security**: Dynamic port allocation prevents conflicts
6. **Container sandboxing**: Limited privileges and capabilities

## Troubleshooting

### Common Issues

1. **IDE not starting**: Check container logs and resource availability
2. **Port conflicts**: System automatically resolves, but may cause delays
3. **Health check failures**: Often resolve automatically after brief delay
4. **Resource exhaustion**: Reduce concurrent multi-IDE labs or increase limits
5. **Container startup timeout**: Increase container startup timeout in configuration

### Monitoring Commands

```bash
# Check lab manager service health
curl http://localhost:8006/health

# List all active labs with IDE information
curl -H "Authorization: Bearer TOKEN" http://localhost:8006/labs

# Check specific lab IDE status
curl -H "Authorization: Bearer TOKEN" http://localhost:8006/labs/{lab_id}/ide/status

# Docker container inspection
docker ps | grep lab-
docker logs lab-{lab_id}
```

This completes the Multi-IDE Lab Container API documentation. For more information about the overall platform architecture, see the main [README.md](../../README.md) and [CLAUDE.md](../../CLAUDE.md) files.