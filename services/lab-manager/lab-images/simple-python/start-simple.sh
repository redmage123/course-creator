#!/bin/bash

# Simple multi-service startup script
echo "Starting Simple Python Lab Environment..."

# Start JupyterLab in background
jupyter lab --ip=0.0.0.0 --port=8081 --no-browser --allow-root --NotebookApp.token='' --NotebookApp.password='' &

# Start code-server in background  
code-server --bind-addr 0.0.0.0:8080 --auth none --disable-telemetry /home/labuser/workspace &

# Start Jupyter Notebook in background
jupyter notebook --ip=0.0.0.0 --port=8082 --no-browser --allow-root --NotebookApp.token='' --NotebookApp.password='' &

# Keep the container running
echo "All services started. Lab environment ready."
tail -f /dev/null