# Optimized RAG Service Dockerfile with Build Cache and Error Handling
# Fixes SentenceTransformer download issues and dramatically improves build times

# Use BuildKit for advanced caching features
# syntax=docker/dockerfile:1.4

# Stage 1: Base system dependencies (cached for weeks/months)
FROM python:3.11-slim as system-base

# Install system dependencies with aggressive caching
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    rm -f /etc/apt/apt.conf.d/docker-clean && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        build-essential \
        sqlite3 \
        curl \
        ca-certificates \
        git \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Stage 2: Python base packages (cached when requirements don't change)
FROM system-base as python-deps

WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python packages with persistent cache
RUN --mount=type=cache,target=/root/.cache/pip,sharing=locked \
    pip install --upgrade pip setuptools wheel && \
    pip install --no-deps -r requirements.txt || \
    (echo "First attempt failed, retrying with individual packages..." && \
     pip install --no-deps fastapi uvicorn pydantic python-dotenv structlog && \
     pip install --no-deps numpy scipy && \
     pip install --no-deps httpx aiohttp redis aioredis && \
     pip install --no-deps pandas pyarrow python-dateutil python-multipart && \
     pip install --no-deps pytest pytest-asyncio pytest-mock && \
     pip install --no-deps pydantic-settings)

# Stage 3: AI/ML dependencies with error handling (most problematic stage)
FROM python-deps as ml-deps

# Set environment variables for better model downloading
ENV TRANSFORMERS_CACHE=/app/.cache/huggingface \
    TORCH_HOME=/app/.cache/torch \
    HF_HOME=/app/.cache/huggingface \
    TOKENIZERS_PARALLELISM=false \
    HF_HUB_DISABLE_PROGRESS_BARS=1 \
    HF_HUB_DISABLE_TELEMETRY=1

# Create cache directories
RUN mkdir -p /app/.cache/huggingface /app/.cache/torch

# Install AI/ML packages with retry logic and fallbacks
RUN --mount=type=cache,target=/root/.cache/pip,sharing=locked \
    --mount=type=cache,target=/app/.cache/huggingface,sharing=locked \
    --mount=type=cache,target=/app/.cache/torch,sharing=locked \
    ( \
        echo "Installing ChromaDB and AI dependencies..." && \
        pip install --no-deps chromadb==0.4.18 || \
        pip install chromadb==0.4.15 || \
        pip install chromadb \
    ) && \
    ( \
        echo "Installing SentenceTransformers..." && \
        pip install --no-deps sentence-transformers==2.2.2 || \
        pip install sentence-transformers==2.0.0 || \
        pip install sentence-transformers \
    ) && \
    ( \
        echo "Installing OpenAI client..." && \
        pip install --no-deps openai==1.3.0 || \
        pip install openai \
    )

# Stage 4: Model download with comprehensive error handling
FROM ml-deps as model-cache

# Download models with multiple fallback strategies
RUN --mount=type=cache,target=/app/.cache/huggingface,sharing=locked \
    --mount=type=cache,target=/app/.cache/torch,sharing=locked \
    python -c "
import sys
import time
import os

# Set cache paths
os.environ['TRANSFORMERS_CACHE'] = '/app/.cache/huggingface'
os.environ['TORCH_HOME'] = '/app/.cache/torch'
os.environ['HF_HOME'] = '/app/.cache/huggingface'

def download_model_with_retries(model_name, max_retries=3):
    for attempt in range(max_retries):
        try:
            print(f'Attempt {attempt + 1}: Downloading {model_name}...')
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer(model_name, cache_folder='/app/.cache/huggingface')
            print(f'Successfully downloaded {model_name}')
            return True
        except Exception as e:
            print(f'Attempt {attempt + 1} failed: {str(e)}')
            if attempt < max_retries - 1:
                print('Retrying in 5 seconds...')
                time.sleep(5)
            else:
                print(f'All attempts failed for {model_name}')
                return False

# Try multiple model options
models_to_try = [
    'all-MiniLM-L6-v2',
    'all-mpnet-base-v2', 
    'paraphrase-MiniLM-L6-v2'
]

success = False
for model in models_to_try:
    if download_model_with_retries(model):
        success = True
        break

if not success:
    print('Warning: No models could be downloaded. Will download at runtime.')
    # Create empty cache structure so container doesn't fail
    import os
    os.makedirs('/app/.cache/huggingface/sentence_transformers', exist_ok=True)
else:
    print('Model download completed successfully')
"

# Stage 5: Final runtime image
FROM system-base as runtime

WORKDIR /app

# Set optimized environment variables
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    CHROMADB_PATH=/app/chromadb_data \
    LOG_DIR=/var/log/course-creator \
    TRANSFORMERS_CACHE=/app/.cache/huggingface \
    TORCH_HOME=/app/.cache/torch \
    HF_HOME=/app/.cache/huggingface \
    TOKENIZERS_PARALLELISM=false \
    HF_HUB_DISABLE_PROGRESS_BARS=1 \
    HF_HUB_DISABLE_TELEMETRY=1

# Create non-root user first
RUN groupadd -r appuser && useradd -r -g appuser -m appuser

# Copy Python packages from deps stage
COPY --from=model-cache /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=model-cache /usr/local/bin /usr/local/bin

# Copy model cache with proper ownership
COPY --from=model-cache --chown=appuser:appuser /app/.cache /home/appuser/.cache

# Create necessary directories
RUN mkdir -p /app/chromadb_data /var/log/course-creator /app/logs /app/outputs && \
    chown -R appuser:appuser /app /home/appuser /var/log/course-creator

# Copy application code (this layer changes most frequently)
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8009

# Optimized health check without external dependencies
HEALTHCHECK --interval=30s --timeout=10s --start-period=45s --retries=3 \
    CMD python -c "
import sys
try:
    import requests
    response = requests.get('http://localhost:8009/api/v1/rag/health', timeout=5)
    sys.exit(0 if response.status_code == 200 else 1)
except Exception:
    sys.exit(1)
" || exit 1

# Start command with error handling
CMD ["python", "main.py"]