FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir fastapi uvicorn anthropic hydra-core omegaconf

COPY shared/ ./shared/
COPY services/api-gateway/ ./
COPY config/ ./config/

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
