# Course Creator Platform - Production Deployment Guide

## 🚀 **Production-Ready Deployment System**

This deployment system creates a **production-ready Course Creator Platform** with:

- ✅ **Systemd services** for proper service management
- ✅ **Python virtual environment** with all dependencies
- ✅ **PostgreSQL schema** automatically loaded
- ✅ **API key collection** during deployment
- ✅ **Production configuration** (excludes dev files)
- ✅ **Platform-specific settings** and security
- ✅ **Service management tools**

## 📋 **Prerequisites**

- **Ubuntu 20.04 LTS or later**
- **Root/sudo access** 
- **Internet connection** for downloading dependencies
- **API Keys**: Anthropic Claude API key (required), OpenAI API key (optional)

## 🔧 **Deployment Steps**

### 1. **Prepare the Deployment**

```bash
# Clone or copy the Course Creator repository to your server
git clone <repository-url> course-creator
cd course-creator

# Or if transferring from another system:
rsync -av --progress course-creator/ user@server:/path/to/course-creator/
ssh user@server
cd /path/to/course-creator
```

### 2. **Run Production Deployment**

```bash
# Make the deployment script executable
chmod +x deploy-production.sh

# Run the deployment script
sudo ./deploy-production.sh
```

The script will:
- ✅ Check system requirements
- ✅ **Prompt for API keys** (Anthropic required, OpenAI optional)  
- ✅ **Collect deployment settings** (domain, SSL email, etc.)
- ✅ Install system dependencies (Python, PostgreSQL, Redis, nginx)
- ✅ Create users (`course-creator`, `appuser`)
- ✅ **Deploy production files** (excludes tests, claude.md, dev files)
- ✅ Set up Python virtual environment
- ✅ **Install all Python dependencies** from requirements.txt files
- ✅ Configure PostgreSQL and Redis
- ✅ **Load database schema and migrations**
- ✅ Create systemd service files
- ✅ Start all services

### 3. **Verify Deployment**

```bash
# Check service status
./manage-services.sh status

# View logs
./manage-services.sh logs user-management

# Test the platform
curl http://localhost:8000/health
```

## 🎯 **What Gets Deployed**

### **Included in Production**:
- `services/` - All 8 microservices
- `frontend/` - Web interface 
- `shared/` - Shared libraries
- `data/` - Database schema and migrations
- `config/` - Configuration files
- `requirements.txt` files

### **Excluded from Production**:
- `tests/` - Test files
- `claude.md/` - Development documentation  
- `*.test.js`, `test_*.py` - Test files
- `.git/` - Git repository
- `lab-storage/` - Development lab data  
- `deploy-*.sh` - Deployment scripts
- Development markdown files

## 🏗️ **Directory Structure After Deployment**

```
/opt/course-creator/
├── app/                    # Application files
│   ├── services/          # 8 microservices
│   ├── frontend/          # Web interface
│   ├── shared/            # Shared libraries
│   ├── data/              # Database schema
│   └── .cc_env            # Production configuration
├── venv/                  # Python virtual environment
├── logs/                  # Application logs
└── backups/               # Database backups

/var/log/course-creator/   # Service logs
/etc/course-creator/       # System configuration
```

## ⚙️ **Service Management**

### **Using the Service Manager**:
```bash
# Show all service status
./manage-services.sh status

# Start all services
./manage-services.sh start

# Stop all services  
./manage-services.sh stop

# Restart all services
./manage-services.sh restart

# View logs for specific service
./manage-services.sh logs user-management
./manage-services.sh logs course-generator

# Reload configuration
./manage-services.sh reload
```

### **Direct systemctl Commands**:
```bash
# Individual service control
systemctl status course-creator-user-management
systemctl restart course-creator-course-generator
systemctl stop course-creator-*

# View logs
journalctl -u course-creator-user-management -f
journalctl -u course-creator-* --since "1 hour ago"
```

## 🗄️ **Services Created**

| Service | Port | Description |
|---------|------|-------------|
| `course-creator-user-management` | 8000 | User authentication & management |
| `course-creator-course-generator` | 8001 | AI-powered content generation |
| `course-creator-content-storage` | 8003 | File storage & content management |
| `course-creator-course-management` | 8004 | Course lifecycle & enrollment |
| `course-creator-content-management` | 8005 | Content validation & search |
| `course-creator-lab-manager` | 8006 | Docker lab containers |
| `course-creator-analytics` | 8007 | Learning analytics & reporting |
| `course-creator-organization-management` | 8008 | Multi-tenant RBAC |
| `course-creator-rag-service` | 8009 | AI enhancement with ChromaDB |
| `nginx` | 3000 | Frontend web server |

## 🔐 **Configuration**

### **Environment File** (`/opt/course-creator/app/.cc_env`):
```bash
# Generated during deployment with your specific settings
ENVIRONMENT=production
ANTHROPIC_API_KEY=your_key_here
DATABASE_URL=postgresql://course_creator_user:password@localhost/course_creator
# ... and more platform-specific settings
```

### **Database Configuration**:
- **Database**: `course_creator`
- **User**: `course_creator_user` 
- **Schema**: Automatically loaded from `data/` directory
- **Migrations**: Applied in order from `data/migrations/`

## 🌐 **Access URLs**

After deployment, access:
- **Frontend**: http://localhost:3000 (or your domain)
- **API Gateway**: http://localhost:8000
- **Health Checks**: http://localhost:800X/health (for each service)

## 🔧 **Updating the Platform**

To deploy updates:

```bash
# 1. Stop services
./manage-services.sh stop

# 2. Backup current deployment
sudo cp -r /opt/course-creator/app /opt/course-creator/app.backup.$(date +%Y%m%d)

# 3. Deploy new version with force reinstall
sudo ./deploy-production.sh --force-reinstall

# 4. Verify services
./manage-services.sh status
```

## 🛠️ **Troubleshooting**

### **Check Service Logs**:
```bash
# View all service logs
journalctl -u course-creator-* --since "1 hour ago"

# Follow logs for specific service
./manage-services.sh logs user-management
```

### **Common Issues**:

1. **Service won't start**: Check logs with `journalctl -u service-name`
2. **Database connection errors**: Verify PostgreSQL is running and credentials are correct
3. **API key errors**: Check `/opt/course-creator/app/.cc_env` file
4. **Permission errors**: Ensure files are owned by `appuser:course-creator`

### **Database Issues**:
```bash
# Check PostgreSQL status
systemctl status postgresql

# Connect to database
sudo -u postgres psql -d course_creator

# Reload schema
sudo -u postgres psql -d course_creator -f /opt/course-creator/app/data/create_course_creator_schema.sql
```

## 📊 **Monitoring**

### **Service Health**:
```bash
# Check all services
./manage-services.sh status

# Test API endpoints
curl http://localhost:8000/health
curl http://localhost:8001/health
```

### **Log Locations**:
- **Service logs**: `/var/log/course-creator/`
- **System logs**: `journalctl -u course-creator-*`
- **nginx logs**: `/var/log/nginx/`
- **PostgreSQL logs**: `/var/log/postgresql/`

## 🔒 **Security Notes**

- Services run as dedicated `appuser` (non-root)
- Database uses dedicated user with limited permissions
- API keys stored securely in environment file (640 permissions)
- nginx configured with security headers
- Services isolated with systemd security settings

## 📝 **Post-Deployment Checklist**

- [ ] All services show as active: `./manage-services.sh status`
- [ ] Frontend accessible at http://localhost:3000
- [ ] API health checks return 200: `curl http://localhost:8000/health`
- [ ] Database schema loaded successfully
- [ ] API keys working (check course generation)
- [ ] Log files being created in `/var/log/course-creator/`

Your **Course Creator Platform** is now production-ready! 🎉