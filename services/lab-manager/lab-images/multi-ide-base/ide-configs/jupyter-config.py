# Jupyter Lab configuration for Course Creator labs

c = get_config()

# Network settings
c.ServerApp.ip = '0.0.0.0'
c.ServerApp.port = 8082
c.ServerApp.allow_origin = '*'
c.ServerApp.allow_remote_access = True

# Security settings
c.ServerApp.token = ''
c.ServerApp.password = ''
c.ServerApp.disable_check_xsrf = True

# Directory settings
c.ServerApp.root_dir = '/home/labuser/workspace'
c.ServerApp.preferred_dir = '/home/labuser/workspace/notebooks'

# UI settings
c.ServerApp.open_browser = False
c.LabApp.default_url = '/lab'

# Extension settings
c.ServerApp.nbserver_extensions = {
    'jupyterlab': True
}

# Kernel settings
c.MappingKernelManager.default_kernel_name = 'python3'

# File settings
c.ContentsManager.allow_hidden = True
c.FileContentsManager.delete_to_trash = False

# Terminal settings
c.ServerApp.terminals_enabled = True