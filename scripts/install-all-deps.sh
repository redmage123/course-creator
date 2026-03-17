#!/bin/bash

# Install all service dependencies into local .venv
# This avoids pip downloads during Docker builds

set -e

echo "Installing all service dependencies into local .venv..."

# Activate virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

source .venv/bin/activate

# Install dependencies from each service
echo "Installing dependencies from all services..."

for requirements_file in $(find services/ -name "requirements.txt"); do
    echo "Installing from $requirements_file..."
    pip install -r "$requirements_file"
done

# Also install lab container requirements if they exist
if [ -f "lab-containers/requirements.txt" ]; then
    echo "Installing lab container dependencies..."
    pip install -r "lab-containers/requirements.txt"
fi

# Install root requirements if they exist
if [ -f "requirements.txt" ]; then
    echo "Installing root dependencies..."
    pip install -r "requirements.txt"
fi

echo "✅ All dependencies installed in .venv"
echo "📦 Virtual environment location: $(pwd)/.venv"
echo "🐍 Python location: $(which python)"
echo "📋 Installed packages: $(pip list | wc -l) packages"