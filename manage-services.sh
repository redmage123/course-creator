#!/bin/bash

#
# Course Creator Platform - Service Management Script
# ==================================================
#
# Manages all Course Creator systemd services
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Course Creator services
SERVICES=(
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

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

show_status() {
    echo -e "${BLUE}Course Creator Platform Service Status:${NC}"
    echo "========================================"
    
    for service in "${SERVICES[@]}"; do
        if systemctl is-active --quiet "$service"; then
            echo -e "${GREEN}✓${NC} $service"
        else
            echo -e "${RED}✗${NC} $service"
        fi
    done
    
    echo ""
    echo "Frontend (nginx): $(systemctl is-active nginx)"
    echo "Database (postgresql): $(systemctl is-active postgresql)"
    echo "Cache (redis): $(systemctl is-active redis-server)"
}

start_services() {
    log_info "Starting Course Creator Platform services..."
    
    # Start dependencies first
    systemctl start postgresql redis-server
    
    for service in "${SERVICES[@]}"; do
        log_info "Starting $service..."
        systemctl start "$service"
    done
    
    systemctl start nginx
    log_success "All services started"
}

stop_services() {
    log_info "Stopping Course Creator Platform services..."
    
    for service in "${SERVICES[@]}"; do
        log_info "Stopping $service..."
        systemctl stop "$service" || true
    done
    
    log_success "All services stopped"
}

restart_services() {
    log_info "Restarting Course Creator Platform services..."
    stop_services
    sleep 2
    start_services
}

show_logs() {
    local service="$1"
    
    if [[ -n "$service" ]]; then
        if [[ "$service" =~ ^course-creator- ]]; then
            journalctl -u "$service" -f
        else
            journalctl -u "course-creator-$service" -f
        fi
    else
        echo "Available services:"
        for service in "${SERVICES[@]}"; do
            echo "  ${service#course-creator-}"
        done
        echo ""
        echo "Usage: $0 logs <service-name>"
        echo "Example: $0 logs user-management"
    fi
}

reload_config() {
    log_info "Reloading configuration..."
    systemctl daemon-reload
    
    for service in "${SERVICES[@]}"; do
        systemctl reload-or-restart "$service"
    done
    
    log_success "Configuration reloaded"
}

show_help() {
    cat << EOF
Course Creator Platform Service Management

Usage: $0 {start|stop|restart|status|logs|reload|help}

Commands:
  start              Start all Course Creator services
  stop               Stop all Course Creator services  
  restart            Restart all Course Creator services
  status             Show status of all services
  logs [service]     Show logs for specific service or list available services
  reload             Reload configuration and restart services
  help               Show this help message

Examples:
  $0 status          # Show all service status
  $0 restart         # Restart all services
  $0 logs user-management    # Show logs for user management service
  $0 logs user-management -f # Follow logs in real-time

EOF
}

# Main command handling
case "${1:-help}" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs "$2"
        ;;
    reload)
        reload_config
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac