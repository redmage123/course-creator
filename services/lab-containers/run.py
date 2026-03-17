#!/usr/bin/env python3
"""
Lab Containers Service Runner (Alias for Lab Manager)

BUSINESS REQUIREMENT:
This is an alias service that redirects to the lab-manager service to maintain
compatibility with Kubernetes deployments that reference "lab-containers" while
the Docker Compose setup uses "lab-manager".

TECHNICAL IMPLEMENTATION:
- Provides consistent service entry point for lab-containers naming
- Redirects to lab-manager main application
- Maintains compatibility with both naming conventions
- Enables direct service execution with `python run.py`

USAGE:
python run.py  # Start lab containers service on port 8006

NOTE:
This service is functionally identical to lab-manager. The separate directory
exists to support multiple deployment naming conventions (Kubernetes vs Docker).
"""

if __name__ == "__main__":
    import sys
    import os

    # Add lab-manager to the Python path to import its main module
    lab_manager_path = os.path.join(os.path.dirname(__file__), '..', 'lab-manager')
    sys.path.insert(0, lab_manager_path)

    from main import app
    import uvicorn

    # Run the FastAPI application
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8006,
        reload=False,  # Disable in production
        access_log=True
    )
