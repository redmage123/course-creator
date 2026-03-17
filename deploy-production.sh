#!/bin/bash

#
# COURSE CREATOR PLATFORM - PRODUCTION DEPLOYMENT SCRIPT
# ======================================================
#
# Production deployment script for Ubuntu systems (20.04 LTS and later)
# Creates systemctl services, installs dependencies, sets up database schema
#
# FEATURES:
# - Production-ready systemctl services
# - PostgreSQL schema loading
# - API key collection and validation
# - Python dependency installation
# - Excludes development files
# - Platform-specific configuration
# - User and permission management
#
# VERSION: 4.0.0 (Production Ready)
#

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# =============================================================================
# CONFIGURATION AND CONSTANTS
# =============================================================================

readonly SCRIPT_VERSION="4.0.0"
readonly SCRIPT_NAME="Course Creator Platform Production Deployment"
readonly MIN_UBUNTU_VERSION="20.04"

# Default configuration
DEPLOYMENT_MODE="production"
DOMAIN_NAME=""
SSL_EMAIL=""
SKIP_DATABASE=false
SKIP_SSL=false
FORCE_REINSTALL=false
DEBUG_MODE=false
INSTALL_DIR="/opt/course-creator"
SERVICE_USER="course-creator"
APP_USER="appuser"
DATABASE_NAME="course_creator"
DATABASE_USER="course_creator_user"
DATABASE_PASSWORD=""
REDIS_PASSWORD=""
JWT_SECRET_KEY=""
ANTHROPIC_API_KEY=""
OPENAI_API_KEY=""

# Python configuration
PYTHON_VERSION="3.11"
VENV_DIR="${INSTALL_DIR}/venv"

# Service ports
API_GATEWAY_PORT=8000
CONTENT_GENERATOR_PORT=8001
CONTENT_STORAGE_PORT=8003
COURSE_MANAGEMENT_PORT=8004
CONTENT_MANAGEMENT_PORT=8005
LAB_MANAGER_PORT=8006
ANALYTICS_PORT=8007
ORGANIZATION_MANAGEMENT_PORT=8008
RAG_SERVICE_PORT=8009
USER_INTERFACE_PORT=3000
DB_PORT=5432
REDIS_PORT=6379

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly PURPLE='\033[0;35m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m' # No Color

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case "$level" in
        "INFO")  echo -e "${GREEN}[INFO]${NC}  [$timestamp] $message" ;;
        "WARN")  echo -e "${YELLOW}[WARN]${NC}  [$timestamp] $message" ;;
        "ERROR") echo -e "${RED}[ERROR]${NC} [$timestamp] $message" ;;
        "DEBUG") 
            if [[ "$DEBUG_MODE" == "true" ]]; then
                echo -e "${BLUE}[DEBUG]${NC} [$timestamp] $message"
            fi
            ;;
        "SUCCESS") echo -e "${GREEN}[SUCCESS]${NC} [$timestamp] $message" ;;
        *)       echo -e "${CYAN}[$level]${NC} [$timestamp] $message" ;;
    esac
}

error_exit() {
    log "ERROR" "$1"
    exit 1
}

check_command_exists() {
    command -v "$1" &> /dev/null
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        error_exit "This script must be run as root or with sudo"
    fi
}

check_ubuntu_version() {
    local version
    version=$(lsb_release -rs 2>/dev/null || echo "0.0")
    
    if ! check_command_exists lsb_release; then
        error_exit "Cannot determine Ubuntu version. Please ensure you're running Ubuntu ${MIN_UBUNTU_VERSION} or later."
    fi
    
    if (( $(echo "$version < $MIN_UBUNTU_VERSION" | bc -l) )); then
        error_exit "Ubuntu ${MIN_UBUNTU_VERSION} or later is required. Found: $version"
    fi
    
    log "INFO" "Ubuntu version check passed: $version"
}

generate_password() {
    local length="${1:-32}"
    openssl rand -base64 "$length" | tr -d "=+/" | cut -c1-"$length"
}

# =============================================================================
# USER INPUT AND API KEY COLLECTION
# =============================================================================

collect_api_keys() {
    log "INFO" "Collecting API keys for Course Creator Platform..."
    echo ""
    echo -e "${YELLOW}========================================${NC}"
    echo -e "${YELLOW}   API KEY CONFIGURATION REQUIRED${NC}"
    echo -e "${YELLOW}========================================${NC}"
    echo ""
    echo "The Course Creator Platform requires API keys for AI-powered features:"
    echo "• Anthropic Claude API - for advanced content generation"
    echo "• OpenAI API - for additional AI capabilities"
    echo ""
    echo "You can obtain these keys from:"
    echo "• Anthropic: https://console.anthropic.com/"
    echo "• OpenAI: https://platform.openai.com/api-keys"
    echo ""
    
    # Collect Anthropic API Key
    while [[ -z "$ANTHROPIC_API_KEY" ]]; do
        echo -n "Enter your Anthropic API key: "
        read -r ANTHROPIC_API_KEY
        
        if [[ -z "$ANTHROPIC_API_KEY" ]]; then
            echo -e "${RED}Error: Anthropic API key is required${NC}"
            echo "Press Enter to try again, or Ctrl+C to exit"
            read -r
        elif [[ ! "$ANTHROPIC_API_KEY" =~ ^sk-ant-api03- ]]; then
            echo -e "${YELLOW}Warning: This doesn't look like a valid Anthropic API key${NC}"
            echo -n "Continue anyway? (y/N): "
            read -r confirm
            if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
                ANTHROPIC_API_KEY=""
            fi
        fi
    done
    
    # Collect OpenAI API Key (optional)
    echo ""
    echo -n "Enter your OpenAI API key (optional, press Enter to skip): "
    read -r OPENAI_API_KEY
    
    if [[ -n "$OPENAI_API_KEY" && ! "$OPENAI_API_KEY" =~ ^sk- ]]; then
        echo -e "${YELLOW}Warning: This doesn't look like a valid OpenAI API key${NC}"
        echo -n "Continue anyway? (y/N): "
        read -r confirm
        if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
            OPENAI_API_KEY=""
        fi
    fi
    
    echo ""
    log "SUCCESS" "API keys collected successfully"
}

collect_deployment_settings() {
    log "INFO" "Collecting deployment settings..."
    echo ""
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}   DEPLOYMENT CONFIGURATION${NC}"
    echo -e "${CYAN}========================================${NC}"
    echo ""
    
    # Domain name
    echo -n "Enter your domain name (optional, for SSL setup): "
    read -r DOMAIN_NAME
    
    if [[ -n "$DOMAIN_NAME" ]]; then
        echo -n "Enter email for SSL certificate: "
        read -r SSL_EMAIL
    fi
    
    # Database password
    echo ""
    echo -n "Enter database password (press Enter for auto-generated): "
    read -r DATABASE_PASSWORD
    
    if [[ -z "$DATABASE_PASSWORD" ]]; then
        DATABASE_PASSWORD=$(generate_password 16)
        log "INFO" "Generated secure database password"
    fi
    
    log "SUCCESS" "Deployment settings collected"
}

# =============================================================================
# SYSTEM SETUP
# =============================================================================

install_system_dependencies() {
    log "INFO" "Installing system dependencies..."
    
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -qq
    
    # Essential packages
    local packages=(
        "python${PYTHON_VERSION}"
        "python${PYTHON_VERSION}-dev"
        "python${PYTHON_VERSION}-venv"
        "python3-pip"
        "postgresql"
        "postgresql-contrib"
        "redis-server"
        "nginx"
        "supervisor"
        "git"
        "curl"
        "wget"
        "unzip"
        "rsync"
        "openssl"
        "bc"
        "jq"
        "htop"
    )
    
    if apt-get install -y "${packages[@]}"; then
        log "SUCCESS" "System dependencies installed"
    else
        error_exit "Failed to install system dependencies"
    fi
}

create_users_and_directories() {
    log "INFO" "Creating users and directories..."
    
    # Create service user
    if ! id "$SERVICE_USER" &>/dev/null; then
        useradd --system --shell /bin/bash --home "$INSTALL_DIR" --create-home "$SERVICE_USER"
        log "SUCCESS" "Created service user: $SERVICE_USER"
    fi
    
    # Create app user
    if ! id "$APP_USER" &>/dev/null; then
        useradd --system --shell /bin/bash --home "${INSTALL_DIR}/app" --create-home "$APP_USER"
        usermod -aG "$SERVICE_USER" "$APP_USER"
        log "SUCCESS" "Created application user: $APP_USER"
    fi
    
    # Create directories
    local directories=(
        "$INSTALL_DIR"
        "${INSTALL_DIR}/app"
        "${INSTALL_DIR}/logs"
        "${INSTALL_DIR}/backups"
        "/var/log/course-creator"
        "/var/run/course-creator"
        "/etc/course-creator"
    )
    
    for dir in "${directories[@]}"; do
        mkdir -p "$dir"
    done
    
    # Set ownership
    chown -R "${SERVICE_USER}:${SERVICE_USER}" "$INSTALL_DIR"
    chown -R "${APP_USER}:${SERVICE_USER}" "${INSTALL_DIR}/app"
    chown -R "${APP_USER}:adm" "/var/log/course-creator"
    chown -R "${APP_USER}:${SERVICE_USER}" "/var/run/course-creator"
    chown -R "root:${SERVICE_USER}" "/etc/course-creator"
    
    log "SUCCESS" "Users and directories created"
}

# =============================================================================
# PROJECT DEPLOYMENT
# =============================================================================

deploy_production_files() {
    log "INFO" "Deploying production files..."
    
    local source_dir="$(pwd)"
    local target_dir="${INSTALL_DIR}/app"
    
    # Verify we're in the right source directory
    if [[ ! -f "$source_dir/docker-compose.yml" ]] || [[ ! -d "$source_dir/services" ]]; then
        error_exit "Please run this script from the Course Creator project root directory"
    fi
    
    log "INFO" "Deploying from: $source_dir"
    log "INFO" "Deploying to: $target_dir"
    
    # Clean target if force reinstall
    if [[ "$FORCE_REINSTALL" == "true" ]] && [[ -d "$target_dir" ]]; then
        rm -rf "$target_dir"
        mkdir -p "$target_dir"
    fi
    
    # Copy production files, excluding development artifacts
    rsync -av --progress \
        --exclude='*.pyc' \
        --exclude='__pycache__/' \
        --exclude='.git/' \
        --exclude='.pytest_cache/' \
        --exclude='node_modules/' \
        --exclude='*.log' \
        --exclude='.venv/' \
        --exclude='venv/' \
        --exclude='.env*' \
        --exclude='claude.md/' \
        --exclude='CLAUDE.md*' \
        --exclude='tests/' \
        --exclude='*.test.js' \
        --exclude='test_*' \
        --exclude='*_test.py' \
        --exclude='*.spec.js' \
        --exclude='lab-storage/' \
        --exclude='deploy-*.sh' \
        --exclude='DEPLOY_*' \
        --exclude='*.md' \
        --exclude='LICENSE' \
        --exclude='.gitignore' \
        --exclude='pytest.ini' \
        --exclude='mypy.ini' \
        --exclude='playwright.config.js' \
        --exclude='sonar-project.properties' \
        --exclude='sonarqube/' \
        --exclude='jenkins/' \
        "$source_dir/" "$target_dir/"
    
    # Set proper ownership
    chown -R "${APP_USER}:${SERVICE_USER}" "$target_dir"
    
    # Make scripts executable
    find "$target_dir" -name "*.sh" -exec chmod +x {} \;
    
    log "SUCCESS" "Production files deployed to $target_dir"
}

# =============================================================================
# PYTHON ENVIRONMENT SETUP
# =============================================================================

setup_python_environment() {
    log "INFO" "Setting up Python virtual environment..."
    
    # Create virtual environment as app user
    sudo -u "$APP_USER" "python${PYTHON_VERSION}" -m venv "$VENV_DIR"
    
    # Upgrade pip and install wheel
    sudo -u "$APP_USER" bash -c "
        source ${VENV_DIR}/bin/activate
        pip install --upgrade pip setuptools wheel
    "
    
    # Install dependencies from each service
    local services_dir="${INSTALL_DIR}/app/services"
    
    # Install base requirements
    if [[ -f "${INSTALL_DIR}/app/requirements.txt" ]]; then
        sudo -u "$APP_USER" bash -c "
            source ${VENV_DIR}/bin/activate
            pip install -r ${INSTALL_DIR}/app/requirements.txt
        "
    fi
    
    # Install service-specific requirements
    for service_dir in "$services_dir"/*; do
        if [[ -d "$service_dir" ]] && [[ -f "$service_dir/requirements.txt" ]]; then
            local service_name=$(basename "$service_dir")
            log "INFO" "Installing dependencies for $service_name"
            
            sudo -u "$APP_USER" bash -c "
                source ${VENV_DIR}/bin/activate
                pip install -r ${service_dir}/requirements.txt
            "
        fi
    done
    
    log "SUCCESS" "Python environment setup completed"
}

# =============================================================================
# DATABASE SETUP
# =============================================================================

setup_postgresql() {
    log "INFO" "Setting up PostgreSQL database..."
    
    # Start PostgreSQL
    systemctl enable postgresql
    systemctl start postgresql
    
    # Wait for PostgreSQL to be ready
    sleep 5
    
    # Create database user
    sudo -u postgres psql -c "
        CREATE USER ${DATABASE_USER} WITH PASSWORD '${DATABASE_PASSWORD}';
        ALTER USER ${DATABASE_USER} CREATEDB;
    " 2>/dev/null || log "INFO" "Database user may already exist"
    
    # Create database
    sudo -u postgres createdb -O "${DATABASE_USER}" "${DATABASE_NAME}" 2>/dev/null || log "INFO" "Database may already exist"
    
    # Load schema and migrations
    load_database_schema
    
    log "SUCCESS" "PostgreSQL setup completed"
}

load_database_schema() {
    log "INFO" "Loading database schema and migrations..."
    
    local data_dir="${INSTALL_DIR}/app/data"
    local migrations_dir="${data_dir}/migrations"
    
    if [[ ! -d "$data_dir" ]]; then
        log "WARN" "No data directory found, skipping schema loading"
        return 0
    fi
    
    # Load main schema
    if [[ -f "${data_dir}/create_course_creator_schema.sql" ]]; then
        log "INFO" "Loading main schema..."
        sudo -u postgres psql -d "$DATABASE_NAME" -f "${data_dir}/create_course_creator_schema.sql"
    fi
    
    # Load migrations in order
    if [[ -d "$migrations_dir" ]]; then
        log "INFO" "Loading database migrations..."
        
        for migration_file in "$migrations_dir"/*.sql; do
            if [[ -f "$migration_file" ]]; then
                local migration_name=$(basename "$migration_file")
                log "INFO" "Applying migration: $migration_name"
                
                sudo -u postgres psql -d "$DATABASE_NAME" -f "$migration_file" || {
                    log "WARN" "Migration $migration_name may have already been applied"
                }
            fi
        done
    fi
    
    log "SUCCESS" "Database schema loaded successfully"
}

setup_redis() {
    log "INFO" "Setting up Redis..."
    
    # Generate Redis password if not set
    if [[ -z "$REDIS_PASSWORD" ]]; then
        REDIS_PASSWORD=$(generate_password 24)
    fi
    
    # Configure Redis
    local redis_conf="/etc/redis/redis.conf"
    if [[ -f "$redis_conf" ]]; then
        cp "$redis_conf" "${redis_conf}.backup"
        sed -i "s/# requirepass foobared/requirepass ${REDIS_PASSWORD}/" "$redis_conf"
        sed -i "s/bind 127.0.0.1 ::1/bind 127.0.0.1/" "$redis_conf"
    fi
    
    # Start Redis
    systemctl enable redis-server
    systemctl start redis-server
    
    log "SUCCESS" "Redis setup completed"
}

# =============================================================================
# CONFIGURATION FILES
# =============================================================================

create_production_config() {
    log "INFO" "Creating production configuration..."
    
    local config_file="${INSTALL_DIR}/app/.cc_env"
    
    cat > "$config_file" << EOF
# Course Creator Platform - Production Configuration
# Generated on $(date)

# Environment
ENVIRONMENT=production
DEBUG=false

# API Keys
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
OPENAI_API_KEY=${OPENAI_API_KEY:-}

# Database Configuration
DB_HOST=localhost
DB_PORT=${DB_PORT}
DB_USER=${DATABASE_USER}
DB_PASSWORD=${DATABASE_PASSWORD}
DB_NAME=${DATABASE_NAME}
DATABASE_URL=postgresql://${DATABASE_USER}:${DATABASE_PASSWORD}@localhost:${DB_PORT}/${DATABASE_NAME}

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=${REDIS_PORT}
REDIS_PASSWORD=${REDIS_PASSWORD}
REDIS_URL=redis://:${REDIS_PASSWORD}@localhost:${REDIS_PORT}

# Service Ports
API_GATEWAY_PORT=${API_GATEWAY_PORT}
CONTENT_GENERATOR_PORT=${CONTENT_GENERATOR_PORT}
CONTENT_STORAGE_PORT=${CONTENT_STORAGE_PORT}
COURSE_MANAGEMENT_PORT=${COURSE_MANAGEMENT_PORT}
CONTENT_MANAGEMENT_PORT=${CONTENT_MANAGEMENT_PORT}
LAB_MANAGER_PORT=${LAB_MANAGER_PORT}
ANALYTICS_PORT=${ANALYTICS_PORT}
ORGANIZATION_MANAGEMENT_PORT=${ORGANIZATION_MANAGEMENT_PORT}
RAG_SERVICE_PORT=${RAG_SERVICE_PORT}
USER_INTERFACE_PORT=${USER_INTERFACE_PORT}

# Security
JWT_SECRET_KEY=${JWT_SECRET_KEY}
ALLOWED_HOSTS=${DOMAIN_NAME:-localhost},127.0.0.1

# File Paths
LOG_DIR=/var/log/course-creator
UPLOAD_PATH=${INSTALL_DIR}/uploads
VENV_PATH=${VENV_DIR}

# SSL Configuration
DOMAIN_NAME=${DOMAIN_NAME:-}
SSL_EMAIL=${SSL_EMAIL:-}

# Platform Information
DEPLOYMENT_MODE=production
INSTALL_DIR=${INSTALL_DIR}
SERVICE_USER=${SERVICE_USER}
APP_USER=${APP_USER}
EOF
    
    chown "${APP_USER}:${SERVICE_USER}" "$config_file"
    chmod 640 "$config_file"
    
    log "SUCCESS" "Production configuration created"
}

# =============================================================================
# SYSTEMD SERVICES
# =============================================================================

create_systemd_services() {
    log "INFO" "Creating systemd services..."
    
    # Services to create
    local services=(
        "user-management:${API_GATEWAY_PORT}"
        "course-generator:${CONTENT_GENERATOR_PORT}"
        "content-storage:${CONTENT_STORAGE_PORT}"
        "course-management:${COURSE_MANAGEMENT_PORT}"
        "content-management:${CONTENT_MANAGEMENT_PORT}"
        "lab-manager:${LAB_MANAGER_PORT}"
        "analytics:${ANALYTICS_PORT}"
        "organization-management:${ORGANIZATION_MANAGEMENT_PORT}"
        "rag-service:${RAG_SERVICE_PORT}"
    )
    
    for service_info in "${services[@]}"; do
        local service_name="${service_info%%:*}"
        local service_port="${service_info##*:}"
        
        create_service_file "$service_name" "$service_port"
        
        # Enable the service
        systemctl enable "course-creator-${service_name}.service"
        log "SUCCESS" "Created and enabled service: course-creator-${service_name}"
    done
    
    # Create frontend service
    create_frontend_service
    
    # Reload systemd
    systemctl daemon-reload
    
    log "SUCCESS" "All systemd services created"
}

create_service_file() {
    local service_name="$1"
    local service_port="$2"
    
    cat > "/etc/systemd/system/course-creator-${service_name}.service" << EOF
[Unit]
Description=Course Creator Platform - ${service_name^} Service
After=network.target postgresql.service redis.service
Wants=postgresql.service redis.service

[Service]
Type=exec
User=${APP_USER}
Group=${SERVICE_USER}
WorkingDirectory=${INSTALL_DIR}/app/services/${service_name}
Environment=PATH=${VENV_DIR}/bin
EnvironmentFile=${INSTALL_DIR}/app/.cc_env
ExecStart=${VENV_DIR}/bin/python main.py
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=course-creator-${service_name}

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=${INSTALL_DIR}
ReadWritePaths=/var/log/course-creator
ReadWritePaths=/var/run/course-creator

[Install]
WantedBy=multi-user.target
EOF
}

create_frontend_service() {
    # Frontend uses nginx to serve static files
    local frontend_dir="${INSTALL_DIR}/app/frontend"
    
    # Create nginx config for frontend
    cat > "/etc/nginx/sites-available/course-creator" << EOF
server {
    listen ${USER_INTERFACE_PORT};
    server_name ${DOMAIN_NAME:-localhost};
    
    root ${frontend_dir};
    index index.html;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    # API proxy
    location /api/ {
        proxy_pass http://localhost:${API_GATEWAY_PORT}/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
    
    # Static files
    location / {
        try_files \$uri \$uri/ /index.html;
    }
}
EOF
    
    # Enable the site
    ln -sf "/etc/nginx/sites-available/course-creator" "/etc/nginx/sites-enabled/"
    rm -f "/etc/nginx/sites-enabled/default"
    
    # Test and reload nginx
    nginx -t && systemctl reload nginx
    
    log "SUCCESS" "Frontend nginx configuration created"
}

# =============================================================================
# MAIN DEPLOYMENT FUNCTION
# =============================================================================

main() {
    # Print banner
    cat << EOF
${PURPLE}
╔══════════════════════════════════════════════════════════════════╗
║                 COURSE CREATOR PLATFORM                         ║
║                 PRODUCTION DEPLOYMENT                            ║
║                                                                  ║
║                    Version: $SCRIPT_VERSION                         ║
║              Production-Ready Systemd Services                  ║
║              Database Schema Loading & API Keys                 ║
║                  Platform-Specific Configuration                ║
╚══════════════════════════════════════════════════════════════════╝
${NC}

EOF
    
    log "INFO" "Starting Course Creator Platform production deployment..."
    
    # Pre-flight checks
    check_root
    check_ubuntu_version
    
    # Collect user input
    collect_api_keys
    collect_deployment_settings
    
    # Generate security keys
    if [[ -z "$JWT_SECRET_KEY" ]]; then
        JWT_SECRET_KEY=$(generate_password 64)
    fi
    
    # System setup
    log "INFO" "Installing system dependencies..."
    install_system_dependencies
    
    log "INFO" "Creating users and directories..."
    create_users_and_directories
    
    log "INFO" "Deploying production files..."
    deploy_production_files
    
    log "INFO" "Setting up Python environment..."
    setup_python_environment
    
    log "INFO" "Setting up databases..."
    setup_postgresql
    setup_redis
    
    log "INFO" "Creating configuration files..."
    create_production_config
    
    log "INFO" "Creating systemd services..."
    create_systemd_services
    
    # Start services
    log "INFO" "Starting Course Creator Platform services..."
    local services=(
        "course-creator-user-management"
        "course-creator-course-generator"
        "course-creator-content-storage"
        "course-creator-course-management"
        "course-creator-content-management"
        "course-creator-lab-manager"
        "course-creator-analytics"
        "course-creator-organization-management"
        "course-creator-rag-service"
    )
    
    for service in "${services[@]}"; do
        systemctl start "$service"
        log "SUCCESS" "Started service: $service"
    done
    
    # Start nginx for frontend
    systemctl enable nginx
    systemctl start nginx
    
    # Final success message
    log "SUCCESS" "🎉 Course Creator Platform deployment completed! 🎉"
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}   DEPLOYMENT COMPLETE${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "🌐 Service URLs:"
    echo "   Frontend: http://localhost:${USER_INTERFACE_PORT}"
    echo "   API Gateway: http://localhost:${API_GATEWAY_PORT}"
    if [[ -n "$DOMAIN_NAME" ]]; then
        echo "   Public URL: https://${DOMAIN_NAME}"
    fi
    echo ""
    echo "📁 Installation Directory: ${INSTALL_DIR}"
    echo "📝 Configuration File: ${INSTALL_DIR}/app/.cc_env"
    echo "📊 Logs: /var/log/course-creator/"
    echo ""
    echo "🔧 Service Management:"
    echo "   systemctl status course-creator-user-management"
    echo "   systemctl restart course-creator-*"
    echo "   journalctl -u course-creator-user-management -f"
    echo ""
    echo "✅ All services are running and ready for use!"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --force-reinstall)
            FORCE_REINSTALL=true
            shift
            ;;
        --debug)
            DEBUG_MODE=true
            shift
            ;;
        --help)
            echo "$SCRIPT_NAME v$SCRIPT_VERSION"
            echo ""
            echo "Usage: sudo $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --force-reinstall  Force reinstall of all components"
            echo "  --debug           Enable debug output"
            echo "  --help            Show this help message"
            echo ""
            echo "This script will:"
            echo "  • Install all system dependencies"
            echo "  • Create users and directories"
            echo "  • Deploy production files (excluding dev files)"
            echo "  • Set up Python virtual environment"
            echo "  • Configure PostgreSQL and Redis"
            echo "  • Load database schema and migrations"
            echo "  • Create systemd services"
            echo "  • Collect API keys interactively"
            echo "  • Start all services"
            exit 0
            ;;
        *)
            error_exit "Unknown option: $1. Use --help for usage information."
            ;;
    esac
done

# Run main function
main "$@"