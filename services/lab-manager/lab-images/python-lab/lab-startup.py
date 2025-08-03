#!/usr/bin/env python3
"""
Python Lab Startup Script
Configures and starts the lab environment based on session parameters
"""

import os
import json
import subprocess
import sys
from pathlib import Path

def setup_lab_environment():
    """Set up the lab environment based on configuration"""
    
    # Get lab configuration from environment
    session_id = os.getenv('LAB_SESSION_ID', 'default')
    user_id = os.getenv('USER_ID', 'student')
    course_id = os.getenv('COURSE_ID', 'default-course')
    lab_config = json.loads(os.getenv('LAB_CONFIG', '{}'))
    
    print(f"Setting up Python lab for session: {session_id}")
    print(f"User: {user_id}, Course: {course_id}")
    
    workspace = Path('/home/labuser/workspace')
    
    # Create lab-specific directories
    (workspace / 'session_info.json').write_text(json.dumps({
        'session_id': session_id,
        'user_id': user_id,
        'course_id': course_id,
        'lab_type': 'python',
        'config': lab_config
    }, indent=2))
    
    # Install additional packages if specified
    if 'packages' in lab_config:
        packages = lab_config['packages']
        if packages:
            print(f"Installing additional packages: {packages}")
            subprocess.run([sys.executable, '-m', 'pip', 'install'] + packages)
    
    # Create starter files if specified
    if 'starter_files' in lab_config:
        for filename, content in lab_config['starter_files'].items():
            file_path = workspace / 'assignments' / filename
            file_path.parent.mkdir(exist_ok=True)
            file_path.write_text(content)
            print(f"Created starter file: {filename}")
    
    # Create a welcome notebook
    welcome_notebook = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    f"# Welcome to Python Lab\n\n",
                    f"**Session ID:** {session_id}\n",
                    f"**Course:** {course_id}\n",
                    f"**Lab Type:** Python Programming\n\n",
                    "## Getting Started\n\n",
                    "This is your Python programming lab environment. You can:\n\n",
                    "- Write and execute Python code in notebooks\n",
                    "- Access your assignments in the `assignments/` folder\n",
                    "- Save your work in the `workspace/` folder\n",
                    "- View example solutions in the `solutions/` folder (when available)\n\n",
                    "## Available Libraries\n\n",
                    "Common libraries are pre-installed:\n",
                    "- NumPy, Pandas for data manipulation\n",
                    "- Matplotlib, Seaborn for visualization\n",
                    "- Requests for HTTP operations\n",
                    "- Flask, FastAPI for web development\n",
                    "- Pytest for testing\n\n",
                    "Happy coding! 🐍"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "source": [
                    "# Test your Python environment\n",
                    "import sys\n",
                    "import numpy as np\n",
                    "import pandas as pd\n",
                    "import matplotlib.pyplot as plt\n",
                    "\n",
                    "print(f\"Python version: {sys.version}\")\n",
                    "print(f\"NumPy version: {np.__version__}\")\n",
                    "print(f\"Pandas version: {pd.__version__}\")\n",
                    "print(\"\\n✅ Lab environment is ready!\")"
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
                "version": "3.10"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 4
    }
    
    (workspace / 'Welcome.ipynb').write_text(json.dumps(welcome_notebook, indent=2))
    
    print("Lab environment setup complete!")

def start_jupyter():
    """Start JupyterLab server"""
    print("Starting JupyterLab...")
    
    # JupyterLab configuration
    cmd = [
        'jupyter', 'lab',
        '--ip=0.0.0.0',
        '--port=8080',
        '--no-browser',
        '--allow-root',
        '--NotebookApp.token=""',
        '--NotebookApp.password=""',
        '--NotebookApp.allow_origin="*"',
        '--NotebookApp.disable_check_xsrf=True'
    ]
    
    # Start JupyterLab
    subprocess.run(cmd)

if __name__ == "__main__":
    setup_lab_environment()
    start_jupyter()