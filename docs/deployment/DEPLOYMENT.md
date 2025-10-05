# Course Creator Platform - Deployment Guide

## 🚀 Universal Linux Deployment System

### **Version**: 3.0.0 (Universal Linux Support - 96%+ Security Score)

This deployment system provides **enterprise-grade, production-ready deployment** of the Course Creator Platform on **ANY** Linux distribution with comprehensive security, monitoring, and automated setup.

## 📱 Supported Linux Distributions

- **Ubuntu / Debian** (apt package manager)
- **CentOS / RHEL / Rocky Linux / AlmaLinux** (yum/dnf)
- **Fedora** (dnf)
- **openSUSE / SUSE Enterprise** (zypper)
- **Arch Linux / Manjaro** (pacman)
- **Alpine Linux** (apk)
- **Any modern Linux distribution** with automatic detection

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Prerequisites](#prerequisites)
3. [Deployment Options](#deployment-options)
4. [Security Features](#security-features)
5. [Post-Deployment Configuration](#post-deployment-configuration)
6. [Monitoring and Maintenance](#monitoring-and-maintenance)
7. [Troubleshooting](#troubleshooting)
8. [Advanced Configuration](#advanced-configuration)

---

## 🚀 Quick Start

### Automated Deployment (Recommended)

```bash
# 1. Download the universal deployment script
wget https://raw.githubusercontent.com/yourusername/course-creator/main/deploy-linux.sh
chmod +x deploy-linux.sh

# 2. Development deployment (default)
sudo ./deploy-linux.sh

# 3. Production deployment with SSL
sudo ./deploy-linux.sh --production --domain yourdomain.com --ssl-email admin@yourdomain.com
```

### Manual Deployment

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/course-creator.git
cd course-creator

# 2. Run deployment script
# Use deploy-linux.sh for universal Linux support
sudo ./deploy-linux.sh [OPTIONS]

# Or use deploy-ubuntu.sh for Ubuntu-specific optimizations
sudo ./deploy-ubuntu.sh [OPTIONS]
```

---

## 📦 Prerequisites

### System Requirements

- **Operating System**: Any modern Linux distribution (2018 or later)
  - Ubuntu 18.04+ / Debian 10+
  - CentOS 7+ / RHEL 7+ / Rocky Linux 8+
  - Fedora 30+ / openSUSE Leap 15+
  - Arch Linux / Alpine Linux 3.12+
- **Memory**: Minimum 4GB RAM (8GB+ recommended for production)
- **Storage**: Minimum 20GB available disk space
- **Network**: Internet connection for package downloads
- **Access**: Root or sudo privileges

### Required Information for Production

- **Domain name** (for SSL certificate)
- **Email address** (for Let's Encrypt notifications)
- **API keys** (Anthropic Claude, OpenAI - for AI features)
- **SMTP credentials** (for email notifications)

---

## 🔧 Deployment Options

### Development Deployment

```bash
# Universal Linux deployment (auto-detects distribution)
sudo ./deploy-linux.sh

# Or Ubuntu-specific deployment
sudo ./deploy-ubuntu.sh
```

**Features**:
- HTTPS by default (secure connections)
- Debug mode enabled
- API documentation accessible
- All service ports exposed
- Local development optimized

**Note**: The application now uses HTTPS as the default protocol for enhanced security. If you need to use HTTP for local development without SSL certificates, modify `frontend/js/config.js` and change `PROTOCOL: 'https'` to `PROTOCOL: 'http'`.

### Production Deployment

```bash
# Universal Linux deployment (auto-detects distribution)
sudo ./deploy-linux.sh --production --domain yourdomain.com --ssl-email admin@yourdomain.com

# Or Ubuntu-specific deployment
sudo ./deploy-ubuntu.sh --production --domain yourdomain.com --ssl-email admin@yourdomain.com
```

**Features**:
- HTTPS with Let's Encrypt SSL
- Security headers enabled
- Rate limiting active
- Debug mode disabled
- Production optimized

### Available Options

| Option | Description |
|--------|-------------|
| `--production` | Deploy in production mode |
| `--domain DOMAIN` | Set domain name for SSL/TLS |
| `--ssl-email EMAIL` | Email for Let's Encrypt SSL |
| `--skip-db` | Skip database setup |
| `--skip-ssl` | Skip SSL certificate setup |
| `--help` | Show help message |

---

## 🛡️ Security Features

### Universal Linux Distribution Support

- **Automatic Detection**: Intelligently detects your Linux distribution and adapts accordingly
- **Package Manager Support**: Works with apt, yum, dnf, zypper, pacman, and apk
- **Init System Compatibility**: Supports systemd, OpenRC, and SysV init systems
- **Firewall Integration**: Configures ufw, firewalld, or iptables based on distribution
- **Service Management**: Creates appropriate service files for your init system

### OWASP Top 10 2021 Compliance (96%+ Score)

#### ✅ A01: Broken Access Control - FULLY PROTECTED
- **Multi-Tenant Security**: 100% organization isolation
- **RBAC Implementation**: Complete role-based access control
- **Horizontal Privilege Escalation**: Prevented with organization middleware
- **Vertical Privilege Escalation**: Protected with role-based restrictions

#### ✅ A02: Cryptographic Failures - FULLY PROTECTED
- **JWT Security**: HS256 algorithm, no vulnerabilities
- **Password Security**: bcrypt hashing
- **TLS/HTTPS**: Production HTTPS with HSTS
- **Logging Security**: No sensitive data exposure

#### ✅ A03: Injection - FULLY PROTECTED
- **SQL Injection**: Parameterized queries
- **Command Injection**: Input sanitization
- **XSS Prevention**: Output encoding + CSP headers

#### ✅ A04: Insecure Design - FULLY PROTECTED
- **Rate Limiting**: Advanced token bucket algorithm
- **Security Headers**: Comprehensive CSP, HSTS, X-Frame-Options
- **Business Logic Security**: RBAC validation

#### ✅ A05: Security Misconfiguration - FULLY PROTECTED
- **Production Hardening**: Debug features disabled
- **Secure Configuration**: Production-ready settings
- **Error Messages**: Generic responses prevent info disclosure

### Additional Security Features

- **Firewall Configuration**: UFW with restrictive rules
- **Fail2ban Protection**: Intrusion prevention system
- **Container Security**: Read-only containers, no-new-privileges
- **Network Isolation**: Private Docker networks
- **Monitoring**: Comprehensive logging and metrics

---

## ⚙️ Post-Deployment Configuration

### 1. Configure API Keys

```bash
# Edit the secrets file
sudo nano /opt/course-creator/.env.secrets

# Add your API keys:
ANTHROPIC_API_KEY=your_anthropic_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

### 2. Configure Email Settings

```bash
# Edit the secrets file
sudo nano /opt/course-creator/.env.secrets

# Configure SMTP:
SMTP_HOST=your_smtp_server.com
SMTP_PORT=587
SMTP_USER=your_smtp_username
SMTP_PASSWORD=your_smtp_password
FROM_EMAIL=noreply@yourdomain.com
```

### 3. Create Admin User

```bash
cd /opt/course-creator/course-creator
sudo -u course-creator python create-admin.py
```

### 4. Restart Services

```bash
sudo systemctl restart course-creator-*
```

---

## 📊 Monitoring and Maintenance

### Health Monitoring

```bash
# Run comprehensive health check
sudo /opt/course-creator/monitor.sh

# Advanced health check with security validation
sudo /opt/course-creator/course-creator/deploy/health-check.sh --security --performance

# JSON output for monitoring systems
sudo /opt/course-creator/course-creator/deploy/health-check.sh --json --silent
```

### Service Management

```bash
# Check all services
sudo systemctl status course-creator-*

# Restart all services
sudo systemctl restart course-creator-*

# View service logs
sudo journalctl -u course-creator-* -f

# View specific service logs
sudo journalctl -u course-creator-user-management -f
```

### Log Monitoring

```bash
# View centralized logs
sudo tail -f /var/log/course-creator/*.log

# View specific service logs
sudo tail -f /var/log/course-creator/user-management.log
```

### Performance Monitoring

The deployment includes Prometheus and Grafana for monitoring:

- **Prometheus**: http://localhost:9090 (metrics collection)
- **Grafana**: http://localhost:3001 (visualization dashboards)

---

## 🔍 Troubleshooting

### Common Issues

#### Service Not Starting

```bash
# Check service status
sudo systemctl status course-creator-SERVICE_NAME

# View detailed logs
sudo journalctl -u course-creator-SERVICE_NAME -n 50

# Check service health
curl -f http://localhost:PORT/health
```

#### Database Connection Issues

```bash
# Test database connectivity
sudo -u postgres psql -d course_creator -c "SELECT 1;"

# Check database service
sudo systemctl status postgresql

# View database logs
sudo journalctl -u postgresql -n 50
```

#### SSL Certificate Issues

```bash
# Check certificate status
sudo certbot certificates

# Renew certificates manually
sudo certbot renew

# Check Nginx configuration
sudo nginx -t
```

#### Permission Issues

```bash
# Fix file permissions
sudo chown -R course-creator:course-creator /opt/course-creator
sudo chmod -R 755 /opt/course-creator
sudo chmod 600 /opt/course-creator/.env.*
```

### Diagnostic Commands

```bash
# System health overview
sudo /opt/course-creator/monitor.sh

# Network connectivity
sudo netstat -tlnp | grep -E "(3000|800[0-8]|5432|6379)"

# Docker status (if using Docker deployment)
sudo docker ps -a
sudo docker-compose ps

# Firewall status
sudo ufw status verbose

# Resource usage
htop
df -h
free -h
```

---

## 🏗️ Advanced Configuration

### Docker Deployment

For container-based deployment:

```bash
# Copy and configure environment
cp deploy/production.env.template .env.production
# Edit .env.production with your values

# Deploy with Docker Compose
docker-compose -f deploy/docker-compose.production.yml up -d

# Monitor services
docker-compose -f deploy/docker-compose.production.yml ps
```

### Load Balancer Configuration

For high-availability deployments with multiple instances:

```nginx
# Example Nginx upstream configuration
upstream course_creator_backend {
    server 10.0.1.10:3000;
    server 10.0.1.11:3000;
    server 10.0.1.12:3000;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    location / {
        proxy_pass http://course_creator_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Database Clustering

For production database clustering:

```bash
# Configure PostgreSQL streaming replication
# See deploy/postgres-cluster-setup.sh for detailed instructions
```

### Backup Configuration

```bash
# Configure automated backups
sudo systemctl enable course-creator-backup.timer
sudo systemctl start course-creator-backup.timer

# Manual backup
sudo /opt/course-creator/scripts/backup.sh
```

---

## 📁 File Structure

```
/opt/course-creator/
├── course-creator/              # Application code
├── .env.secrets                 # API keys and secrets
├── .env.database               # Database credentials
├── monitor.sh                  # Monitoring script
├── backups/                    # Backup storage
└── logs/                       # Application logs

/etc/systemd/system/
├── course-creator-*.service    # Service definitions

/etc/nginx/
├── sites-available/course-creator
└── sites-enabled/course-creator

/var/log/course-creator/        # Centralized logs
```

---

## 🌐 Access URLs

After successful deployment:

### Public URLs
- **Platform**: http(s)://yourdomain.com
- **Admin Dashboard**: http(s)://yourdomain.com/admin.html
- **Instructor Dashboard**: http(s)://yourdomain.com/instructor-dashboard.html
- **Student Dashboard**: http(s)://yourdomain.com/student-dashboard.html

### Development URLs (if deployed in development mode)
- **Frontend**: https://localhost:3000
- **User Management**: https://localhost:8000
- **Course Generator**: https://localhost:8001
- **Content Storage**: https://localhost:8003
- **Course Management**: https://localhost:8004
- **Content Management**: https://localhost:8005
- **Lab Manager**: https://localhost:8006
- **Analytics**: https://localhost:8007
- **Organization Management**: https://localhost:8008

### Monitoring URLs
- **Prometheus**: https://localhost:9090
- **Grafana**: https://localhost:3001

---

## 🆘 Support

### Documentation
- **Platform Documentation**: `docs/` directory
- **API Documentation**: Available at `/docs` endpoint (development mode)
- **Security Assessment**: `OWASP_SECURITY_ASSESSMENT_SUMMARY.md`

### Getting Help
- **Issues**: https://github.com/yourusername/course-creator/issues
- **Discussions**: https://github.com/yourusername/course-creator/discussions
- **Wiki**: https://github.com/yourusername/course-creator/wiki

### Professional Support
For professional deployment assistance, security consulting, or custom development:
- Email: support@course-creator-platform.com
- Enterprise Support: enterprise@course-creator-platform.com

---

## 📜 License

This deployment system is part of the Course Creator Platform and is licensed under the MIT License. See `LICENSE` file for details.

---

## 🎉 Success!

Your Course Creator Platform is now deployed with enterprise-grade security and monitoring. The platform includes:

- ✅ **96%+ OWASP Security Score** (EXCELLENT rating)
- ✅ **Multi-Tenant Organization Isolation**
- ✅ **Advanced Rate Limiting & DoS Protection**
- ✅ **Comprehensive Security Headers**
- ✅ **Production-Hardened Configuration**
- ✅ **Automated Health Monitoring**
- ✅ **Centralized Logging & Metrics**

**Next Steps**:
1. Configure API keys and email settings
2. Create your first admin user
3. Set up monitoring dashboards
4. Begin creating educational content!

---

*Deployment Guide v3.0.0 - Universal Linux Support*  
*Course Creator Platform Team*

---

## 🔄 Migration from Ubuntu-Only Deployment

If you're currently using the Ubuntu-specific deployment script:

```bash
# Your existing Ubuntu deployment continues to work
sudo ./deploy-ubuntu.sh [options]

# Or migrate to universal deployment (recommended)
sudo ./deploy-linux.sh [options]
```

The universal deployment script provides:
- **Broader compatibility** across Linux distributions
- **Automatic detection** and adaptation
- **Enhanced portability** for multi-environment deployments
- **Future-proof** support for new distributions