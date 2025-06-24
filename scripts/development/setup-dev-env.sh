#!/bin/bash
# Development environment setup

set -e

echo "🚀 Setting up Course Creator development environment..."

# Check dependencies
echo "📋 Checking dependencies..."
if ! command -v python3.11 &> /dev/null; then
    echo "❌ Python 3.11 not found. Please install Python 3.11+"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker"
    exit 1
fi

# Create virtual environment
echo "🐍 Creating Python virtual environment..."
python3.11 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install fastapi uvicorn anthropic hydra-core omegaconf sqlalchemy redis docker httpx

# Copy environment file
if [ ! -f .env ]; then
    echo "📄 Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please update .env with your API keys"
fi

echo "✅ Development environment setup complete!"
