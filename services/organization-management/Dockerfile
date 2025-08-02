# syntax=docker/dockerfile:1
# Organization Management Service Dockerfile - Optimized Multi-stage Build

# Stage 1: Base image with system dependencies (rarely changes)
FROM python:3.10-slim as base

# Install system dependencies with cache mount
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Stage 2: Python dependencies (changes occasionally)
FROM base as deps

WORKDIR /app

# Copy and install Python dependencies with pip cache
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

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

# Copy application code (most frequently changing layer)
COPY . .

# Create non-root user for security and set up permissions
RUN groupadd -r appuser && useradd -r -g appuser appuser && \
    mkdir -p /var/log/course-creator && \
    chown -R appuser:appuser /app /var/log/course-creator && \
    chmod -R 755 /var/log/course-creator
USER appuser

# Expose port
EXPOSE 8008

# Optimized health check with timeout
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD python -c "import requests; r = requests.get('http://localhost:8008/health', timeout=5); exit(0 if r.status_code == 200 else 1)" || exit 1

# Run the application
CMD ["python", "main.py"]