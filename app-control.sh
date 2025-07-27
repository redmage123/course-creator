#!/bin/bash

# Course Creator Platform Control Script - Docker Only
# Manages all services using Docker Compose

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Load environment variables from .cc_env file
if [ -f "$SCRIPT_DIR/.cc_env" ]; then
    set -a  # automatically export all variables
    source "$SCRIPT_DIR/.cc_env"
    set +a  # stop automatically exporting
fi

# Docker configuration
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yml"
DOCKER_PROJECT_NAME="course-creator"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker and Docker Compose are available
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        log_info "Please install Docker: https://docs.docker.com/get-docker/"
        return 1
    fi

    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running or not accessible"
        log_info "Please start Docker daemon or check permissions"
        return 1
    fi

    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed"
        log_info "Please install Docker Compose: https://docs.docker.com/compose/install/"
        return 1
    fi

    return 0
}

# Get the appropriate Docker Compose command
get_compose_cmd() {
    if command -v docker-compose &> /dev/null; then
        echo "docker-compose"
    else
        echo "docker compose"
    fi
}

# Start all services using Docker Compose
start_docker() {
    log_info "Starting Course Creator Platform with Docker..."
    
    if ! check_docker; then
        log_error "Docker environment not ready"
        return 1
    fi

    local compose_cmd=$(get_compose_cmd)
    
    # Ensure .cc_env file exists with default values
    if [ ! -f "$SCRIPT_DIR/.cc_env" ]; then
        log_warning ".cc_env not found, creating with default values..."
        cat > "$SCRIPT_DIR/.cc_env" << EOF
# Course Creator Environment Variables
DB_PASSWORD=postgres_password
JWT_SECRET_KEY=your-super-secret-key-change-in-production
HOST_IP=localhost
EOF
        log_info "Created .cc_env with default values. Please update as needed."
    fi

    # Load updated environment
    set -a
    source "$SCRIPT_DIR/.cc_env"
    set +a

    log_info "Building and starting services..."
    $compose_cmd -f "$COMPOSE_FILE" -p "$DOCKER_PROJECT_NAME" up -d --build

    # Wait for services to be healthy
    log_info "Waiting for services to become healthy..."
    sleep 10
    
    log_success "Course Creator Platform started successfully!"
    echo
    echo "🌐 Service URLs:"
    echo "  Frontend: http://localhost:3000"
    echo "  User Management: http://localhost:8000"
    echo "  Course Generator: http://localhost:8001"
    echo "  Content Storage: http://localhost:8003"
    echo "  Course Management: http://localhost:8004"
    echo "  Content Management: http://localhost:8005"
    echo "  Lab Manager: http://localhost:8006"
    echo "  Analytics: http://localhost:8007"
    echo
    echo "🗄️ Database & Cache:"
    echo "  PostgreSQL: localhost:5433"
    echo "  Redis: localhost:6379"
    echo
    echo "📋 Management:"
    echo "  Status: $0 status"
    echo "  Logs: $0 logs [service-name]"
    echo "  Stop: $0 stop"
}

# Stop all Docker services
stop_docker() {
    log_info "Stopping Course Creator Platform Docker services..."
    
    if ! check_docker; then
        log_error "Docker environment not ready"
        return 1
    fi
    
    local compose_cmd=$(get_compose_cmd)
    
    $compose_cmd -f "$COMPOSE_FILE" -p "$DOCKER_PROJECT_NAME" down
    
    log_success "Docker services stopped"
}

# Restart all Docker services
restart_docker() {
    log_info "Restarting Course Creator Platform with Docker..."
    stop_docker
    sleep 2
    start_docker
}

# Show status of all Docker containers
docker_status() {
    if ! check_docker; then
        log_error "Docker environment not ready"
        return 1
    fi
    
    local compose_cmd=$(get_compose_cmd)
    
    echo "Course Creator Platform - Docker Status"
    echo "======================================"
    echo
    
    # Show compose services status
    if $compose_cmd -f "$COMPOSE_FILE" -p "$DOCKER_PROJECT_NAME" ps --format table 2>/dev/null; then
        echo
    else
        log_warning "No services found or Docker Compose not available"
        echo "Container Status:"
        docker ps --filter "name=${DOCKER_PROJECT_NAME}" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    fi
    
    echo
    echo "🔍 Health Status:"
    
    # List of expected services and ports
    declare -a services=(
        "course-creator-user-management-1:8000:User Management"
        "course-creator-course-generator-1:8001:Course Generator"
        "course-creator-content-storage-1:8003:Content Storage"
        "course-creator-course-management-1:8004:Course Management"
        "course-creator-content-management-1:8005:Content Management"
        "course-creator-lab-manager-1:8006:Lab Manager"
        "course-creator-analytics-1:8007:Analytics"
        "course-creator-frontend-1:3000:Frontend"
        "course-creator-postgres-1:5433:PostgreSQL"
        "course-creator-redis-1:6379:Redis"
    )
    
    for service_info in "${services[@]}"; do
        IFS=':' read -r container_name port service_display_name <<< "$service_info"
        
        # Check if container is running
        if docker ps --format '{{.Names}}' | grep -q "^${container_name}$"; then
            # Check container health
            health=$(docker inspect --format='{{.State.Health.Status}}' "$container_name" 2>/dev/null || echo "no-health-check")
            if [ "$health" = "healthy" ]; then
                echo -e "  ✅ ${service_display_name} (${container_name}) - Healthy"
            elif [ "$health" = "unhealthy" ]; then
                echo -e "  ❌ ${service_display_name} (${container_name}) - Unhealthy"
            elif [ "$health" = "starting" ]; then
                echo -e "  🔄 ${service_display_name} (${container_name}) - Starting"
            else
                # No health check defined, check if container is running
                status=$(docker inspect --format='{{.State.Status}}' "$container_name" 2>/dev/null || echo "not-found")
                if [ "$status" = "running" ]; then
                    echo -e "  ✅ ${service_display_name} (${container_name}) - Running"
                else
                    echo -e "  ❌ ${service_display_name} (${container_name}) - ${status}"
                fi
            fi
        else
            echo -e "  ❌ ${service_display_name} (${container_name}) - Not Running"
        fi
    done
    
    echo
    echo "🔗 Quick Links:"
    echo "  Dashboard: http://localhost:3000"
    echo "  API Health: http://localhost:8000/health"
}

# Show logs for specific service or all services
docker_logs() {
    if ! check_docker; then
        log_error "Docker environment not ready"
        return 1
    fi
    
    local service_name="${1:-}"
    local follow_flag="${2:-}"
    local compose_cmd=$(get_compose_cmd)
    
    if [ -z "$service_name" ]; then
        log_info "Showing logs for all services..."
        if [ "$follow_flag" = "follow" ] || [ "$follow_flag" = "-f" ]; then
            $compose_cmd -f "$COMPOSE_FILE" -p "$DOCKER_PROJECT_NAME" logs -f
        else
            $compose_cmd -f "$COMPOSE_FILE" -p "$DOCKER_PROJECT_NAME" logs --tail=50
        fi
    else
        log_info "Showing logs for service: $service_name"
        if [ "$follow_flag" = "follow" ] || [ "$follow_flag" = "-f" ]; then
            $compose_cmd -f "$COMPOSE_FILE" -p "$DOCKER_PROJECT_NAME" logs -f "$service_name"
        else
            $compose_cmd -f "$COMPOSE_FILE" -p "$DOCKER_PROJECT_NAME" logs --tail=50 "$service_name"
        fi
    fi
}

# Build Docker images from scratch
docker_build() {
    log_info "Building Course Creator Platform Docker images..."
    
    if ! check_docker; then
        log_error "Docker environment not ready"
        return 1
    fi
    
    local compose_cmd=$(get_compose_cmd)
    
    $compose_cmd -f "$COMPOSE_FILE" -p "$DOCKER_PROJECT_NAME" build --no-cache
    
    log_success "Docker images built successfully"
}

# Pull latest base Docker images
docker_pull() {
    log_info "Pulling latest base Docker images..."
    
    if ! check_docker; then
        log_error "Docker environment not ready"
        return 1
    fi
    
    local compose_cmd=$(get_compose_cmd)
    
    $compose_cmd -f "$COMPOSE_FILE" -p "$DOCKER_PROJECT_NAME" pull
    
    log_success "Docker images pulled successfully"
}

# Clean up Docker resources
docker_clean() {
    log_info "Cleaning up Course Creator Docker resources..."
    
    if ! check_docker; then
        log_error "Docker environment not ready"
        return 1
    fi
    
    local compose_cmd=$(get_compose_cmd)
    
    # Stop and remove containers, networks, volumes
    $compose_cmd -f "$COMPOSE_FILE" -p "$DOCKER_PROJECT_NAME" down -v --remove-orphans
    
    # Remove unused images (be careful with this)
    read -p "Remove unused Docker images? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker image prune -f
        log_success "Unused Docker images removed"
    fi
    
    log_success "Docker cleanup completed"
}

# Main command handler
case "${1:-}" in
    start)
        start_docker
        ;;
    stop)
        stop_docker
        ;;
    restart)
        restart_docker
        ;;
    status)
        docker_status
        ;;
    logs)
        docker_logs "$2" "$3"
        ;;
    build)
        docker_build
        ;;
    pull)
        docker_pull
        ;;
    clean)
        docker_clean
        ;;
    # Legacy docker-* commands for backward compatibility
    docker-start)
        start_docker
        ;;
    docker-stop)
        stop_docker
        ;;
    docker-restart)
        restart_docker
        ;;
    docker-status)
        docker_status
        ;;
    docker-logs)
        docker_logs "$2" "$3"
        ;;
    docker-build)
        docker_build
        ;;
    docker-pull)
        docker_pull
        ;;
    docker-clean)
        docker_clean
        ;;
    *)
        echo "Course Creator Platform Control Script (Docker Only)"
        echo
        echo "Usage: $0 {start|stop|restart|status|logs|build|pull|clean}"
        echo
        echo "Commands:"
        echo "  start            Start all services using Docker Compose"
        echo "  stop             Stop all Docker containers"
        echo "  restart          Restart all services using Docker Compose"
        echo "  status           Show status of all Docker containers"
        echo "  logs [service]   Show logs for all services or specific service"
        echo "                   Add 'follow' or '-f' to follow logs in real-time"
        echo "  build            Build Docker images from scratch"
        echo "  pull             Pull latest base Docker images"
        echo "  clean            Clean up Docker resources (containers, volumes, images)"
        echo
        echo "Legacy Commands (backward compatibility):"
        echo "  docker-start     Same as 'start'"
        echo "  docker-stop      Same as 'stop'"
        echo "  docker-restart   Same as 'restart'"
        echo "  docker-status    Same as 'status'"
        echo "  docker-logs      Same as 'logs'"
        echo "  docker-build     Same as 'build'"
        echo "  docker-pull      Same as 'pull'"
        echo "  docker-clean     Same as 'clean'"
        echo
        echo "Service Names for logs:"
        echo "  user-management, course-generator, content-storage,"
        echo "  course-management, content-management, lab-manager,"
        echo "  analytics, frontend, postgres, redis"
        echo
        echo "Examples:"
        echo "  $0 start"
        echo "  $0 status"
        echo "  $0 logs user-management"
        echo "  $0 logs analytics follow"
        echo "  $0 restart"
        echo
        echo "Environment:"
        echo "  Create .cc_env file with DB_PASSWORD and other secrets"
        echo "  Example: echo 'DB_PASSWORD=your_password' > .cc_env"
        echo
        echo "🐳 All operations use Docker - no native deployment supported"
        exit 1
        ;;
esac