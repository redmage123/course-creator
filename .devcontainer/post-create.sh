#!/bin/bash
set -e

echo "=== Setting up Course Creator development environment ==="

# Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt 2>/dev/null || echo "Note: some optional dependencies may have failed"
pip install pytest pytest-asyncio pytest-cov black isort flake8 bandit

# Node dependencies (frontend)
if [ -f "package.json" ]; then
    echo "Installing Node dependencies..."
    npm install --legacy-peer-deps 2>/dev/null || npm install --force 2>/dev/null || true
fi

# Database setup
echo "Setting up development database..."
python setup-database-ci.py 2>/dev/null || echo "DB setup script not found — run manually if needed"

echo ""
echo "============================================"
echo "  Course Creator dev environment is ready!"
echo "============================================"
echo ""
echo "  Services:"
echo "    PostgreSQL: localhost:5432 (postgres/postgres)"
echo "    Redis:      localhost:6379"
echo ""
echo "  Quick start:"
echo "    pytest tests/ -m unit          # Run unit tests"
echo "    pytest tests/ -m integration   # Run integration tests"
echo "    python -m pytest --co -q       # List all tests"
echo ""
echo "  Full stack (Docker):"
echo "    docker compose up -d           # Start all 22 services"
echo "    docker compose ps              # Check status"
echo ""
