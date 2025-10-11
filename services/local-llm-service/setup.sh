#!/bin/bash
#
# Local LLM Service Setup Script
#
# This script installs and configures the Local LLM Service:
# 1. Checks for Ollama installation
# 2. Installs Python dependencies
# 3. Pulls Llama 3.1 8B model
# 4. Runs tests to verify installation
#

set -e

echo "=========================================="
echo "Local LLM Service Setup"
echo "=========================================="
echo ""

# Check if Ollama is installed
echo "Checking for Ollama installation..."
if command -v ollama &> /dev/null; then
    echo "✓ Ollama is installed"
    ollama --version
else
    echo "✗ Ollama is not installed"
    echo ""
    echo "Please install Ollama from: https://ollama.ai/download"
    echo ""
    echo "On Linux:"
    echo "  curl -fsSL https://ollama.ai/install.sh | sh"
    echo ""
    echo "On macOS:"
    echo "  brew install ollama"
    echo ""
    exit 1
fi

echo ""

# Check if Ollama is running
echo "Checking if Ollama is running..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✓ Ollama is running"
else
    echo "⚠ Ollama is not running"
    echo "Starting Ollama..."
    ollama serve &
    sleep 5
fi

echo ""

# Install Python dependencies
echo "Installing Python dependencies..."
cd "$(dirname "$0")"
pip install -r requirements.txt
echo "✓ Dependencies installed"

echo ""

# Pull Llama 3.1 8B model
echo "Pulling Llama 3.1 8B model (4-bit quantized)..."
if ollama list | grep -q "llama3.1:8b-instruct-q4_K_M"; then
    echo "✓ Model already downloaded"
else
    echo "Downloading model (this may take a few minutes)..."
    ollama pull llama3.1:8b-instruct-q4_K_M
    echo "✓ Model downloaded"
fi

echo ""

# Verify model
echo "Verifying model installation..."
ollama list | grep "llama3.1"

echo ""

# Run tests
echo "Running tests..."
pytest tests/ -v --tb=short

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "To start the service:"
echo "  python main.py"
echo ""
echo "To test the service:"
echo "  curl http://localhost:8015/health"
echo ""
