# RAG Service Dockerfile - Two-Stage Requirements Installation
# Uses shared base image for system packages, then installs requirements in layers

FROM course-creator-base:latest

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    CHROMADB_PATH=/app/chromadb_data \
    TRANSFORMERS_CACHE=/app/.cache/huggingface \
    HF_HOME=/app/.cache/huggingface \
    TOKENIZERS_PARALLELISM=false

# Use mounted virtual environment - no pip installs needed
# Virtual environment will be mounted from host at runtime

# Copy application code
COPY . .

# Create necessary directories for RAG service
RUN mkdir -p /app/chromadb_data /app/.cache/huggingface

# Use existing appuser from base image and fix ownership
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8009

CMD ["python", "main.py"]