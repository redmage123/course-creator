# Python Lab Environment with Multi-IDE Support
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    CODE_SERVER_VERSION=4.20.0

# Install system dependencies including Node.js for VSCode Server
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    nano \
    vim \
    build-essential \
    software-properties-common \
    ca-certificates \
    gnupg \
    lsb-release \
    openjdk-11-jdk \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js (required for some VSCode extensions)
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# Install code-server (VSCode Server)
RUN curl -fsSL https://code-server.dev/install.sh | sh

# Install Python packages for labs and IDEs
RUN pip install --no-cache-dir \
    jupyter \
    jupyterlab \
    notebook \
    numpy \
    pandas \
    matplotlib \
    seaborn \
    requests \
    flask \
    fastapi \
    pytest \
    black \
    pylint \
    autopep8 \
    rope \
    jedi \
    aiohttp \
    aiohttp-cors

# Install JetBrains Projector for IntelliJ IDEA (optional, resource intensive)
RUN pip install --no-cache-dir projector-installer

# Create lab user with limited privileges
RUN groupadd -r labuser && useradd -r -g labuser -m -d /home/labuser labuser

# Set up workspace and IDE directories
WORKDIR /home/labuser
RUN mkdir -p /home/labuser/{workspace,ide-configs,.local/share/code-server} \
    && chown -R labuser:labuser /home/labuser

# Switch to lab user for installations
USER labuser

# Install common VSCode extensions for Python
RUN code-server --install-extension ms-python.python \
    && code-server --install-extension ms-python.black-formatter \
    && code-server --install-extension ms-python.pylint \
    && code-server --install-extension ms-toolsai.jupyter

# Install PyCharm Community Edition via Projector (disabled by default)
# RUN projector install --accept-license --no-auto-run 'PyCharm Community Edition' --port 8083

# Create VSCode configuration
RUN mkdir -p /home/labuser/.local/share/code-server/User \
    && echo '{
        "workbench.colorTheme": "Default Dark+",
        "workbench.startupEditor": "none",
        "python.defaultInterpreterPath": "/usr/local/bin/python",
        "python.terminal.activateEnvironment": false,
        "jupyter.askForKernelRestart": false,
        "extensions.autoUpdate": false,
        "telemetry.telemetryLevel": "off"
    }' > /home/labuser/.local/share/code-server/User/settings.json

# Create Jupyter configuration
RUN mkdir -p /home/labuser/.jupyter \
    && echo "c = get_config()
c.ServerApp.ip = '0.0.0.0'
c.ServerApp.port = 8082
c.ServerApp.token = ''
c.ServerApp.password = ''
c.ServerApp.allow_origin = '*'
c.ServerApp.open_browser = False
c.ServerApp.root_dir = '/home/labuser/workspace'" > /home/labuser/.jupyter/jupyter_lab_config.py

# Set up workspace structure
WORKDIR /home/labuser/workspace
RUN mkdir -p {assignments,solutions,data,notebooks,projects,src}

# Create sample files for different IDEs
RUN echo '# Python Lab Workspace

Welcome to your Python lab environment! 

## Available IDEs:
- **Terminal**: Traditional command-line interface (Default)
- **VSCode**: Full-featured code editor with Python support
- **JupyterLab**: Notebook environment for data science and exploration

## Getting Started:
1. Choose your preferred IDE from the selection menu
2. Explore the workspace directories:
   - `assignments/` - Your lab assignments
   - `solutions/` - Reference solutions
   - `data/` - Data files for analysis
   - `notebooks/` - Jupyter notebooks
   - `projects/` - Your coding projects
   - `src/` - Source code files

Happy coding!
' > README.md

# Create a sample Python file
RUN echo '#!/usr/bin/env python3
"""
Sample Python file for Course Creator Lab
"""

def hello_world():
    """A simple hello world function"""
    print("Hello from Course Creator Lab!")
    return "Hello World"

def fibonacci(n):
    """Generate fibonacci sequence up to n"""
    a, b = 0, 1
    sequence = []
    while a < n:
        sequence.append(a)
        a, b = b, a + b
    return sequence

if __name__ == "__main__":
    hello_world()
    print("Fibonacci sequence up to 100:", fibonacci(100))
' > src/sample.py

# Create a sample Jupyter notebook
RUN echo '{
  "cells": [
    {
      "cell_type": "markdown",
      "metadata": {},
      "source": [
        "# Course Creator Lab - Sample Notebook\\n",
        "\\n",
        "Welcome to your Jupyter Lab environment!"
      ]
    },
    {
      "cell_type": "code",
      "execution_count": null,
      "metadata": {},
      "outputs": [],
      "source": [
        "# Sample Python code\\n",
        "import numpy as np\\n",
        "import matplotlib.pyplot as plt\\n",
        "\\n",
        "# Create sample data\\n",
        "x = np.linspace(0, 10, 100)\\n",
        "y = np.sin(x)\\n",
        "\\n",
        "# Plot\\n",
        "plt.figure(figsize=(10, 6))\\n",
        "plt.plot(x, y)\\n",
        "plt.title(\\"Sample Plot\\")\\n",
        "plt.show()"
      ]
    }
  ],
  "metadata": {
    "kernelspec": {
      "display_name": "Python 3",
      "language": "python",
      "name": "python3"
    },
    "language_info": {
      "name": "python",
      "version": "3.10.0"
    }
  },
  "nbformat": 4,
  "nbformat_minor": 4
}' > notebooks/sample.ipynb

# Copy IDE startup script
COPY --chown=labuser:labuser ide-startup.py /home/labuser/ide-startup.py

# Expose ports for different IDEs
# 8080: Main web interface and terminal
# 8081: VSCode Server
# 8082: JupyterLab
# 8083: PyCharm/IntelliJ (if enabled)
EXPOSE 8080 8081 8082 8083

# Health check for the main service
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8080/api/status || exit 1

# Start IDE management service
CMD ["python", "/home/labuser/ide-startup.py"]