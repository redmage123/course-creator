# Course Creator Platform - Simple Deployment Guide

## 🚀 **The Platform Is Already Built and Ready!**

Your Course Creator Platform is a complete educational technology system with:
- **8 Microservices** (user-management, course-generator, content-management, analytics, etc.)
- **Docker setup** with health checks and service dependencies  
- **Frontend** with multiple dashboards (student, instructor, admin)
- **Database** setup with PostgreSQL and Redis
- **Lab containers** for student coding environments
- **RAG-enhanced AI** for content generation

## ✅ **Quick Start (Recommended)**

### 1. Create Environment Configuration
```bash
# Copy the example environment file
cp .env.example .cc_env

# Edit .cc_env with your settings (optional - has good defaults)
nano .cc_env
```

### 2. Start the Platform
```bash
# Make the control script executable
chmod +x app-control.sh

# Start all services (this builds and starts everything)
./app-control.sh start
```

### 3. Check Status
```bash
# View service status
./app-control.sh status

# View logs
./app-control.sh logs

# Follow logs in real-time
./app-control.sh logs follow
```

### 4. Access the Platform
Once started, access these URLs:
- **Frontend**: http://localhost:3000
- **User Management API**: http://localhost:8000
- **Course Generator API**: http://localhost:8001  
- **Content Storage API**: http://localhost:8003
- **Course Management API**: http://localhost:8004
- **Content Management API**: http://localhost:8005
- **Lab Manager API**: http://localhost:8006
- **Analytics API**: http://localhost:8007
- **Organization Management API**: http://localhost:8008
- **RAG Service API**: http://localhost:8009

## 🛠️ **Available Commands**

```bash
./app-control.sh start              # Start all services
./app-control.sh stop               # Stop all services
./app-control.sh restart            # Restart all services
./app-control.sh status             # Show service status
./app-control.sh logs [service]     # View logs
./app-control.sh build              # Build Docker images
./app-control.sh rebuild [service]  # Force rebuild (after code changes)
./app-control.sh clean              # Clean up Docker resources
```

## 🎯 **What Each Service Does**

- **user-management** (8000): Authentication, user accounts, sessions
- **course-generator** (8001): AI-powered course content generation  
- **content-storage** (8003): File storage and content management
- **course-management** (8004): Course lifecycle, enrollment, publishing
- **content-management** (8005): Content validation, search, organization
- **lab-manager** (8006): Docker lab containers for student coding
- **analytics** (8007): Learning analytics, progress tracking, reporting
- **organization-management** (8008): Multi-tenant RBAC system
- **rag-service** (8009): AI enhancement with ChromaDB for personalized content
- **frontend** (3000): Web interface with multiple dashboards

## ⚙️ **Environment Configuration (.cc_env)**

Key settings you can customize:
```bash
# AI API Keys (required for content generation)
ANTHROPIC_API_KEY=your_anthropic_key_here
OPENAI_API_KEY=your_openai_key_here

# Database (uses Docker containers by default)
DB_HOST=postgres
DB_PASSWORD=postgres_password

# Environment
ENVIRONMENT=development  # or production
```

## 🐳 **What the Docker Setup Includes**

- **PostgreSQL 15** with database migrations
- **Redis 7** for caching and sessions  
- **ChromaDB** for RAG/AI enhancement
- **All 8 microservices** with health checks
- **Shared volumes** for data persistence
- **Network isolation** with course-creator-network
- **Log aggregation** to /var/log/course-creator

## 🔧 **Development Workflow**

1. **Make code changes** in services/ or frontend/
2. **Rebuild specific service**: `./app-control.sh rebuild [service-name]`
3. **View logs**: `./app-control.sh logs [service-name] follow`
4. **Check status**: `./app-control.sh status`

## 📝 **Notes**

- **No need for the deploy-ubuntu.sh script** - it was overcomplicating things
- **Everything runs in Docker** - no manual Python/Node.js setup needed
- **Database is automatically set up** with migrations on first start
- **Lab containers are managed automatically** by the lab-manager service
- **All services have health checks** and will restart if they fail

## 🚨 **If You Have Issues**

1. **Check Docker is running**: `docker --version && docker-compose --version`
2. **Clean and rebuild**: `./app-control.sh clean && ./app-control.sh build`
3. **Check logs**: `./app-control.sh logs`
4. **Verify environment**: Make sure `.cc_env` exists and has valid settings

The platform is **production-ready** with comprehensive testing, security enhancements, and scalable architecture!