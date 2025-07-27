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
RUN groupadd -r labuser && useradd -r -g labuser labuser
RUN chown -R labuser:labuser /app

# Note: We need privileged mode for Docker-in-Docker, so we can't drop privileges here
# USER labuser

# Expose port
EXPOSE 8006

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8006/health')"

# Run the application
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8006"]