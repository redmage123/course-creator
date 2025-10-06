#!/usr/bin/env python3
"""
Analytics Service Runner
Runs the student analytics FastAPI service using the shared course creator database
"""

import os
import sys
import uvicorn
from pathlib import Path

# Add the services directory to the Python path
services_dir = Path(__file__).parent.parent
sys.path.insert(0, str(services_dir))

# Import the FastAPI app
from analytics.main import app

if __name__ == "__main__":
    # Environment configuration
    host = os.getenv("ANALYTICS_HOST", "0.0.0.0")
    port = int(os.getenv("ANALYTICS_PORT", 8007))
    debug = os.getenv("DEBUG", "False").lower() == "true"
    
    print(f"Starting Analytics Service on {host}:{port}")
    print(f"Using shared course creator database")
    print(f"Debug mode: {debug}")
    
    # Run the application
    uvicorn.run(
        "analytics.main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info" if not debug else "debug"
    )