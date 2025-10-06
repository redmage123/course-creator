FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create certs directory for SSL (will be mounted from host)
RUN mkdir -p /app/certs

# Expose port
EXPOSE 8013

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import warnings; warnings.filterwarnings('ignore'); import requests; r = requests.get('https://localhost:8013/health', verify=False); exit(0 if r.status_code == 200 else 1)"

# Run the service
CMD ["python", "main.py"]
