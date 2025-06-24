FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir fastapi uvicorn anthropic hydra-core omegaconf

COPY shared/ ./shared/
COPY services/content-generator/ ./
COPY config/ ./config/

EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
