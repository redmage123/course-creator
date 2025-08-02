# Lab Manager Service Dockerfile
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Set work directory
WORKDIR /app

# Install system dependencies including Docker CLI
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create storage directories with proper permissions
RUN mkdir -p /app/lab-storage /app/templates

# For Docker socket access, create user with same UID as other services (999)
RUN groupadd -r appuser && useradd -r -g appuser -u 999 appuser
# Remove existing docker group if it exists and create with correct GID
RUN groupdel docker 2>/dev/null || true
RUN groupadd -g 123 docker
RUN usermod -aG docker appuser
RUN mkdir -p /var/log/course-creator && \
    chown -R appuser:appuser /app /var/log/course-creator && \
    chmod 755 /var/log/course-creator

# Use appuser for consistency with other services
USER appuser

# Expose port
EXPOSE 8006

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8006/health')"

# Run the application using Hydra
CMD ["python", "main.py"]