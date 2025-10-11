# Local LLM Service Dockerfile
#
# This service provides local LLM inference using Llama 3.1 8B via Ollama
# Connects to Ollama running on the host machine with GPU acceleration
#

FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY local_llm_service/ ./local_llm_service/
COPY main.py .

# Create non-root user
RUN useradd -m -u 1000 llmuser && \
    chown -R llmuser:llmuser /app
USER llmuser

# Expose service port
EXPOSE 8015

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8015/health || exit 1

# Start service
CMD ["python3", "main.py"]
