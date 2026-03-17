"""
Jupyter Lab Configuration for Course Creator Lab Environments

This configuration file sets up JupyterLab for use in containerized student lab environments.
It's mounted into Docker containers running the multi-IDE lab image, providing a notebook
interface for data science and Python programming courses.

Business Context:
-----------------
Students need an interactive Python environment for hands-on coding exercises. JupyterLab
provides:
- Interactive notebooks with code cells and Markdown documentation
- Inline visualization (matplotlib, seaborn plots)
- Terminal access for command-line operations
- File browser for managing course materials
- Kernel management for running Python code

Technical Implementation:
------------------------
This config is loaded by JupyterLab server startup scripts in the container. Settings are
optimized for:
- Multi-tenant deployment (each student gets their own container)
- Security in untrusted code execution environment
- Development mode convenience (no authentication within container network)
- Performance (disable unnecessary features)

Security Considerations:
- No token/password authentication (relies on container isolation)
- XSRF checking disabled (simplifies iframe embedding)
- Wildcards for CORS (lab runs on different port than main app)
- Network isolation ensures only authorized users reach containers

WARNING: This configuration is only safe because containers run on isolated Docker networks
and are accessed through authenticated proxies. Do NOT use this config for public-facing
Jupyter servers.

File Locations:
    /services/lab-manager/lab-images/multi-ide-base/ide-configs/jupyter-config.py
    Copied to /home/labuser/.jupyter/jupyter_lab_config.py in containers
"""
# Jupyter Lab configuration for Course Creator labs

c = get_config()

# Network settings
c.ServerApp.ip = '0.0.0.0'  # Listen on all interfaces (container networking)
c.ServerApp.port = 8082  # Standard port for Jupyter in our multi-IDE setup
c.ServerApp.allow_origin = '*'  # Allow CORS from main app (different port)
c.ServerApp.allow_remote_access = True  # Enable access from outside container

# Security settings
# WARNING: These settings disable authentication and are only safe in isolated containers
c.ServerApp.token = ''  # No token authentication (rely on container isolation)
c.ServerApp.password = ''  # No password authentication
c.ServerApp.disable_check_xsrf = True  # Disable XSRF checks for iframe embedding

# Directory settings
c.ServerApp.root_dir = '/home/labuser/workspace'  # Student workspace root
c.ServerApp.preferred_dir = '/home/labuser/workspace/notebooks'  # Default to notebooks folder

# UI settings
c.ServerApp.open_browser = False  # Don't open browser (running in container)
c.LabApp.default_url = '/lab'  # Start in JupyterLab interface (not classic notebook)

# Extension settings
c.ServerApp.nbserver_extensions = {
    'jupyterlab': True  # Enable JupyterLab server extension
}

# Kernel settings
c.MappingKernelManager.default_kernel_name = 'python3'  # Default to Python 3 kernel

# File settings
c.ContentsManager.allow_hidden = True  # Show hidden files (e.g., .gitignore)
c.FileContentsManager.delete_to_trash = False  # Permanent delete (no trash in containers)

# Terminal settings
c.ServerApp.terminals_enabled = True  # Enable web-based terminal access