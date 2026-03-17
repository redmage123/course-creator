# Course Creator Platform - Complete Runbook

## 📋 Overview

This runbook provides step-by-step instructions for installing, deploying, and using the Course Creator Platform. Follow these instructions in order for a successful setup.

## 🎯 What You'll Get

After following this runbook, you'll have:
- ✅ A fully functional Course Creator Platform
- ✅ Multi-IDE lab environments for coding exercises
- ✅ AI-powered course content generation
- ✅ Student and instructor dashboards
- ✅ Automated CI/CD pipeline with Jenkins and SonarQube
- ✅ Production-ready deployment with monitoring

## 📋 Prerequisites

### System Requirements

**Minimum Hardware:**
- **CPU**: 4 cores
- **RAM**: 8GB
- **Storage**: 50GB free space
- **Network**: Internet connection for downloads

**Recommended Hardware:**
- **CPU**: 8 cores
- **RAM**: 16GB
- **Storage**: 100GB SSD
- **Network**: High-speed internet

**Operating System:**
- Linux (Ubuntu 20.04+ recommended)
- macOS 10.15+
- Windows 10/11 with WSL2

### Required Software

Before starting, install these prerequisites:

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y git curl wget unzip python3 python3-pip nodejs npm docker.io docker-compose postgresql-client

# macOS (with Homebrew)
brew install git curl wget unzip python3 node npm docker docker-compose postgresql

# Enable Docker service (Linux)
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker $USER
```

**Log out and back in after adding yourself to the docker group.**

### API Keys (Required)

You'll need API keys from:
1. **Anthropic Claude API** - [Get key here](https://console.anthropic.com/)
2. **OpenAI API** (optional) - [Get key here](https://platform.openai.com/)

## 🚀 Quick Start (Recommended)

### Step 1: Clone the Repository

```bash
# Clone the repository
git clone https://github.com/your-org/course-creator.git
cd course-creator

# Verify you're in the right directory
ls -la
# You should see: services/, frontend/, lab-containers/, docker-compose.yml, etc.
```

### Step 2: Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit the environment file with your API keys
nano .env  # or use your preferred editor
```

**Required Environment Variables:**
```bash
# AI Service Configuration
ANTHROPIC_API_KEY=your_anthropic_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Database Configuration (will be auto-configured)
DATABASE_URL=postgresql://course_creator:secure_password@postgres:5432/course_creator
REDIS_URL=redis://redis:6379/0

# Security (change these!)
JWT_SECRET_KEY=your_super_secret_jwt_key_change_this
SECRET_KEY=your_app_secret_key_change_this

# Application Settings
DEBUG=false
ENVIRONMENT=production
```

### Step 3: Deploy with Docker (Recommended)

```bash
# Start the entire platform
./app-control.sh docker-start

# Check status (all services should show as healthy)
./app-control.sh docker-status

# View logs if needed
./app-control.sh docker-logs
```

**Wait 2-3 minutes for all services to start completely.**

### Step 4: Verify Installation

```bash
# Check all services are running
curl http://localhost:8000/health  # User Management
curl http://localhost:8001/health  # Course Generator  
curl http://localhost:8004/health  # Course Management
curl http://localhost:8003/health  # Content Storage
curl http://localhost:8005/health  # Content Management
curl http://localhost:8006/health  # Lab Containers
curl http://localhost:8007/health  # Analytics

# Check frontend
curl http://localhost:3000
```

### Step 5: Create Admin User

```bash
# Create the first admin user
python create-admin.py

# Follow the prompts to create your admin account
```

### Step 6: Access the Platform

Open your web browser and visit:
- **Platform Home**: http://localhost:3000
- **Admin Dashboard**: http://localhost:3000/admin.html
- **Instructor Dashboard**: http://localhost:3000/instructor-dashboard.html
- **Student Dashboard**: http://localhost:3000/student-dashboard.html
- **Interactive Lab**: http://localhost:3000/lab.html

## 🏗️ Advanced Installation Options

### Option A: Development Setup (Native Python)

For development work, you can run services natively:

```bash
# Install Python dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Install frontend dependencies
cd frontend && npm install && cd ..

# Setup database
python setup-database.py

# Start services individually
./app-control.sh start
```

### Option B: Kubernetes Deployment (Production)

For production deployment:

```bash
# Prerequisites: Kubernetes cluster with kubectl configured

# Apply base configuration
kubectl apply -k deploy/k8s/base/

# Apply production overlay
kubectl apply -k deploy/k8s/overlays/prod/

# Check deployment status
kubectl get pods -n course-creator-prod
```

## 🔧 CI/CD Pipeline Setup (Optional)

### Install Jenkins

```bash
# Run Jenkins setup
./jenkins/jenkins-setup.sh

# Access Jenkins at http://localhost:8080
# Default credentials: admin/admin
```

### Install SonarQube

```bash
# Run SonarQube setup
./sonarqube/setup-sonarqube.sh

# Access SonarQube at http://localhost:9000
# Default credentials: admin/admin
```

## 📚 Using the Platform

### For Administrators

1. **Access Admin Dashboard**: http://localhost:3000/admin.html
2. **Create Users**: Add instructors and students
3. **Manage Platform Settings**: Configure AI services, lab environments
4. **Monitor Usage**: View analytics and system health

### For Instructors

1. **Access Instructor Dashboard**: http://localhost:3000/instructor-dashboard.html
2. **Create Courses**: Use AI-powered course generation
3. **Upload Content**: Drag-and-drop PDFs, PowerPoints, documents
4. **Design Labs**: Create interactive coding environments
5. **Manage Students**: Enroll students and track progress

**Course Creation Workflow:**
```
1. Click "Create New Course"
2. Upload course materials (PDF, DOCX, PPTX)
3. AI generates course outline and content
4. Review and customize generated content
5. Add interactive labs and exercises
6. Publish course for students
```

### For Students

1. **Access Student Dashboard**: http://localhost:3000/student-dashboard.html
2. **Browse Courses**: View available courses
3. **Enroll in Courses**: Join courses assigned by instructors
4. **Complete Labs**: Use interactive coding environments
5. **Track Progress**: View completion status and grades

**Lab Environment Features:**
- Multiple IDE options (VS Code, Vim, Nano)
- Real-time code execution
- File upload/download
- Terminal access
- Language support (Python, JavaScript, Java, C++, etc.)

## 🔍 Monitoring and Maintenance

### Health Checks

```bash
# Check all services
./app-control.sh status

# Check individual service logs
./app-control.sh logs user-management
./app-control.sh logs course-generator
```

### Database Management

```bash
# Backup database
docker exec course-creator-postgres pg_dump -U course_creator course_creator > backup.sql

# Restore database
docker exec -i course-creator-postgres psql -U course_creator course_creator < backup.sql

# Reset database (WARNING: destroys all data)
python setup-database.py --reset
```

### Performance Monitoring

Visit these URLs to monitor performance:
- **Application Metrics**: http://localhost:8007/metrics
- **Database Metrics**: Check PostgreSQL logs
- **Container Metrics**: `docker stats`

## 🚨 Troubleshooting

### Common Issues

#### 1. Services Won't Start

**Problem**: Services fail to start or show unhealthy status

**Solutions:**
```bash
# Check Docker daemon
sudo systemctl status docker

# Check logs for specific service
./app-control.sh docker-logs user-management

# Restart specific service
docker-compose restart user-management

# Full restart
./app-control.sh docker-restart
```

#### 2. Database Connection Errors

**Problem**: Services can't connect to database

**Solutions:**
```bash
# Check database container
docker-compose ps postgres

# Check database logs
docker-compose logs postgres

# Reset database
docker-compose down
docker volume rm course-creator_postgres_data
./app-control.sh docker-start
```

#### 3. Lab Containers Won't Start

**Problem**: Interactive labs fail to launch

**Solutions:**
```bash
# Check Docker socket permissions
sudo chmod 666 /var/run/docker.sock

# Check lab container logs
./app-control.sh docker-logs lab-containers

# Restart lab service
docker-compose restart lab-containers
```

#### 4. Frontend Not Loading

**Problem**: Web interface doesn't load or shows errors

**Solutions:**
```bash
# Check frontend service
./app-control.sh docker-logs frontend

# Clear browser cache
# Try incognito/private browsing mode

# Check if backend APIs are responding
curl http://localhost:8000/health
```

#### 5. AI Services Not Working

**Problem**: Course generation fails or AI features don't work

**Solutions:**
```bash
# Verify API keys in .env file
grep ANTHROPIC_API_KEY .env
grep OPENAI_API_KEY .env

# Test API connectivity
curl -H "Authorization: Bearer $ANTHROPIC_API_KEY" https://api.anthropic.com/v1/models

# Check course generator logs
./app-control.sh docker-logs course-generator
```

### Getting Help

1. **Check Logs**: Always start by checking service logs
2. **Review Documentation**: Check `docs/` directory for detailed info
3. **Health Endpoints**: Use `/health` endpoints to diagnose issues
4. **Community**: Create issues in the project repository

### Diagnostic Commands

```bash
# System information
docker --version
docker-compose --version
python3 --version
node --version

# Service status
./app-control.sh docker-status
docker-compose ps

# Resource usage
docker stats
df -h  # Disk space
free -h  # Memory usage

# Network connectivity
curl -I http://localhost:3000
curl -I http://localhost:8000
```

## 🔄 Updates and Upgrades

### Updating the Platform

```bash
# Pull latest code
git pull origin main

# Rebuild images
./app-control.sh docker-build

# Restart with new images
./app-control.sh docker-restart

# Run database migrations if needed
python setup-database.py --migrate
```

### Backup Before Updates

```bash
# Create full backup
mkdir backup-$(date +%Y%m%d)
./scripts/backup.sh backup-$(date +%Y%m%d)/
```

## 📊 Performance Optimization

### For Better Performance

1. **Increase Docker Resources**:
   - Docker Desktop: Settings → Resources → Advanced
   - Increase CPU cores and memory allocation

2. **SSD Storage**: Use SSD for Docker volumes and database

3. **Resource Limits**: Adjust Docker resource limits in `docker-compose.yml`

4. **Database Tuning**: Configure PostgreSQL for your workload

### Scaling for Production

```bash
# Scale specific services
docker-compose up -d --scale user-management=3
docker-compose up -d --scale course-generator=2

# Use Kubernetes for auto-scaling
kubectl apply -k deploy/k8s/overlays/prod/
```

## 📝 Configuration Reference

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `ANTHROPIC_API_KEY` | Anthropic Claude API key | - | Yes |
| `OPENAI_API_KEY` | OpenAI API key | - | No |
| `DATABASE_URL` | PostgreSQL connection string | Auto-configured | No |
| `REDIS_URL` | Redis connection string | Auto-configured | No |
| `JWT_SECRET_KEY` | JWT token signing key | - | Yes |
| `DEBUG` | Enable debug mode | false | No |
| `LOG_LEVEL` | Logging level | INFO | No |
| `MAX_CONCURRENT_LABS` | Max simultaneous labs | 10 | No |

### Port Reference

| Service | Port | Description |
|---------|------|-------------|
| Frontend | 3000 | Web interface |
| User Management | 8000 | Authentication & users |
| Course Generator | 8001 | AI content generation |
| Content Storage | 8003 | File storage |
| Course Management | 8004 | Course CRUD operations |
| Content Management | 8005 | Content upload/export |
| Lab Containers | 8006 | Interactive lab environment |
| Analytics | 8007 | Usage analytics |
| PostgreSQL | 5432 | Database |
| Redis | 6379 | Cache & sessions |

## 🎓 Next Steps

Once your platform is running:

1. **Create Your First Course**: Upload a PDF and let AI generate course content
2. **Set Up Lab Environment**: Create interactive coding exercises
3. **Invite Users**: Add instructors and students to your platform
4. **Explore Features**: Try content export, analytics, and multi-IDE labs
5. **Customize**: Modify templates and branding in `frontend/` directory

## 📞 Support

For additional help:
- **Documentation**: Check `docs/` directory
- **Issues**: Create issues in the project repository
- **Logs**: Always include relevant logs when reporting problems
- **Community**: Join discussions in project repository

---

**🎉 Congratulations!** You now have a fully functional Course Creator Platform with AI-powered content generation and interactive lab environments.

**Happy Teaching and Learning! 🚀**