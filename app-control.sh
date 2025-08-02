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

# Parse Docker Compose file for service configurations
parse_compose_config() {
    if [ ! -f "$COMPOSE_FILE" ]; then
        log_error "Docker Compose file not found: $COMPOSE_FILE"
        return 1
    fi
    
    # Create temporary arrays for service info
    declare -g -A SERVICE_PORTS=()
    declare -g -A SERVICE_NAMES=()
    declare -g -A SERVICE_CONTAINERS=()
    
    # Parse docker-compose.yml for ports and service names
    local in_services_section=false
    local in_volumes_section=false
    local in_networks_section=false
    local current_service=""
    
    while IFS= read -r line; do
        # Track which section we're in
        if [[ $line =~ ^services:[[:space:]]*$ ]]; then
            in_services_section=true
            in_volumes_section=false
            in_networks_section=false
            continue
        elif [[ $line =~ ^volumes:[[:space:]]*$ ]]; then
            in_services_section=false
            in_volumes_section=true
            in_networks_section=false
            continue
        elif [[ $line =~ ^networks:[[:space:]]*$ ]]; then
            in_services_section=false
            in_volumes_section=false
            in_networks_section=true
            continue
        fi
        
        # Only process service definitions when in services section
        if [[ $in_services_section == true ]]; then
            # Match service definitions (lines that start with service names and have a colon, at top level)
            if [[ $line =~ ^[[:space:]]{2}([a-zA-Z0-9_-]+):[[:space:]]*$ ]]; then
                current_service="${BASH_REMATCH[1]}"
                SERVICE_NAMES["$current_service"]="$current_service"
                SERVICE_CONTAINERS["$current_service"]="${DOCKER_PROJECT_NAME}-${current_service}-1"
            # Match port mappings
            elif [[ $line =~ ^[[:space:]]*-[[:space:]]*\"([0-9]+):([0-9]+)\"[[:space:]]*$ ]] && [[ -n "$current_service" ]]; then
                host_port="${BASH_REMATCH[1]}"
                container_port="${BASH_REMATCH[2]}"
                SERVICE_PORTS["$current_service"]="$host_port"
            fi
        fi
    done < "$COMPOSE_FILE"
    
    # Set display names for services
    SERVICE_NAMES["user-management"]="User Management"
    SERVICE_NAMES["course-generator"]="Course Generator"
    SERVICE_NAMES["content-storage"]="Content Storage"
    SERVICE_NAMES["course-management"]="Course Management"
    SERVICE_NAMES["content-management"]="Content Management"
    SERVICE_NAMES["lab-manager"]="Lab Manager"
    SERVICE_NAMES["analytics"]="Analytics"
    SERVICE_NAMES["organization-management"]="Organization Management (RBAC)"
    SERVICE_NAMES["frontend"]="Frontend"
    SERVICE_NAMES["postgres"]="PostgreSQL"
    SERVICE_NAMES["redis"]="Redis"
    
    return 0
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

    # Parse compose configuration
    parse_compose_config

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
    
    # Display service URLs based on parsed configuration
    for service in frontend user-management course-generator content-storage course-management content-management lab-manager analytics organization-management; do
        if [[ -n "${SERVICE_PORTS[$service]:-}" ]]; then
            display_name="${SERVICE_NAMES[$service]:-$service}"
            echo "  $display_name: http://localhost:${SERVICE_PORTS[$service]}"
        fi
    done
    
    echo
    echo "🗄️ Database & Cache:"
    if [[ -n "${SERVICE_PORTS[postgres]:-}" ]]; then
        echo "  PostgreSQL: localhost:${SERVICE_PORTS[postgres]}"
    fi
    if [[ -n "${SERVICE_PORTS[redis]:-}" ]]; then
        echo "  Redis: localhost:${SERVICE_PORTS[redis]}"
    fi
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
    
    # OPTIMIZED: Batch fetch all container info in single Docker call
    # Get all container names, status, and health in one query
    docker_info=$(docker ps -a --format '{{.Names}}\t{{.Status}}\t{{json .}}' --filter "name=${DOCKER_PROJECT_NAME}" 2>/dev/null)
    
    # Check health of all services from parsed configuration
    for service in "${!SERVICE_CONTAINERS[@]}"; do
        container_name="${SERVICE_CONTAINERS[$service]}"
        display_name="${SERVICE_NAMES[$service]:-$service}"
        
        # Find matching container from batch query (much faster)
        container_line=$(echo "$docker_info" | grep "${container_name}$" | head -1)
        
        if [ -n "$container_line" ]; then
            # Extract container name and status from batch query
            actual_container_name=$(echo "$container_line" | cut -f1)
            container_status=$(echo "$container_line" | cut -f2)
            
            # Quick health check - only inspect if needed
            if [[ "$container_status" == *"healthy"* ]]; then
                echo -e "  ✅ ${display_name} (${container_name}) - Healthy"
            elif [[ "$container_status" == *"unhealthy"* ]]; then
                echo -e "  ❌ ${display_name} (${container_name}) - Unhealthy"
            elif [[ "$container_status" == *"starting"* ]] || [[ "$container_status" == *"health: starting"* ]]; then
                echo -e "  🔄 ${display_name} (${container_name}) - Starting"
            elif [[ "$container_status" == *"Up"* ]]; then
                echo -e "  ✅ ${display_name} (${container_name}) - Running"
            elif [[ "$container_status" == *"Restarting"* ]]; then
                echo -e "  🔄 ${display_name} (${container_name}) - Restarting"
            elif [[ "$container_status" == *"Exited"* ]]; then
                echo -e "  ❌ ${display_name} (${container_name}) - Stopped"
            else
                echo -e "  ❓ ${display_name} (${container_name}) - ${container_status}"
            fi
        else
            echo -e "  ❌ ${display_name} (${container_name}) - Not Running"
        fi
    done
    
    echo
    echo "🔗 Quick Links:"
    # Use parsed frontend port or default
    frontend_port="${SERVICE_PORTS[frontend]:-3000}"
    user_mgmt_port="${SERVICE_PORTS[user-management]:-8000}"
    echo "  Dashboard: http://localhost:${frontend_port}"
    echo "  API Health: http://localhost:${user_mgmt_port}/health"
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

# Force rebuild with no cache - useful for fixing import/code changes
docker_rebuild() {
    local service_name="${1:-}"
    
    log_info "Force rebuilding Course Creator Platform with no cache..."
    
    if ! check_docker; then
        log_error "Docker environment not ready"
        return 1
    fi
    
    local compose_cmd=$(get_compose_cmd)
    
    if [ -n "$service_name" ]; then
        log_info "Force rebuilding specific service: $service_name"
        
        # Stop specific service
        log_info "Stopping service: $service_name"
        $compose_cmd -f "$COMPOSE_FILE" -p "$DOCKER_PROJECT_NAME" stop "$service_name"
        
        # Remove specific container and image
        log_info "Removing container and image for: $service_name"
        $compose_cmd -f "$COMPOSE_FILE" -p "$DOCKER_PROJECT_NAME" rm -f "$service_name"
        docker image rm -f "${DOCKER_PROJECT_NAME}-${service_name}:latest" 2>/dev/null || true
        
        # Force rebuild with no cache
        log_info "Building $service_name with no cache..."
        $compose_cmd -f "$COMPOSE_FILE" -p "$DOCKER_PROJECT_NAME" build --no-cache "$service_name"
        
        # Start the service
        log_info "Starting $service_name..."
        $compose_cmd -f "$COMPOSE_FILE" -p "$DOCKER_PROJECT_NAME" up -d "$service_name"
        
        log_success "Service $service_name rebuilt and started successfully!"
    else
        log_info "Force rebuilding all services"
        
        # Stop all services
        log_info "Stopping all services..."
        $compose_cmd -f "$COMPOSE_FILE" -p "$DOCKER_PROJECT_NAME" down
        
        # Remove all project images
        log_info "Removing all project images..."
        docker images "${DOCKER_PROJECT_NAME}-*" --format "{{.Repository}}:{{.Tag}}" | xargs -I {} docker image rm -f {} 2>/dev/null || true
        
        # Clear build cache
        log_info "Clearing Docker build cache..."
        docker builder prune -f
        
        # Rebuild all with no cache
        log_info "Building all services with no cache..."
        $compose_cmd -f "$COMPOSE_FILE" -p "$DOCKER_PROJECT_NAME" build --no-cache
        
        # Start all services
        log_info "Starting all services..."
        $compose_cmd -f "$COMPOSE_FILE" -p "$DOCKER_PROJECT_NAME" up -d
        
        # Wait for services to be healthy
        log_info "Waiting for services to become healthy..."
        sleep 15
        
        log_success "All services rebuilt and started successfully!"
        echo
        echo "🌐 Service URLs:"
        
        # Display service URLs based on parsed configuration
        for service in frontend user-management course-generator content-storage course-management content-management lab-manager analytics organization-management; do
            if [[ -n "${SERVICE_PORTS[$service]:-}" ]]; then
                display_name="${SERVICE_NAMES[$service]:-$service}"
                echo "  $display_name: http://localhost:${SERVICE_PORTS[$service]}"
            fi
        done
    fi
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
    rebuild)
        docker_rebuild "$2"
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
    docker-rebuild)
        docker_rebuild "$2"
        ;;
    *)
        echo "Course Creator Platform Control Script (Docker Only)"
        echo
        echo "Usage: $0 {start|stop|restart|status|logs|build|pull|clean|rebuild}"
        echo
        echo "Commands:"
        echo "  start              Start all services using Docker Compose"
        echo "  stop               Stop all Docker containers"
        echo "  restart            Restart all services using Docker Compose"
        echo "  status             Show status of all Docker containers"
        echo "  logs [service]     Show logs for all services or specific service"
        echo "                     Add 'follow' or '-f' to follow logs in real-time"
        echo "  build              Build Docker images from scratch"
        echo "  pull               Pull latest base Docker images"
        echo "  clean              Clean up Docker resources (containers, volumes, images)"
        echo "  rebuild [service]  Force rebuild with no-cache (all services or specific service)"
        echo "                     Useful after code changes that don't reflect in containers"
        echo
        echo "Legacy Commands (backward compatibility):"
        echo "  docker-start       Same as 'start'"
        echo "  docker-stop        Same as 'stop'"
        echo "  docker-restart     Same as 'restart'"
        echo "  docker-status      Same as 'status'"
        echo "  docker-logs        Same as 'logs'"
        echo "  docker-build       Same as 'build'"
        echo "  docker-pull        Same as 'pull'"
        echo "  docker-clean       Same as 'clean'"
        echo "  docker-rebuild     Same as 'rebuild'"
        echo
        echo "Service Names for logs and rebuild:"
        
        # Parse and display available service names dynamically
        if parse_compose_config 2>/dev/null; then
            echo -n "  "
            for service in "${!SERVICE_NAMES[@]}"; do
                echo -n "$service, "
            done | sed 's/, $//'
            echo
        else
            echo "  user-management, course-generator, content-storage,"
            echo "  course-management, content-management, lab-manager,"
            echo "  analytics, organization-management, frontend, postgres, redis"
        fi
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