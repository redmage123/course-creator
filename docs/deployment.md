# Deployment Guide - Course Creator Platform

## Overview

This guide covers deployment strategies for the Course Creator Platform, from local development to production environments.

## Table of Contents

1. [Deployment Architecture](#deployment-architecture)
2. [Local Development Setup](#local-development-setup)
3. [Docker Deployment](#docker-deployment)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [Production Deployment](#production-deployment)
6. [Environment Configuration](#environment-configuration)
7. [Monitoring and Logging](#monitoring-and-logging)
8. [Security Considerations](#security-considerations)
9. [Scaling Strategies](#scaling-strategies)
10. [Troubleshooting](#troubleshooting)

## Deployment Architecture

### Environment Tiers

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Development   │    │     Staging     │    │   Production    │
│                 │    │                 │    │                 │
│ • Local setup   │    │ • Pre-prod test │    │ • Live system   │
│ • Hot reloading │    │ • Full features │    │ • High availability│
│ • Debug mode    │    │ • Performance   │    │ • Monitoring    │
│ • Test data     │    │ • Integration   │    │ • Backup/DR     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Service Dependencies

```
Frontend (Port 8080)
    ↓
Load Balancer / API Gateway
    ↓
┌─────────────────────────────────────────────────────────────┐
│                     Backend Services                        │
├─────────────┬─────────────┬─────────────┬─────────────────┤
│ User Mgmt   │ Course Mgmt │ Course Gen  │ Content Storage │
│ (Port 8001) │ (Port 8002) │ (Port 8003) │ (Port 8004)     │
└─────────────┴─────────────┴─────────────┴─────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│                      Data Layer                             │
├─────────────┬─────────────┬─────────────┬─────────────────┤
│ PostgreSQL  │   Redis     │ File Storage│   Monitoring    │
│ (Port 5432) │ (Port 6379) │    (S3)     │    Stack        │
└─────────────┴─────────────┴─────────────┴─────────────────┘
```

## Local Development Setup

### Prerequisites

```bash
# Required software
- Python 3.8+
- Node.js 16+
- PostgreSQL 12+
- Redis 6+
- Git

# Optional
- Docker & Docker Compose
- kubectl (for Kubernetes testing)
```

### Quick Start

1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd course-creator
   ```

2. **Environment Setup**
   ```bash
   # Create environment files
   cp .env.example .env
   
   # Configure database
   sudo -u postgres createdb course_creator
   ```

3. **Install Dependencies**
   ```bash
   # Backend dependencies
   pip install -r requirements.txt
   
   # Frontend dependencies (if using Node.js tools)
   npm install
   ```

4. **Database Setup**
   ```bash
   # Run migrations
   python setup-database.py
   
   # Seed with test data (optional)
   python create-admin.py
   ```

5. **Start Services**
   ```bash
   # Option 1: Use the platform startup script
   python start-platform.py
   
   # Option 2: Start services individually
   cd services/user-management && python run.py &
   cd services/course-management && python run.py &
   cd services/course-generator && python run.py &
   cd services/content-storage && python run.py &
   
   # Start frontend server
   cd frontend && python -m http.server 8080
   ```

6. **Verify Installation**
   ```bash
   # Check health endpoints
   curl http://localhost:8001/health
   curl http://localhost:8002/health
   curl http://localhost:8003/health
   curl http://localhost:8004/health
   
   # Access frontend
   open http://localhost:8080
   ```

### Development Tools

1. **Database Management**
   ```bash
   # PostgreSQL commands
   psql -U postgres -d course_creator
   
   # View tables
   \dt
   
   # Reset database
   python setup-database.py --reset
   ```

2. **Log Monitoring**
   ```bash
   # View service logs
   tail -f logs/user-management.log
   tail -f logs/course-management.log
   tail -f logs/course-generator.log
   tail -f logs/content-storage.log
   ```

3. **Hot Reloading**
   ```bash
   # Start services with auto-reload
   cd services/user-management
   uvicorn main:app --reload --port 8001
   ```

## Docker Deployment

### Docker Compose Setup

1. **Create docker-compose.yml**
   ```yaml
   version: '3.8'
   
   services:
     # Database
     postgres:
       image: postgres:13
       environment:
         POSTGRES_DB: course_creator
         POSTGRES_USER: postgres
         POSTGRES_PASSWORD: postgres
       volumes:
         - postgres_data:/var/lib/postgresql/data
       ports:
         - "5432:5432"
   
     # Redis Cache
     redis:
       image: redis:6-alpine
       ports:
         - "6379:6379"
   
     # User Management Service
     user-service:
       build: ./services/user-management
       environment:
         DATABASE_URL: postgresql://postgres:postgres@postgres:5432/course_creator
         REDIS_URL: redis://redis:6379
       depends_on:
         - postgres
         - redis
       ports:
         - "8001:8001"
   
     # Course Management Service
     course-service:
       build: ./services/course-management
       environment:
         DATABASE_URL: postgresql://postgres:postgres@postgres:5432/course_creator
         USER_SERVICE_URL: http://user-service:8001
       depends_on:
         - postgres
         - user-service
       ports:
         - "8002:8002"
   
     # Course Generator Service
     course-generator:
       build: ./services/course-generator
       environment:
         DATABASE_URL: postgresql://postgres:postgres@postgres:5432/course_creator
         ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
       depends_on:
         - postgres
       ports:
         - "8003:8003"
   
     # Content Storage Service
     content-storage:
       build: ./services/content-storage
       environment:
         DATABASE_URL: postgresql://postgres:postgres@postgres:5432/course_creator
         AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID}
         AWS_SECRET_ACCESS_KEY: ${AWS_SECRET_ACCESS_KEY}
       depends_on:
         - postgres
       ports:
         - "8004:8004"
   
     # Frontend
     frontend:
       image: nginx:alpine
       volumes:
         - ./frontend:/usr/share/nginx/html
         - ./nginx.conf:/etc/nginx/nginx.conf
       ports:
         - "8080:80"
       depends_on:
         - user-service
         - course-service
   
   volumes:
     postgres_data:
   ```

2. **Service Dockerfiles**

   **User Management Service Dockerfile:**
   ```dockerfile
   FROM python:3.9-slim
   
   WORKDIR /app
   
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   
   COPY . .
   
   EXPOSE 8001
   
   CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
   ```

3. **Deployment Commands**
   ```bash
   # Build and start all services
   docker-compose up -d
   
   # View logs
   docker-compose logs -f
   
   # Scale services
   docker-compose up -d --scale course-service=3
   
   # Stop services
   docker-compose down
   
   # Rebuild after changes
   docker-compose build && docker-compose up -d
   ```

### Multi-Stage Production Dockerfile

```dockerfile
# Build stage
FROM python:3.9-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.9-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
USER app

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8001/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
```

## Kubernetes Deployment

### Cluster Setup

1. **Prerequisites**
   ```bash
   # Install kubectl
   curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
   sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
   
   # Install Helm
   curl https://get.helm.sh/helm-v3.9.0-linux-amd64.tar.gz | tar xz
   sudo mv linux-amd64/helm /usr/local/bin/
   ```

2. **Namespace Creation**
   ```yaml
   # namespace.yaml
   apiVersion: v1
   kind: Namespace
   metadata:
     name: course-creator
     labels:
       name: course-creator
   ```

### ConfigMaps and Secrets

1. **Configuration Management**
   ```yaml
   # configmap.yaml
   apiVersion: v1
   kind: ConfigMap
   metadata:
     name: app-config
     namespace: course-creator
   data:
     DATABASE_HOST: "postgres-service"
     DATABASE_PORT: "5432"
     DATABASE_NAME: "course_creator"
     REDIS_HOST: "redis-service"
     REDIS_PORT: "6379"
     ENVIRONMENT: "production"
   ```

2. **Secret Management**
   ```yaml
   # secrets.yaml
   apiVersion: v1
   kind: Secret
   metadata:
     name: app-secrets
     namespace: course-creator
   type: Opaque
   data:
     DATABASE_PASSWORD: <base64-encoded-password>
     JWT_SECRET_KEY: <base64-encoded-secret>
     ANTHROPIC_API_KEY: <base64-encoded-key>
   ```

### Database Deployment

```yaml
# postgres-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
  namespace: course-creator
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:13
        env:
        - name: POSTGRES_DB
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: DATABASE_NAME
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: DATABASE_PASSWORD
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
      volumes:
      - name: postgres-storage
        persistentVolumeClaim:
          claimName: postgres-pvc

---
apiVersion: v1
kind: Service
metadata:
  name: postgres-service
  namespace: course-creator
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
```

### Application Deployments

1. **User Management Service**
   ```yaml
   # user-service-deployment.yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: user-service
     namespace: course-creator
   spec:
     replicas: 3
     selector:
       matchLabels:
         app: user-service
     template:
       metadata:
         labels:
           app: user-service
       spec:
         containers:
         - name: user-service
           image: course-creator/user-service:latest
           ports:
           - containerPort: 8001
           env:
           - name: DATABASE_URL
             value: "postgresql://postgres:$(DATABASE_PASSWORD)@postgres-service:5432/course_creator"
           - name: DATABASE_PASSWORD
             valueFrom:
               secretKeyRef:
                 name: app-secrets
                 key: DATABASE_PASSWORD
           envFrom:
           - configMapRef:
               name: app-config
           livenessProbe:
             httpGet:
               path: /health
               port: 8001
             initialDelaySeconds: 30
             periodSeconds: 10
           readinessProbe:
             httpGet:
               path: /health
               port: 8001
             initialDelaySeconds: 5
             periodSeconds: 5
   
   ---
   apiVersion: v1
   kind: Service
   metadata:
     name: user-service
     namespace: course-creator
   spec:
     selector:
       app: user-service
     ports:
     - port: 8001
       targetPort: 8001
   ```

### Ingress Configuration

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: course-creator-ingress
  namespace: course-creator
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - api.courseplatform.com
    - app.courseplatform.com
    secretName: course-creator-tls
  rules:
  - host: api.courseplatform.com
    http:
      paths:
      - path: /api/auth
        pathType: Prefix
        backend:
          service:
            name: user-service
            port:
              number: 8001
      - path: /api/courses
        pathType: Prefix
        backend:
          service:
            name: course-service
            port:
              number: 8002
  - host: app.courseplatform.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend-service
            port:
              number: 80
```

### Deployment Commands

```bash
# Apply configurations
kubectl apply -f infrastructure/kubernetes/

# Check deployment status
kubectl get pods -n course-creator
kubectl get services -n course-creator
kubectl get ingress -n course-creator

# View logs
kubectl logs -f deployment/user-service -n course-creator

# Scale services
kubectl scale deployment user-service --replicas=5 -n course-creator

# Rolling update
kubectl set image deployment/user-service user-service=course-creator/user-service:v2 -n course-creator
```

## Production Deployment

### Cloud Provider Setup

#### AWS Deployment

1. **EKS Cluster Setup**
   ```bash
   # Install eksctl
   curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
   sudo mv /tmp/eksctl /usr/local/bin
   
   # Create cluster
   eksctl create cluster --name course-creator --region us-west-2 --nodegroup-name workers --node-type m5.large --nodes 3
   ```

2. **RDS Database**
   ```bash
   # Create RDS instance
   aws rds create-db-instance \
     --db-instance-identifier course-creator-db \
     --db-instance-class db.t3.micro \
     --engine postgres \
     --master-username postgres \
     --master-user-password <secure-password> \
     --allocated-storage 20
   ```

3. **ElastiCache for Redis**
   ```bash
   # Create Redis cluster
   aws elasticache create-cache-cluster \
     --cache-cluster-id course-creator-redis \
     --cache-node-type cache.t3.micro \
     --engine redis \
     --num-cache-nodes 1
   ```

#### Google Cloud Deployment

1. **GKE Cluster**
   ```bash
   # Create cluster
   gcloud container clusters create course-creator \
     --zone us-central1-a \
     --num-nodes 3 \
     --machine-type n1-standard-2
   
   # Get credentials
   gcloud container clusters get-credentials course-creator --zone us-central1-a
   ```

2. **Cloud SQL**
   ```bash
   # Create PostgreSQL instance
   gcloud sql instances create course-creator-db \
     --database-version POSTGRES_13 \
     --tier db-n1-standard-1 \
     --region us-central1
   ```

### CI/CD Pipeline

#### GitHub Actions Workflow

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r test_requirements.txt
    
    - name: Run tests
      run: |
        python -m pytest tests/
    
    - name: Run security scan
      run: |
        bandit -r services/

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v1
    
    - name: Login to Registry
      uses: docker/login-action@v1
      with:
        registry: ${{ secrets.DOCKER_REGISTRY }}
        username: ${{ secrets.DOCKER_USERNAME }}
        password: ${{ secrets.DOCKER_PASSWORD }}
    
    - name: Build and push images
      run: |
        docker build -t ${{ secrets.DOCKER_REGISTRY }}/user-service:${{ github.sha }} services/user-management/
        docker push ${{ secrets.DOCKER_REGISTRY }}/user-service:${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Configure kubectl
      run: |
        echo "${{ secrets.KUBE_CONFIG }}" | base64 -d > kubeconfig
        export KUBECONFIG=kubeconfig
    
    - name: Deploy to Kubernetes
      run: |
        sed -i 's|IMAGE_TAG|${{ github.sha }}|g' infrastructure/kubernetes/deployments/*.yaml
        kubectl apply -f infrastructure/kubernetes/
        kubectl rollout status deployment/user-service -n course-creator
```

### Health Checks and Monitoring

1. **Application Health Checks**
   ```python
   # Health check endpoint
   @app.get("/health")
   async def health_check():
       try:
           # Check database connection
           db_status = await check_database()
           
           # Check external dependencies
           redis_status = await check_redis()
           
           return {
               "status": "healthy",
               "timestamp": datetime.utcnow(),
               "checks": {
                   "database": db_status,
                   "redis": redis_status
               }
           }
       except Exception as e:
           raise HTTPException(status_code=503, detail="Service unhealthy")
   ```

2. **Kubernetes Probes**
   ```yaml
   livenessProbe:
     httpGet:
       path: /health
       port: 8001
     initialDelaySeconds: 30
     periodSeconds: 10
     timeoutSeconds: 5
     failureThreshold: 3

   readinessProbe:
     httpGet:
       path: /ready
       port: 8001
     initialDelaySeconds: 5
     periodSeconds: 5
     timeoutSeconds: 3
     failureThreshold: 2
   ```

## Environment Configuration

### Environment Variables

```bash
# Production Environment Variables
export ENVIRONMENT=production
export DEBUG=false

# Database Configuration
export DATABASE_URL=postgresql://user:pass@host:5432/dbname
export DATABASE_POOL_SIZE=20
export DATABASE_MAX_OVERFLOW=30

# Redis Configuration
export REDIS_URL=redis://host:6379
export REDIS_MAX_CONNECTIONS=50

# Security
export JWT_SECRET_KEY=your-super-secure-secret-key
export ENCRYPTION_KEY=your-encryption-key

# External APIs
export ANTHROPIC_API_KEY=your-anthropic-key
export OPENAI_API_KEY=your-openai-key

# File Storage
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key
export AWS_BUCKET_NAME=course-creator-files

# Monitoring
export PROMETHEUS_ENABLED=true
export JAEGER_ENDPOINT=http://jaeger:14268
```

This deployment guide provides comprehensive coverage of deploying the Course Creator Platform across different environments and scales. Choose the appropriate deployment strategy based on your requirements and infrastructure preferences.