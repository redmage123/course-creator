# Multi-IDE Lab Environment

## Overview

The Course Creator platform provides a comprehensive multi-IDE lab environment that allows students to code using their preferred development environment. All IDEs run in isolated Docker containers with pre-configured tools and dependencies.

## Available IDEs

### 1. VSCode Server (Port 8081)
- **Status**: ✅ Enabled by default
- **Technology**: code-server (open-source VSCode for the browser)
- **Best For**: General-purpose coding, web development, multi-language projects
- **Features**:
  - Full VSCode experience in browser
  - IntelliSense and code completion
  - Integrated terminal
  - Git integration
  - Extension marketplace access
  - Debugging support

### 2. PyCharm Community Edition (Port 8084)
- **Status**: ✅ Enabled by default (NEW!)
- **Technology**: JetBrains Projector
- **Best For**: Python development, data science, Django/Flask projects
- **Features**:
  - Professional Python IDE
  - Smart code completion
  - Advanced debugging
  - Scientific tools integration
  - Database tools
  - Version control integration

### 3. IntelliJ IDEA Community Edition (Port 8083)
- **Status**: ✅ Enabled by default
- **Technology**: JetBrains Projector
- **Best For**: Java, Kotlin, Scala, and JVM language development
- **Features**:
  - Intelligent code assistance
  - Built-in tools and integrations
  - Framework support (Spring, Jakarta EE, etc.)
  - Database tools
  - Version control
  - Maven/Gradle support

### 4. JupyterLab (Port 8082)
- **Status**: ✅ Enabled by default
- **Technology**: Native JupyterLab
- **Best For**: Data science, machine learning, interactive Python notebooks
- **Features**:
  - Interactive notebooks
  - Data visualization
  - Markdown support
  - Code execution with output
  - Scientific computing libraries pre-installed

### 5. Terminal (Port 8080)
- **Status**: ✅ Always available
- **Technology**: xterm.js web terminal
- **Best For**: Command-line operations, system administration, quick scripts
- **Features**:
  - Full bash shell access
  - File system operations
  - Package installation
  - Git operations

## Architecture

### Container Structure
```
┌─────────────────────────────────────────┐
│   Lab Container (multi-ide-base)        │
├─────────────────────────────────────────┤
│  Port 8080: Terminal & IDE Manager      │
│  Port 8081: VSCode Server               │
│  Port 8082: JupyterLab                  │
│  Port 8083: IntelliJ IDEA               │
│  Port 8084: PyCharm Community           │
├─────────────────────────────────────────┤
│  Workspace: /home/labuser/workspace     │
│    ├── assignments/                     │
│    ├── solutions/                       │
│    ├── data/                            │
│    ├── notebooks/                       │
│    └── projects/                        │
└─────────────────────────────────────────┘
```

### Pre-installed Tools
- **Languages**: Python 3.10, Java 11, Node.js 18
- **Build Tools**: pip, npm, Maven, Gradle
- **Version Control**: git, gitk
- **Editors**: vim, nano
- **Compilers**: gcc, g++, javac
- **Python Packages**: numpy, pandas, matplotlib, jupyter, flask, django

## File Locations

### Docker Configuration
- **Dockerfile**: `/services/lab-manager/lab-images/multi-ide-base/Dockerfile`
- **IDE Startup Script**: `/services/lab-manager/lab-images/multi-ide-base/ide-startup.py`
- **IDE Configs**: `/services/lab-manager/lab-images/multi-ide-base/ide-configs/`

### Frontend
- **Lab Environment Page**: `/frontend/html/lab-environment.html`
- **Nginx Route**: `/lab` → redirects to lab environment page

### Backend Service
- **Lab Manager Service**: `/services/lab-manager/main.py`
- **Docker Compose**: `docker-compose.yml` (lab-manager service)

## Usage

### Accessing the Lab Environment

**For Students:**
1. Navigate to `/lab` in your browser
2. Choose your preferred IDE from the grid
3. Click "Launch [IDE Name]"
4. IDE opens in a new window/tab

**For Instructors:**
- Monitor lab usage via Lab Manager service API
- Configure IDE availability per course
- View student workspace files
- Reset lab environments as needed

### API Endpoints

**Lab Manager Service (Port 8006):**
- `GET /api/status` - Get status of all IDEs
- `GET /health` - Health check endpoint
- `GET /ide/{ide_name}/{path}` - Proxy to specific IDE

**IDE Status Response:**
```json
{
  "status": "healthy",
  "ides": {
    "vscode": {
      "name": "VSCode Server",
      "port": 8081,
      "enabled": true,
      "healthy": true,
      "url": "/ide/vscode"
    },
    "pycharm": {
      "name": "PyCharm Community",
      "port": 8084,
      "enabled": true,
      "healthy": true,
      "url": "/ide/pycharm"
    }
    // ... other IDEs
  }
}
```

## E2E Testing

### Test Expectations

**Lab Environment Workflow Tests:**
1. `test_start_lab_environment` - Verify lab page loads and shows available IDEs
2. `test_write_and_run_code_in_lab` - Test code execution in lab environment
3. `test_lab_persistence_across_sessions` - Verify workspace persistence

**Test File:** `/tests/e2e/critical_user_journeys/test_student_complete_journey.py`

### Running Lab Tests
```bash
HEADLESS=true TEST_BASE_URL=https://localhost:3000 \
  pytest tests/e2e/critical_user_journeys/test_student_complete_journey.py::TestLabEnvironmentWorkflow -v
```

## Resource Management

### Memory Allocation per IDE
- **Terminal**: ~50MB
- **VSCode**: ~200-300MB
- **JupyterLab**: ~150-250MB
- **PyCharm**: ~500-800MB (resource intensive)
- **IntelliJ IDEA**: ~500-800MB (resource intensive)

**Total Container Memory**: Recommended 2-4GB per student container

### Performance Optimization
- IDEs can be selectively enabled/disabled based on course requirements
- PyCharm and IntelliJ use JetBrains Projector (lightweight remote rendering)
- Containers use shared base layers for faster deployment
- Student workspaces are volume-mounted for persistence

## Security

### Isolation
- Each student gets an isolated container
- No root access in lab containers
- Limited resource allocation per container
- Network isolation between student containers

### Authentication
- Lab access requires student authentication
- Session tokens passed to IDE containers
- IDE endpoints not publicly accessible
- All communication over HTTPS

## Troubleshooting

### Common Issues

**1. IDE won't load:**
- Check container health: `docker ps | grep lab`
- View container logs: `docker logs course-creator_lab-manager_1`
- Verify port availability

**2. PyCharm/IntelliJ slow to start:**
- JetBrains IDEs require more resources
- Allow 30-60 seconds for initial startup
- Check container memory allocation

**3. Files not persisting:**
- Verify volume mounts in docker-compose.yml
- Check workspace permissions
- Ensure proper session cleanup

**4. Port conflicts:**
- Each IDE runs on different port
- Ensure ports 8080-8084 are available
- Check docker-compose port mappings

## Future Enhancements

### Planned Features
- [ ] RStudio for R programming courses
- [ ] Eclipse IDE for enterprise Java
- [ ] Atom/Sublime Text for lightweight editing
- [ ] Code review and collaboration tools
- [ ] Real-time pair programming support
- [ ] Custom IDE configurations per course

### Configuration Options
- Dynamic IDE enablement based on course language
- Student IDE preference persistence
- Instructor-controlled resource limits
- Custom Docker images per course type

## References

- **VSCode Server**: https://github.com/coder/code-server
- **JetBrains Projector**: https://github.com/JetBrains/projector-server
- **JupyterLab**: https://jupyterlab.readthedocs.io/
- **Docker Best Practices**: https://docs.docker.com/develop/dev-best-practices/

---

**Last Updated**: 2025-10-08  
**Version**: 3.4.0 - Multi-IDE Lab Environment
