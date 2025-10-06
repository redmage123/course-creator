#!/usr/bin/env python3
"""
Lab Manager Service Runner

BUSINESS REQUIREMENT:
Standalone runner for the Lab Manager service providing consistent service
startup patterns across all Course Creator platform microservices.

TECHNICAL IMPLEMENTATION:
- Imports and runs the main FastAPI application from main.py
- Provides consistent service entry point matching other services
- Enables direct service execution with `python run.py`
- Maintains compatibility with Docker container execution

USAGE:
python run.py  # Start lab manager service on port 8006
"""

if __name__ == "__main__":
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