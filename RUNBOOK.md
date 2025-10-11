# Course Creator Platform - Operations Runbook

> **Complete guide for installing, deploying, operating, and troubleshooting the Course Creator Platform**

**Version**: 3.3.0
**Last Updated**: 2025-10-11
**Audience**: DevOps Engineers, System Administrators, Platform Operators

---

## Table of Contents

- [Quick Reference](#quick-reference)
- [Installation](#installation)
- [Configuration](#configuration)
- [Deployment](#deployment)
- [Operations](#operations)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)
- [Maintenance](#maintenance)
- [Security](#security)
- [Disaster Recovery](#disaster-recovery)

---

## Quick Reference

### Essential Commands

```bash
# Start platform
./app-control.sh docker-start

# Check status
./app-control.sh status

# View logs
./app-control.sh logs <service-name>

# Stop platform
./app-control.sh docker-stop

# Health check all services
for port in 8000 8001 8003 8004 8005 8006 8007 8008 8015; do
  curl -s http://localhost:$port/health | jq
done

# Health check NLP preprocessing (HTTPS)
curl -k -s https://localhost:8013/health | jq

# Health check Local LLM Service
curl -s http://localhost:8015/health | jq
```

### Service Ports

| Service | Port | Health Check |
|---------|------|--------------|
| User Management | 8000 | http://localhost:8000/health |
| Course Generator | 8001 | http://localhost:8001/health |
| Content Storage | 8003 | http://localhost:8003/health |
| Course Management | 8004 | http://localhost:8004/health |
| Content Management | 8005 | http://localhost:8005/health |
| Lab Manager | 8006 | http://localhost:8006/health |
| Analytics | 8007 | http://localhost:8007/health |
| Organization Management | 8008 | http://localhost:8008/health |
| RAG Service | 8009 | http://localhost:8009/health |
| Demo Service | 8010 | http://localhost:8010/health |
| AI Assistant | 8011 | http://localhost:8011/health |
| Knowledge Graph | 8012 | http://localhost:8012/health |
| NLP Preprocessing | 8013 | https://localhost:8013/health |
| Metadata Service | 8014 | http://localhost:8014/health |
| Local LLM Service | 8015 | http://localhost:8015/health |
| Frontend | 3000 | http://localhost:3000 |
| PostgreSQL | 5432 | N/A |
| Redis | 6379 | N/A |
| Ollama (Host) | 11434 | http://localhost:11434/api/tags |

---

## Installation

### Prerequisites

#### System Requirements

**Minimum**:
- CPU: 4 cores
- RAM: 8 GB
- Disk: 50 GB
- OS: Linux (Ubuntu 20.04+, Debian 11+, CentOS 8+)

**Recommended**:
- CPU: 8 cores
- RAM: 16 GB
- Disk: 100 GB SSD
- OS: Ubuntu 22.04 LTS

#### Required Software

1. **Docker** (20.10+)
2. **Docker Compose** (2.0+)
3. **Git** (2.30+)
4. **Python** (3.10+) - for utilities
5. **PostgreSQL Client** (15+) - for database management

#### Optional Software

- **nginx** - for production reverse proxy
- **certbot** - for SSL/TLS certificates
- **prometheus** - for metrics collection
- **grafana** - for metrics visualization
- **Ollama** - for local LLM inference (required for Local LLM Service)

### Installation Steps

#### 1. Install Dependencies

**Ubuntu/Debian**:
```bash
# Update package index
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install other dependencies
sudo apt install -y git python3-pip postgresql-client redis-tools jq

# Verify installations
docker --version
docker-compose --version
git --version
python3 --version
```

**CentOS/RHEL**:
```bash
# Install Docker
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo yum install -y docker-ce docker-ce-cli containerd.io
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install other dependencies
sudo yum install -y git python3-pip postgresql jq

# Verify installations
docker --version
docker-compose --version
```

#### 2. Clone Repository

```bash
# Clone from GitHub
git clone https://github.com/yourusername/course-creator.git
cd course-creator

# Verify repository structure
ls -la

# Expected output:
# - services/
# - frontend/
# - config/
# - tests/
# - docker-compose.yml
# - app-control.sh
# - etc.
```

#### 3. Install Ollama (Optional - for Local LLM Service)

**For GPU-accelerated local LLM inference**:

```bash
# Install Ollama (Linux)
curl -fsSL https://ollama.com/install.sh | sh

# Verify Ollama installation
ollama --version

# Pull the Llama 3.1 8B model (4.6GB)
ollama pull llama3.1:8b-instruct-q4_K_M

# Verify model is available
ollama list

# Test model inference
ollama run llama3.1:8b-instruct-q4_K_M "What is Python?"

# Start Ollama service (runs on http://localhost:11434)
sudo systemctl start ollama
sudo systemctl enable ollama

# Check Ollama is running
curl http://localhost:11434/api/tags
```

**Requirements for GPU acceleration**:
- NVIDIA GPU (recommended: RTX series or better)
- NVIDIA drivers installed
- CUDA Toolkit installed

**Without GPU**: Ollama will use CPU inference (slower but functional)

#### 4. Configure Environment

```bash
# Create environment file
cp .env.example .env

# Edit environment variables
nano .env
```

**Required `.env` variables**:
```bash
# Database Configuration
DB_HOST=postgres
DB_PORT=5432
DB_NAME=course_creator
DB_USER=course_user
DB_PASSWORD=change_this_strong_password_123

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379

# JWT Configuration
JWT_SECRET_KEY=change_this_to_a_random_secret_key_min_32_chars
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# AI Service Configuration
ANTHROPIC_API_KEY=your_anthropic_api_key_here
OPENAI_API_KEY=your_openai_api_key_optional

# Local LLM Configuration (if using Ollama)
OLLAMA_HOST=http://localhost:11434
LOCAL_LLM_PORT=8015
MODEL_NAME=llama3.1:8b-instruct-q4_K_M
ENABLE_CACHE=true
CACHE_TTL=3600

# Email Configuration (Optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@example.com
SMTP_PASSWORD=your_app_password
SMTP_FROM=noreply@course-creator.com

# Platform Configuration
PLATFORM_URL=http://localhost:3000
ENVIRONMENT=development  # development | staging | production
DEBUG=true

# Security
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
CORS_ALLOW_CREDENTIALS=true

# Lab Container Configuration
LAB_MAX_CONCURRENT=50
LAB_DEFAULT_TIMEOUT_MINUTES=120
LAB_STORAGE_PATH=/tmp/lab-storage
```

#### 4. Initialize Database

```bash
# Option A: Using Docker Compose (Recommended)
docker-compose up -d postgres redis
sleep 10  # Wait for PostgreSQL to be ready

# Run database setup
python setup-database.py

# Option B: Using External PostgreSQL
# Ensure PostgreSQL is running and accessible
psql -h localhost -U course_user -d course_creator -f data/migrations/initial_schema.sql
```

#### 5. Start Services

```bash
# Start all services with Docker Compose
./app-control.sh docker-start

# Wait for services to be healthy (may take 2-3 minutes)
./app-control.sh status

# Check health of all services
for port in 8000 8001 8003 8004 8005 8006 8007 8008 8009 8010 8011 8012 8014 8015; do
  echo "Checking port $port..."
  curl -s http://localhost:$port/health | jq '.status'
done

# Check NLP Preprocessing (HTTPS)
curl -k -s https://localhost:8013/health | jq '.status'

# Check Ollama (if installed)
curl -s http://localhost:11434/api/tags | jq '.models[].name' 2>/dev/null || echo "Ollama not available"
```

#### 6. Create Admin User

```bash
# Interactive admin creation
python create-admin.py

# Expected prompts:
# - Email: admin@yourcompany.com
# - Password: (strong password)
# - Full Name: Admin User
# - Confirm password: (repeat password)

# Verify admin creation
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin@yourcompany.com","password":"your_password"}' | jq
```

#### 7. Verify Installation

```bash
# Run smoke tests
python tests/smoke/test_service_health.py

# Access frontend
curl -I http://localhost:3000

# Check Docker containers
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

---

## Configuration

### Service Configuration

Each service uses Hydra for configuration management.

#### User Management Service

**File**: `services/user-management/conf/config.yaml`

```yaml
service:
  name: user-management
  port: 8000
  host: 0.0.0.0

database:
  host: ${DB_HOST}
  port: ${DB_PORT}
  name: ${DB_NAME}
  user: ${DB_USER}
  password: ${DB_PASSWORD}

jwt:
  secret_key: ${JWT_SECRET_KEY}
  algorithm: ${JWT_ALGORITHM}
  expiration_hours: ${JWT_EXPIRATION_HOURS}

redis:
  host: ${REDIS_HOST}
  port: ${REDIS_PORT}
```

#### Course Generator Service

**File**: `services/course-generator/conf/config.yaml`

```yaml
service:
  name: course-generator
  port: 8001

ai:
  provider: anthropic
  anthropic:
    api_key: ${ANTHROPIC_API_KEY}
    model: claude-3-5-sonnet-20241022
    max_tokens: 4096
  openai:
    api_key: ${OPENAI_API_KEY}
    model: gpt-4-turbo-preview
  cache:
    enabled: true
    ttl_hours: 24
```

#### Lab Manager Service

**File**: `services/lab-manager/conf/config.yaml`

```yaml
service:
  name: lab-manager
  port: 8006

lab:
  max_concurrent: ${LAB_MAX_CONCURRENT:50}
  default_timeout_minutes: ${LAB_DEFAULT_TIMEOUT_MINUTES:120}
  storage_path: ${LAB_STORAGE_PATH:/tmp/lab-storage}
  supported_ides:
    - vscode
    - jupyter
    - intellij
    - terminal
  resource_limits:
    memory: "2g"
    cpu: "1.5"
    disk: "5g"

docker:
  socket: /var/run/docker.sock
  network: course-creator_default
```

### Frontend Configuration

**File**: `frontend/js/config.js`

```javascript
const CONFIG = {
    // API Base URLs
    API_BASE: window.location.origin,

    // Service Endpoints
    SERVICES: {
        USER_MANAGEMENT: 'http://localhost:8000',
        COURSE_GENERATOR: 'http://localhost:8001',
        CONTENT_STORAGE: 'http://localhost:8003',
        COURSE_MANAGEMENT: 'http://localhost:8004',
        CONTENT_MANAGEMENT: 'http://localhost:8005',
        LAB_MANAGER: 'http://localhost:8006',
        ANALYTICS: 'http://localhost:8007',
        ORGANIZATION: 'http://localhost:8008'
    },

    // Authentication
    JWT_STORAGE_KEY: 'course_creator_jwt',
    JWT_REFRESH_INTERVAL: 3600000, // 1 hour

    // Lab Configuration
    LAB_DEFAULT_IDE: 'vscode',
    LAB_HEARTBEAT_INTERVAL: 30000, // 30 seconds

    // Polling Intervals
    STATUS_POLL_INTERVAL: 5000,
    ANALYTICS_REFRESH_INTERVAL: 60000,

    // File Upload
    MAX_FILE_SIZE: 52428800, // 50 MB
    ALLOWED_FILE_TYPES: [
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'application/json'
    ]
};
```

### Database Configuration

#### PostgreSQL Tuning

**File**: `/etc/postgresql/15/main/postgresql.conf`

```ini
# Memory Configuration
shared_buffers = 2GB
effective_cache_size = 6GB
work_mem = 64MB
maintenance_work_mem = 512MB

# Connection Settings
max_connections = 200
superuser_reserved_connections = 3

# Write Ahead Log
wal_buffers = 16MB
checkpoint_completion_target = 0.9
max_wal_size = 2GB
min_wal_size = 1GB

# Query Planning
random_page_cost = 1.1  # For SSD
effective_io_concurrency = 200

# Logging
logging_collector = on
log_directory = 'log'
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
log_min_duration_statement = 1000  # Log queries > 1s
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '
```

---

## Deployment

### Docker Deployment (Recommended)

#### Development Environment

```bash
# Start all services
./app-control.sh docker-start

# View logs
./app-control.sh logs

# Follow specific service logs
docker-compose logs -f user-management

# Rebuild services after code changes
docker-compose up -d --build
```

#### Staging Environment

```bash
# Use staging compose file
docker-compose -f docker-compose.staging.yml up -d

# Apply staging environment variables
export ENVIRONMENT=staging
export DEBUG=false
export PLATFORM_URL=https://staging.course-creator.com

# Start services
./app-control.sh docker-start
```

#### Production Environment

**File**: `docker-compose.prod.yml`

```yaml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - ./frontend:/usr/share/nginx/html:ro
    depends_on:
      - user-management
      - course-generator
    restart: always
    networks:
      - course-creator

  user-management:
    build: ./services/user-management
    environment:
      - ENVIRONMENT=production
      - DEBUG=false
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1'
          memory: 1G
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - course-creator

  # Additional services...

networks:
  course-creator:
    driver: bridge

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
  lab_storage:
    driver: local
```

**Deploy to production**:

```bash
# Pull latest code
git pull origin master

# Build images
docker-compose -f docker-compose.prod.yml build

# Stop old containers
docker-compose -f docker-compose.prod.yml down

# Start new containers
docker-compose -f docker-compose.prod.yml up -d

# Verify deployment
docker-compose -f docker-compose.prod.yml ps
./app-control.sh status
```

### Native Deployment

#### Service Installation

```bash
# Create service user
sudo useradd -r -s /bin/bash course-creator
sudo mkdir -p /opt/course-creator
sudo chown course-creator:course-creator /opt/course-creator

# Clone repository
sudo -u course-creator git clone https://github.com/yourusername/course-creator.git /opt/course-creator
cd /opt/course-creator

# Create virtual environment
sudo -u course-creator python3 -m venv .venv
sudo -u course-creator .venv/bin/pip install -r requirements.txt
```

#### Systemd Service Files

**User Management Service**:

**File**: `/etc/systemd/system/course-creator-user-management.service`

```ini
[Unit]
Description=Course Creator - User Management Service
After=network.target postgresql.service redis.service
Requires=postgresql.service redis.service

[Service]
Type=simple
User=course-creator
Group=course-creator
WorkingDirectory=/opt/course-creator/services/user-management
Environment="PATH=/opt/course-creator/.venv/bin"
EnvironmentFile=/opt/course-creator/.env
ExecStart=/opt/course-creator/.venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Enable and start services**:

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable services
sudo systemctl enable course-creator-user-management
sudo systemctl enable course-creator-course-generator
# ... enable all services

# Start services
sudo systemctl start course-creator-user-management
sudo systemctl start course-creator-course-generator

# Check status
sudo systemctl status course-creator-*
```

---

## Operations

### Daily Operations

#### Service Management

```bash
# Check all services
./app-control.sh status

# Restart a service
./app-control.sh restart user-management

# View recent logs
./app-control.sh logs user-management --tail 100

# Follow logs in real-time
./app-control.sh logs user-management --follow
```

#### Database Operations

```bash
# Connect to database
docker-compose exec postgres psql -U course_user -d course_creator

# Backup database
docker-compose exec -T postgres pg_dump -U course_user course_creator | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz

# Restore database
gunzip < backup.sql.gz | docker-compose exec -T postgres psql -U course_user -d course_creator

# View database size
docker-compose exec postgres psql -U course_user -d course_creator -c "SELECT pg_size_pretty(pg_database_size('course_creator'));"
```

#### Lab Container Management

```bash
# List all active labs
curl -s http://localhost:8006/labs | jq '.labs[] | {lab_id, user_id, status}'

# Stop expired labs
curl -X POST http://localhost:8006/labs/cleanup

# View lab resource usage
docker stats --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" | grep "lab-"
```

### Weekly Operations

#### Performance Monitoring

```bash
# Check service health
for port in 8000 8001 8003 8004 8005 8006 8007 8008 8009 8010 8011 8012 8014 8015; do
  response=$(curl -s http://localhost:$port/health)
  status=$(echo $response | jq -r '.status')
  echo "Port $port: $status"
done

# Database query performance
docker-compose exec postgres psql -U course_user -d course_creator -c "
  SELECT
    query,
    calls,
    total_time,
    mean_time,
    max_time
  FROM pg_stat_statements
  ORDER BY mean_time DESC
  LIMIT 10;
"

# Disk usage
df -h /var/lib/docker
du -sh /opt/course-creator/lab-storage/*
```

#### Log Rotation

```bash
# Rotate logs
./app-control.sh rotate-logs

# Manual log rotation
docker-compose exec user-management sh -c "mv logs/app.log logs/app.log.$(date +%Y%m%d) && touch logs/app.log"

# Clean old logs
find logs/ -name "*.log.*" -mtime +30 -delete
```

### Monthly Operations

#### Database Maintenance

```bash
# Vacuum and analyze
docker-compose exec postgres psql -U course_user -d course_creator -c "VACUUM ANALYZE;"

# Reindex
docker-compose exec postgres psql -U course_user -d course_creator -c "REINDEX DATABASE course_creator;"

# Update statistics
docker-compose exec postgres psql -U course_user -d course_creator -c "ANALYZE;"
```

#### Security Updates

```bash
# Update base Docker images
docker-compose pull

# Rebuild with latest packages
docker-compose up -d --build

# Update Python dependencies
pip-compile requirements.in
pip install -r requirements.txt

# Update npm packages
npm audit fix
```

---

## Monitoring

### Health Checks

#### Automated Health Monitoring

**File**: `scripts/health-check.sh`

```bash
#!/bin/bash

SERVICES=(
    "user-management:8000"
    "course-generator:8001"
    "content-storage:8003"
    "course-management:8004"
    "content-management:8005"
    "lab-manager:8006"
    "analytics:8007"
    "organization-management:8008"
    "rag-service:8009"
    "demo-service:8010"
    "ai-assistant:8011"
    "knowledge-graph:8012"
    "metadata-service:8014"
    "local-llm-service:8015"
)

echo "=== Service Health Check ==="
echo "Timestamp: $(date)"
echo ""

all_healthy=true

for service in "${SERVICES[@]}"; do
    name="${service%:*}"
    port="${service#*:}"

    response=$(curl -s -w "\n%{http_code}" http://localhost:$port/health)
    http_code=$(echo "$response" | tail -n 1)
    body=$(echo "$response" | head -n -1)

    if [ "$http_code" == "200" ]; then
        status=$(echo "$body" | jq -r '.status // "unknown"')
        if [ "$status" == "healthy" ]; then
            echo "✓ $name: HEALTHY"
        else
            echo "✗ $name: UNHEALTHY ($status)"
            all_healthy=false
        fi
    else
        echo "✗ $name: DOWN (HTTP $http_code)"
        all_healthy=false
    fi
done

echo ""
if [ "$all_healthy" == "true" ]; then
    echo "All services healthy ✓"
    exit 0
else
    echo "Some services unhealthy ✗"
    exit 1
fi
```

#### Metrics Collection

**Prometheus Configuration**:

**File**: `config/prometheus.yml`

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'course-creator'
    static_configs:
      - targets:
          - 'user-management:8000'
          - 'course-generator:8001'
          - 'lab-manager:8006'
          - 'analytics:8007'
    metrics_path: '/metrics'

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:9121']

  - job_name: 'docker'
    static_configs:
      - targets: ['docker-exporter:9323']
```

### Logging

#### Centralized Logging

**File**: `config/logging/logging.yaml`

```yaml
version: 1
disable_existing_loggers: False

formatters:
  detailed:
    format: '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
  json:
    class: pythonjsonlogger.jsonlogger.JsonFormatter
    format: '%(asctime)s %(name)s %(levelname)s %(message)s'

handlers:
  console:
    class: logging.StreamHandler
    level: INFO
    formatter: detailed
    stream: ext://sys.stdout

  file:
    class: logging.handlers.RotatingFileHandler
    level: DEBUG
    formatter: json
    filename: logs/app.log
    maxBytes: 104857600  # 100 MB
    backupCount: 10

  error_file:
    class: logging.handlers.RotatingFileHandler
    level: ERROR
    formatter: detailed
    filename: logs/error.log
    maxBytes: 104857600
    backupCount: 10

root:
  level: INFO
  handlers: [console, file, error_file]

loggers:
  uvicorn:
    level: INFO
  fastapi:
    level: INFO
  sqlalchemy:
    level: WARNING
```

---

## Troubleshooting

### Common Issues

#### 1. Services Won't Start

**Symptoms**:
- Docker containers exit immediately
- Health checks fail
- Connection refused errors

**Diagnosis**:
```bash
# Check Docker daemon
sudo systemctl status docker

# Check container logs
docker-compose logs user-management

# Check port conflicts
sudo netstat -tulpn | grep :8000

# Check disk space
df -h

# Check memory
free -h
```

**Solutions**:
```bash
# Restart Docker daemon
sudo systemctl restart docker

# Remove old containers
docker-compose down
docker system prune -a

# Free up ports
sudo kill $(sudo lsof -t -i:8000)

# Free up disk space
docker system prune --volumes

# Restart services
./app-control.sh docker-start
```

#### 2. Database Connection Errors

**Symptoms**:
- "Connection refused" errors
- "Password authentication failed"
- "Database does not exist"

**Diagnosis**:
```bash
# Check PostgreSQL status
docker-compose ps postgres

# Test connection
docker-compose exec postgres psql -U course_user -d course_creator -c "SELECT 1;"

# Check environment variables
docker-compose config | grep DB_

# View PostgreSQL logs
docker-compose logs postgres
```

**Solutions**:
```bash
# Restart PostgreSQL
docker-compose restart postgres

# Reset database
docker-compose down -v
docker-compose up -d postgres
sleep 10
python setup-database.py

# Check credentials
cat .env | grep DB_

# Verify connection string
python -c "import asyncpg; asyncpg.connect('postgresql://course_user:password@localhost:5432/course_creator')"
```

#### 3. Lab Containers Not Starting

**Symptoms**:
- "Cannot connect to Docker daemon"
- Lab creation times out
- Container fails to start

**Diagnosis**:
```bash
# Check Docker socket
ls -la /var/run/docker.sock

# Check lab manager logs
docker-compose logs lab-manager

# List lab containers
docker ps -a | grep "lab-"

# Check Docker network
docker network ls | grep course-creator
```

**Solutions**:
```bash
# Fix Docker socket permissions
sudo chmod 666 /var/run/docker.sock

# Restart lab manager
docker-compose restart lab-manager

# Clean up stuck lab containers
docker ps -a | grep "lab-" | awk '{print $1}' | xargs docker rm -f

# Recreate network
docker network rm course-creator_default
docker-compose up -d
```

#### 4. Frontend Not Loading

**Symptoms**:
- Blank page
- 404 errors
- CORS errors

**Diagnosis**:
```bash
# Check frontend container
docker-compose ps frontend

# Test static files
curl -I http://localhost:3000/index.html

# Check nginx logs
docker-compose logs frontend

# Test API connectivity
curl http://localhost:3000/health
```

**Solutions**:
```bash
# Rebuild frontend
docker-compose up -d --build frontend

# Check CORS configuration
grep ALLOWED_ORIGINS .env

# Clear browser cache
# Ctrl+Shift+R (hard reload)

# Verify frontend files
docker-compose exec frontend ls /usr/share/nginx/html
```

#### 5. AI Service Errors

**Symptoms**:
- "API key invalid"
- Content generation fails
- Timeout errors

**Diagnosis**:
```bash
# Check API key
grep ANTHROPIC_API_KEY .env

# Test AI service
curl -X POST http://localhost:8001/test-ai \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Test"}'

# Check course generator logs
docker-compose logs course-generator
```

**Solutions**:
```bash
# Verify API key
# Go to https://console.anthropic.com/

# Update environment
nano .env  # Add/update ANTHROPIC_API_KEY
docker-compose restart course-generator

# Increase timeout
# Edit services/course-generator/conf/config.yaml
# ai.timeout: 120  # seconds

# Check network connectivity
docker-compose exec course-generator ping -c 4 api.anthropic.com
```

#### 6. Local LLM Service Issues

**Symptoms**:
- "Ollama service not available"
- Local LLM health check fails
- Slow inference (>10s)
- Model not found errors

**Diagnosis**:
```bash
# Check Ollama service status
curl http://localhost:11434/api/tags

# Check Local LLM service
curl http://localhost:8015/health

# List available models
ollama list

# Check Local LLM container logs
docker logs course-creator-local-llm-service-1

# Check GPU availability (if using GPU)
nvidia-smi

# Test model inference directly
ollama run llama3.1:8b-instruct-q4_K_M "Test"
```

**Solutions**:
```bash
# Start Ollama service
sudo systemctl start ollama
sudo systemctl enable ollama

# Pull missing model
ollama pull llama3.1:8b-instruct-q4_K_M

# Restart Local LLM service
docker restart course-creator-local-llm-service-1

# Check Docker host network access
docker run --rm --network host curlimages/curl:latest curl http://localhost:11434/api/tags

# Verify environment variables
docker inspect course-creator-local-llm-service-1 | grep -A 5 Env

# Check cache stats
curl http://localhost:8015/metrics

# Clear cache and restart
docker restart course-creator-local-llm-service-1
```

**Performance Optimization**:
```bash
# Check GPU usage during inference
watch -n 0.5 nvidia-smi

# Test inference latency
time curl -X POST http://localhost:8015/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"What is Python?","max_tokens":50}'

# Check cache effectiveness
curl http://localhost:8015/metrics | jq '.cache'

# Warm up model (first query is slow)
curl -X POST http://localhost:8015/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Hi","max_tokens":10}'
```

### Performance Issues

#### Slow Response Times

**Diagnosis**:
```bash
# Check resource usage
docker stats

# Database query performance
docker-compose exec postgres psql -U course_user -d course_creator -c "
  SELECT query, calls, total_time, mean_time
  FROM pg_stat_statements
  ORDER BY mean_time DESC
  LIMIT 10;
"

# Network latency
docker-compose exec user-management ping -c 10 postgres
```

**Solutions**:
```bash
# Scale services
docker-compose up -d --scale user-management=3

# Optimize database
docker-compose exec postgres psql -U course_user -d course_creator -c "VACUUM ANALYZE;"

# Add indexes
# See data/migrations/performance_indexes.sql

# Enable caching
# Update services/*/conf/config.yaml
# cache.enabled: true
```

#### High Memory Usage

**Diagnosis**:
```bash
# Check container memory
docker stats --no-stream

# Check system memory
free -h

# Identify memory leaks
docker-compose exec user-management python -c "
import psutil
print(f'Memory: {psutil.virtual_memory().percent}%')
"
```

**Solutions**:
```bash
# Set memory limits
# Edit docker-compose.yml
# deploy:
#   resources:
#     limits:
#       memory: 1G

# Restart services
docker-compose restart

# Clear caches
docker-compose exec redis redis-cli FLUSHALL
```

---

## Maintenance

### Backup Procedures

#### Database Backup

**Daily automated backup**:

**File**: `scripts/backup-db.sh`

```bash
#!/bin/bash

BACKUP_DIR="/opt/course-creator/backups/database"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$TIMESTAMP.sql.gz"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
docker-compose exec -T postgres pg_dump -U course_user course_creator | gzip > $BACKUP_FILE

# Keep last 30 days
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_FILE"
```

**Setup cron job**:
```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * /opt/course-creator/scripts/backup-db.sh >> /var/log/course-creator-backup.log 2>&1
```

#### Application Backup

```bash
#!/bin/bash

BACKUP_DIR="/opt/course-creator/backups/application"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$TIMESTAMP.tar.gz"

# Backup configuration and data
tar -czf $BACKUP_FILE \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    --exclude='.venv' \
    --exclude='node_modules' \
    --exclude='logs/*.log' \
    /opt/course-creator

echo "Application backup completed: $BACKUP_FILE"
```

### Update Procedures

#### Application Updates

```bash
# 1. Backup current state
./scripts/backup-db.sh
./scripts/backup-application.sh

# 2. Pull latest code
git fetch origin
git checkout master
git pull origin master

# 3. Review changes
git log --oneline -10
git diff HEAD~1

# 4. Update dependencies
pip install -r requirements.txt --upgrade
npm install

# 5. Run database migrations
python data/migrations/run_migrations.py

# 6. Rebuild services
docker-compose up -d --build

# 7. Verify deployment
./scripts/health-check.sh
./app-control.sh status

# 8. Run smoke tests
pytest tests/smoke/
```

#### Rolling Updates (Zero Downtime)

```bash
# Update one service at a time
for service in user-management course-generator course-management; do
    echo "Updating $service..."
    docker-compose up -d --build --no-deps $service
    sleep 30  # Wait for health check

    # Verify health
    health=$(curl -s http://localhost:800X/health | jq -r '.status')
    if [ "$health" != "healthy" ]; then
        echo "Update failed for $service"
        exit 1
    fi
done
```

---

## Security

### Security Best Practices

1. **Change Default Credentials**
   - Update `.env` with strong passwords
   - Rotate JWT secret keys regularly

2. **Enable HTTPS**
   - Use Let's Encrypt for SSL certificates
   - Configure nginx with SSL/TLS

3. **Firewall Configuration**
   ```bash
   # Allow only necessary ports
   sudo ufw allow 22/tcp   # SSH
   sudo ufw allow 80/tcp   # HTTP
   sudo ufw allow 443/tcp  # HTTPS
   sudo ufw enable
   ```

4. **Regular Security Updates**
   ```bash
   # Update system packages
   sudo apt update && sudo apt upgrade -y

   # Update Docker images
   docker-compose pull
   docker-compose up -d
   ```

5. **Audit Logging**
   - Enable audit logs in Organization Management Service
   - Review logs regularly for suspicious activity

### Disaster Recovery

#### Recovery Procedures

1. **Database Restoration**
   ```bash
   # Stop services
   docker-compose down

   # Restore database
   gunzip < backup.sql.gz | docker-compose exec -T postgres psql -U course_user -d course_creator

   # Restart services
   docker-compose up -d
   ```

2. **Full System Recovery**
   ```bash
   # Clone repository
   git clone https://github.com/yourusername/course-creator.git
   cd course-creator

   # Restore configuration
   cp /backup/.env .env

   # Restore database
   docker-compose up -d postgres
   ./scripts/restore-db.sh /backup/database/backup_latest.sql.gz

   # Start all services
   docker-compose up -d
   ```

---

## Appendix

### Useful Commands

```bash
# Docker
docker-compose ps                    # List containers
docker-compose logs -f <service>    # Follow logs
docker-compose exec <service> bash  # Shell into container
docker system df                     # Disk usage
docker system prune                  # Clean up unused resources

# Database
docker-compose exec postgres psql -U course_user -d course_creator
\dt                                  # List tables
\d+ <table>                         # Describe table
\q                                   # Quit

# Redis
docker-compose exec redis redis-cli
INFO                                 # Server info
KEYS *                              # List all keys
FLUSHALL                            # Clear all data

# System
htop                                 # Process monitor
df -h                               # Disk usage
free -h                             # Memory usage
journalctl -u docker                # Docker logs
```

### Support Contacts

- **GitHub Issues**: https://github.com/yourusername/course-creator/issues
- **Email**: support@course-creator.com
- **Documentation**: https://docs.course-creator.com

---

**Document Version**: 3.1.0
**Last Updated**: 2025-10-04
**Next Review**: 2025-11-04
