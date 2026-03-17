# Knowledge Graph Service Dockerfile

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8012

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f -k https://localhost:8012/health || exit 1

# Run the application with SSL
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8012", "--ssl-keyfile", "/app/ssl/nginx-selfsigned.key", "--ssl-certfile", "/app/ssl/nginx-selfsigned.crt"]
