# syntax=docker/dockerfile:1
# Content Management Service Dockerfile - Lightweight Python-based document processing
# Uses Python libraries instead of heavy system dependencies for faster builds

# Stage 1: Base image with minimal system dependencies
FROM python:3.10-slim as base

# Install only essential system dependencies
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    echo 'Acquire::Languages "none";' > /etc/apt/apt.conf.d/99disable-translations && \
    echo 'APT::Get::Assume-Yes "true";' > /etc/apt/apt.conf.d/99assume-yes && \
    echo 'APT::Install-Recommends "false";' > /etc/apt/apt.conf.d/99no-recommends && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        ca-certificates \
        curl && \
    # Clean up to reduce image size
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Stage 2: Python dependencies (changes occasionally)
FROM base as deps

WORKDIR /app

# Copy and install Python dependencies with pip cache
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir --compile -r requirements.txt && \
    # Clean up pip cache to reduce layer size
    pip cache purge || true

# Stage 3: Runtime (changes frequently)
FROM base as runtime

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Copy Python packages from deps stage
COPY --from=deps /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

# Create storage directories with proper permissions
RUN mkdir -p /app/storage /app/uploads /app/exports /app/temp

# Copy application code (most frequently changing layer)
COPY . .

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8005

# Optimized health check with timeout
HEALTHCHECK --interval=30s --timeout=15s --start-period=30s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8005/health', timeout=10)" || exit 1

# Run the application with optimized uvicorn settings
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8005", "--workers", "1", "--access-log"]