# AI Assistant Service - Docker Deployment Guide

## Overview

The AI Assistant Service is fully dockerized and integrated into the Course Creator Platform's docker-compose orchestration.

---

## Docker Configuration

### Dockerfile

**Location:** `/services/ai-assistant-service/Dockerfile`

**Base Image:** `course-creator-base:latest`

**Key Features:**
- Uses shared base image for system packages
- Mounts virtual environment from host (`.venv`)
- Runs as non-root user (`appuser`)
- Exposes port 8011
- Includes SSL/TLS support

```dockerfile
FROM course-creator-base:latest

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    AI_ASSISTANT_PORT=8011 \
    LOG_LEVEL=INFO

COPY . .

RUN mkdir -p /var/log/course-creator
RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8011

CMD ["python", "main.py"]
```

---

## Docker Compose Configuration

### Service Definition

**Location:** `docker-compose.yml` (lines 683-736)

```yaml
ai-assistant-service:
  image: course-creator-ai-assistant:latest
  build:
    context: ./services/ai-assistant-service
    dockerfile: Dockerfile
    cache_from:
      - course-creator-ai-assistant:latest
  env_file:
    - .cc_env
  environment:
    - ENVIRONMENT=docker
    - DOCKER_CONTAINER=true
    - SERVICE_NAME=ai-assistant-service
    - LOG_LEVEL=INFO
    - AI_ASSISTANT_PORT=8011
    - RAG_SERVICE_URL=https://rag-service:8009
    - NLP_SERVICE_URL=https://nlp-preprocessing:8013
    - KG_SERVICE_URL=https://knowledge-graph-service:8012
    - PLATFORM_API_URL=https://localhost
    - LLM_PROVIDER=${LLM_PROVIDER:-openai}
    - OPENAI_API_KEY=${OPENAI_API_KEY:-}
    - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-}
    - SSL_CERT_PATH=/app/ssl/cert.pem
    - SSL_KEY_PATH=/app/ssl/key.pem
    - PYTHONPATH=/app:/app/.venv/lib/python3.12/site-packages
    - VIRTUAL_ENV=/app/.venv
  ports:
    - "8011:8011"
  volumes:
    - ./.venv:/app/.venv:ro
    - ./shared:/app/shared:ro
    - ./logs:/var/log/course-creator
    - ./ssl:/app/ssl:ro
  networks:
    - course-creator-network
  depends_on:
    rag-service:
      condition: service_healthy
    nlp-preprocessing:
      condition: service_healthy
    knowledge-graph-service:
      condition: service_healthy
    user-management:
      condition: service_healthy
    organization-management:
      condition: service_healthy
    course-management:
      condition: service_healthy
  healthcheck:
    test: ["CMD", "python", "-c", "import requests; r = requests.get('https://localhost:8011/api/v1/ai-assistant/health', verify=False); exit(0 if r.status_code == 200 else 1)"]
    interval: 30s
    timeout: 10s
    retries: 3
  restart: unless-stopped
```

### Service Dependencies

The AI Assistant Service depends on **6 services**:

1. **rag-service** (port 8009) - Codebase knowledge and retrieval
2. **nlp-preprocessing** (port 8013) - Intent classification, entity extraction
3. **knowledge-graph-service** (port 8012) - Course recommendations, learning paths
4. **user-management** (port 8000) - User authentication and context
5. **organization-management** (port 8008) - Organization context
6. **course-management** (port 8004) - Course operations

All dependencies must be **healthy** before the AI Assistant Service starts.

---

## Environment Variables

### Required Variables

Add to `.cc_env` or set in environment:

```bash
# LLM Provider (openai or claude)
LLM_PROVIDER=openai

# API Keys (at least one required)
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-...

# Service Configuration (set by docker-compose)
AI_ASSISTANT_PORT=8011
RAG_SERVICE_URL=https://rag-service:8009
NLP_SERVICE_URL=https://nlp-preprocessing:8013
KG_SERVICE_URL=https://knowledge-graph-service:8012
PLATFORM_API_URL=https://localhost

# SSL/TLS Configuration
SSL_CERT_PATH=/app/ssl/cert.pem
SSL_KEY_PATH=/app/ssl/key.pem

# Logging
LOG_LEVEL=INFO
```

### Optional Variables

```bash
# Maximum reconnection attempts (default: 5)
MAX_RECONNECT_ATTEMPTS=5

# Reconnection delay in ms (default: 2000)
RECONNECT_DELAY=2000

# WebSocket timeout in seconds (default: 30)
WEBSOCKET_TIMEOUT=30
```

---

## Deployment

### Build and Start

```bash
# Build the service
docker-compose build ai-assistant-service

# Start the service (and all dependencies)
docker-compose up -d ai-assistant-service

# View logs
docker-compose logs -f ai-assistant-service
```

### Startup Sequence

```
1. postgres (database)
2. redis (cache)
3. user-management, organization-management, course-management
4. rag-service (codebase indexing)
5. nlp-preprocessing (intent classification)
6. knowledge-graph-service (course relationships)
7. ai-assistant-service ✅

Total startup time: ~60-90 seconds
```

### Health Check

The service is considered healthy when:
- HTTPS endpoint `/api/v1/ai-assistant/health` returns 200
- LLM service is initialized
- RAG service is connected (optional)
- NLP service is connected (optional)
- Knowledge Graph service is connected (optional)
- Function executor is initialized

```bash
# Check health
curl -k https://localhost:8011/api/v1/ai-assistant/health

# Expected response:
{
  "service": "ai-assistant",
  "status": "healthy",
  "llm_service": "connected",
  "rag_service": "connected",
  "nlp_service": "connected",
  "kg_service": "connected",
  "function_executor": "connected"
}
```

---

## Networking

### Internal Communication

Services communicate via Docker network `course-creator-network`:

```
ai-assistant-service:8011
    ↓
    ├─→ rag-service:8009 (HTTPS)
    ├─→ nlp-preprocessing:8013 (HTTPS)
    ├─→ knowledge-graph-service:8012 (HTTPS)
    ├─→ user-management:8000 (HTTPS)
    ├─→ organization-management:8008 (HTTPS)
    └─→ course-management:8004 (HTTPS)
```

### External Access

- **WebSocket:** `wss://localhost:8011/ws/ai-assistant`
- **REST API:** `https://localhost:8011/api/v1/ai-assistant/*`

---

## Volume Mounts

### Read-Only Mounts

```yaml
volumes:
  - ./.venv:/app/.venv:ro              # Python dependencies
  - ./shared:/app/shared:ro            # Shared utilities
  - ./ssl:/app/ssl:ro                  # SSL certificates
```

### Read-Write Mounts

```yaml
volumes:
  - ./logs:/var/log/course-creator     # Service logs
```

---

## Logs

### Location

Logs are written to `/var/log/course-creator/ai-assistant-service.log` inside the container, mounted from `./logs` on the host.

### View Logs

```bash
# View all logs
docker-compose logs ai-assistant-service

# Follow logs in real-time
docker-compose logs -f ai-assistant-service

# View last 100 lines
docker-compose logs --tail=100 ai-assistant-service

# View logs from file
tail -f logs/ai-assistant-service.log
```

### Log Levels

- **INFO**: Normal operations (startup, requests, responses)
- **WARNING**: Non-critical issues (service unavailable, degraded mode)
- **ERROR**: Critical issues (initialization failures, LLM errors)

---

## Troubleshooting

### Issue 1: Service Won't Start

**Symptoms:**
- Container exits immediately
- "Service unhealthy" in docker-compose

**Diagnosis:**
```bash
# Check logs
docker-compose logs ai-assistant-service

# Check service status
docker-compose ps ai-assistant-service

# Check dependencies
docker-compose ps | grep -E "(rag-service|nlp-preprocessing|knowledge-graph-service)"
```

**Solutions:**
1. Ensure all dependencies are healthy
2. Check API keys are set (`OPENAI_API_KEY` or `ANTHROPIC_API_KEY`)
3. Verify SSL certificates exist in `./ssl/`
4. Check Python dependencies in `.venv`

### Issue 2: Health Check Failing

**Symptoms:**
- Container running but marked "unhealthy"
- Cannot connect to WebSocket

**Diagnosis:**
```bash
# Test health endpoint
curl -k https://localhost:8011/api/v1/ai-assistant/health

# Check if port is bound
netstat -tulpn | grep 8011

# Check container logs
docker logs course-creator-ai-assistant-service-1
```

**Solutions:**
1. Check if service is actually listening on 8011
2. Verify SSL certificates are valid
3. Check if dependent services are healthy
4. Restart the service: `docker-compose restart ai-assistant-service`

### Issue 3: Cannot Connect to Dependencies

**Symptoms:**
- Warnings in logs: "⚠ RAG Service not reachable"
- Degraded functionality

**Diagnosis:**
```bash
# Check if dependent services are running
docker-compose ps rag-service nlp-preprocessing knowledge-graph-service

# Test connectivity from container
docker exec -it course-creator-ai-assistant-service-1 \
  curl -k https://rag-service:8009/api/v1/rag/health
```

**Solutions:**
1. Ensure all dependent services are started and healthy
2. Check Docker network: `docker network inspect course-creator-network`
3. Restart services in order: `docker-compose restart rag-service nlp-preprocessing knowledge-graph-service ai-assistant-service`

### Issue 4: High Memory Usage

**Symptoms:**
- Container using > 2GB RAM
- System running slow

**Diagnosis:**
```bash
# Check container stats
docker stats course-creator-ai-assistant-service-1

# Check process memory inside container
docker exec -it course-creator-ai-assistant-service-1 ps aux
```

**Solutions:**
1. Add memory limit to docker-compose.yml:
   ```yaml
   deploy:
     resources:
       limits:
         memory: 2G
   ```
2. Reduce conversation deduplication threshold
3. Enable LLM response caching
4. Use lighter LLM model (GPT-3.5-turbo instead of GPT-4)

### Issue 5: WebSocket Connections Dropping

**Symptoms:**
- Frontend disconnects frequently
- "WebSocket connection closed" errors

**Diagnosis:**
```bash
# Check WebSocket connections
docker exec -it course-creator-ai-assistant-service-1 \
  netstat -an | grep 8011

# Check logs for disconnections
docker logs course-creator-ai-assistant-service-1 | grep "WebSocket"
```

**Solutions:**
1. Increase WebSocket timeout in environment variables
2. Check if NGINX is properly configured for WebSocket proxying
3. Verify SSL certificates are not expired
4. Check network stability between containers

---

## Monitoring

### Health Check Endpoint

```bash
# Check service health
curl -k https://localhost:8011/api/v1/ai-assistant/health

# Expected response (healthy):
{
  "service": "ai-assistant",
  "status": "healthy",
  "llm_service": "connected",
  "rag_service": "connected",
  "nlp_service": "connected",
  "kg_service": "connected",
  "function_executor": "connected"
}
```

### Statistics Endpoint

```bash
# Get service statistics
curl -k https://localhost:8011/api/v1/ai-assistant/stats

# Expected response:
{
  "active_conversations": 5,
  "total_messages_processed": 127,
  "average_response_time_ms": 1250,
  "llm_calls": 85,
  "llm_calls_skipped": 42,
  "token_savings": 31500,
  "cost_savings_usd": 0.945
}
```

### Prometheus Metrics (Optional)

If Prometheus is configured:

```bash
# Metrics endpoint
curl -k https://localhost:8011/metrics

# Key metrics:
# - ai_assistant_active_conversations
# - ai_assistant_messages_total
# - ai_assistant_response_time_seconds
# - ai_assistant_llm_calls_total
# - ai_assistant_tokens_saved_total
```

---

## Scaling

### Horizontal Scaling

The AI Assistant Service can be scaled horizontally:

```bash
# Scale to 3 replicas
docker-compose up -d --scale ai-assistant-service=3
```

**Requirements for horizontal scaling:**
1. Load balancer (NGINX) to distribute WebSocket connections
2. Session affinity (sticky sessions) for WebSocket connections
3. Shared Redis for conversation state (currently in-memory)

### Vertical Scaling

**Resource Limits:**

```yaml
# Add to docker-compose.yml
ai-assistant-service:
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 4G
      reservations:
        cpus: '1'
        memory: 2G
```

---

## Backup and Recovery

### Configuration Backup

```bash
# Backup environment variables
cp .cc_env .cc_env.backup

# Backup docker-compose configuration
cp docker-compose.yml docker-compose.yml.backup
```

### No Persistent Data

The AI Assistant Service is **stateless** - no persistent data to backup:
- Conversation state is in-memory
- No database writes
- Dependent services handle persistence

### Recovery

```bash
# Stop and remove container
docker-compose down ai-assistant-service

# Rebuild and restart
docker-compose build --no-cache ai-assistant-service
docker-compose up -d ai-assistant-service
```

---

## Security

### SSL/TLS

- All internal communication uses HTTPS
- SSL certificates mounted from `./ssl/`
- Certificates shared across all services

### API Keys

- LLM API keys stored in `.cc_env`
- Not included in Docker image
- Passed as environment variables at runtime

### Network Isolation

- Service runs in isolated Docker network
- Only exposed port is 8011
- Internal services not accessible from host

### User Permissions

- Service runs as non-root user (`appuser`)
- Limited file system permissions
- Read-only mounts where possible

---

## Performance Tuning

### Environment Variables

```bash
# Increase WebSocket connections
WEBSOCKET_MAX_CONNECTIONS=100

# Enable response caching
ENABLE_LLM_CACHE=true
LLM_CACHE_TTL=3600

# Reduce preprocessing overhead
NLP_BATCH_SIZE=10
NLP_CACHE_SIZE=1000
```

### Docker Resource Limits

```yaml
# Optimal settings for production
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 3G
    reservations:
      cpus: '1'
      memory: 1.5G
```

---

## Summary

✅ **Dockerfile created** - Uses base image, runs as non-root
✅ **Docker Compose configured** - Full service orchestration
✅ **Dependencies defined** - 6 service dependencies with health checks
✅ **Environment variables configured** - LLM keys, service URLs
✅ **Health checks implemented** - 30s interval, 3 retries
✅ **Networking configured** - Internal Docker network
✅ **Volume mounts configured** - Logs, SSL, dependencies
✅ **Auto-restart enabled** - Unless stopped manually

**Status:** ✅ **PRODUCTION READY FOR DOCKER DEPLOYMENT**

---

## Quick Start

```bash
# 1. Set environment variables
echo "LLM_PROVIDER=openai" >> .cc_env
echo "OPENAI_API_KEY=sk-..." >> .cc_env

# 2. Build service
docker-compose build ai-assistant-service

# 3. Start service (with dependencies)
docker-compose up -d ai-assistant-service

# 4. Check health
curl -k https://localhost:8011/api/v1/ai-assistant/health

# 5. Test WebSocket
# Open browser: https://localhost:3000
# Login as organization admin
# Click AI assistant button (bottom-right)
# Send message: "Hello"
```

---

**Created:** 2025-10-11
**Version:** 1.0.0
**Docker Image:** course-creator-ai-assistant:latest
**Port:** 8011 (HTTPS + WebSocket)
