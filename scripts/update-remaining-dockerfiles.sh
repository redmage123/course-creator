#!/bin/bash

# Script to update remaining Dockerfiles to use mounted .venv approach
# Based on Claude directive to use memory system and established template pattern

set -e

echo "Updating remaining Dockerfiles to use mounted .venv..."

# Function to create venv-based Dockerfile
create_venv_dockerfile() {
    local service_name="$1"
    local port="$2"
    local dockerfile_path="services/$service_name/Dockerfile"
    
    echo "Updating $dockerfile_path..."
    
    cat > "$dockerfile_path" << EOF
# $service_name Service Dockerfile - Using mounted .venv
# No pip installs - uses pre-installed packages from mounted virtual environment

FROM python:3.10-slim

# Install minimal system dependencies
RUN apt-get update && apt-get install -y \\
    libpq-dev \\
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Set environment variables to use mounted venv
# PATH and VIRTUAL_ENV will be set by docker-compose environment
ENV PYTHONDONTWRITEBYTECODE=1 \\
    PYTHONUNBUFFERED=1 \\
    PYTHONPATH=/app

# Copy application code
COPY . .

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser && \\
    chown -R appuser:appuser /app
USER appuser

# The virtual environment directory will be mounted from host
# Path configured via VENV_MOUNT_PATH environment variable in docker-compose.yml
# No pip install needed!

EXPOSE $port

CMD ["python", "main.py"]
EOF
}

# Update remaining services
create_venv_dockerfile "course-management" "8004"
create_venv_dockerfile "content-management" "8005" 
create_venv_dockerfile "analytics" "8007"
create_venv_dockerfile "organization-management" "8008"

# RAG service (special case - different port)
echo "Updating services/rag-service/Dockerfile..."
cat > "services/rag-service/Dockerfile" << 'EOF'
# RAG Service Dockerfile - Using mounted .venv
# No pip installs - uses pre-installed packages from mounted virtual environment

FROM python:3.10-slim

# Install minimal system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Set environment variables to use mounted venv
# PATH and VIRTUAL_ENV will be set by docker-compose environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Copy application code
COPY . .

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser && \
    chown -R appuser:appuser /app
USER appuser

# The virtual environment directory will be mounted from host
# Path configured via VENV_MOUNT_PATH environment variable in docker-compose.yml
# No pip install needed!

EXPOSE 8009

CMD ["python", "main.py"]
EOF

# Lab manager (special case - different path and port)
echo "Updating lab-containers/Dockerfile..."
cat > "lab-containers/Dockerfile" << 'EOF'
# Lab Manager Service Dockerfile - Using mounted .venv
# No pip installs - uses pre-installed packages from mounted virtual environment

FROM python:3.10-slim

# Install minimal system dependencies for Docker operations
RUN apt-get update && apt-get install -y \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Set environment variables to use mounted venv
# PATH and VIRTUAL_ENV will be set by docker-compose environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Copy application code
COPY . .

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser && \
    chown -R appuser:appuser /app
USER appuser

# The virtual environment directory will be mounted from host
# Path configured via VENV_MOUNT_PATH environment variable in docker-compose.yml
# No pip install needed!

EXPOSE 8006

CMD ["python", "main.py"]
EOF

echo "✅ All Dockerfiles updated to use mounted .venv approach"
echo "📦 No pip installs will occur during Docker builds"
echo "🔧 Run ./install-all-deps.sh first to prepare local .venv"