# ============================================================================
# NIMCP Service Dockerfile
# ============================================================================
# Lightweight Python service for NIMCP neuromorphic AI brain system
#
# Build Strategy:
#   Phase 1: Build without NIMCP library (service infrastructure only)
#   Phase 2: Add NIMCP library compilation once source is integrated
#
# Business Context:
#   This service provides the platform's self-aware learning brain system.
#   Currently builds without NIMCP library to test service infrastructure.
#   NIMCP library integration will be added in Phase 1 completion.
#
# Author: Course Creator Platform Team
# Version: 1.0.0
# Last Updated: 2025-11-09
# ============================================================================

FROM python:3.11-slim

# Metadata
LABEL maintainer="Course Creator Platform Team"
LABEL service="nimcp_service"
LABEL version="1.0.0"
LABEL description="Neuromorphic AI Brain System for Course Creator Platform"

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Create brain states directory for neural network persistence
RUN mkdir -p /app/brain_states && \
    chmod 777 /app/brain_states

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY . /app/

# Create non-root user for security
RUN useradd -m -u 1000 nimcp && \
    chown -R nimcp:nimcp /app /app/brain_states

# Switch to non-root user
USER nimcp

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV BRAIN_STATES_DIR=/app/brain_states
ENV NIMCP_SERVICE_PORT=8016
ENV LOG_LEVEL=INFO

# Expose service port
EXPOSE 8016

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8016/health').read()"

# Run the service
CMD ["python", "main.py"]
