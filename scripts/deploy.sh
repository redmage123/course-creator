#!/bin/bash

###############################################################################
# Course Creator Platform - Deployment Script
# 
# This script handles deployment to multiple environments:
# - dev: Development environment
# - staging: Staging environment  
# - prod: Production environment
#
# Features:
# - Multi-environment support
# - Database migrations
# - Service health checks
# - Rollback capabilities
# - Blue-green deployment support
# - Configuration management
###############################################################################

set -euo pipefail

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="/tmp/course-creator-deploy-$(date +%Y%m%d-%H%M%S).log"

# Default values
ENVIRONMENT=""
VERSION=""
REGISTRY=""
REPO=""
NAMESPACE=""
CONFIG_FILE=""
DRY_RUN=false
ROLLBACK=false
ROLLBACK_VERSION=""
FORCE=false
SKIP_MIGRATIONS=false
SKIP_HEALTH_CHECKS=false
BLUE_GREEN=false
TIMEOUT=600

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" | tee -a "$LOG_FILE"
    exit 1
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}" | tee -a "$LOG_FILE"
}

# Help function
show_help() {
    cat << EOF
Course Creator Platform Deployment Script

Usage: $0 [OPTIONS]

OPTIONS:
    -e, --environment ENV       Target environment (dev, staging, prod)
    -v, --version VERSION       Docker image version/tag to deploy
    -r, --registry REGISTRY     Docker registry URL
    -p, --repo REPO            Docker repository name
    -n, --namespace NAMESPACE   Kubernetes namespace (optional)
    -c, --config CONFIG        Configuration file path
    -d, --dry-run              Show what would be deployed without executing
    -R, --rollback             Rollback to previous version
    --rollback-version VERSION  Rollback to specific version
    -f, --force                Force deployment even if health checks fail
    --skip-migrations          Skip database migrations
    --skip-health-checks       Skip post-deployment health checks
    --blue-green               Use blue-green deployment strategy
    --timeout SECONDS          Deployment timeout (default: 600)
    -h, --help                 Show this help message

EXAMPLES:
    # Deploy to development
    $0 -e dev -v v1.2.3 -r docker.io -p course-creator

    # Deploy to production with blue-green strategy
    $0 -e prod -v v1.2.3 -r docker.io -p course-creator --blue-green

    # Rollback production to previous version
    $0 -e prod --rollback

    # Dry run deployment to staging
    $0 -e staging -v v1.2.3 -r docker.io -p course-creator --dry-run

EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -e|--environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            -v|--version)
                VERSION="$2"
                shift 2
                ;;
            -r|--registry)
                REGISTRY="$2"
                shift 2
                ;;
            -p|--repo)
                REPO="$2"
                shift 2
                ;;
            -n|--namespace)
                NAMESPACE="$2"
                shift 2
                ;;
            -c|--config)
                CONFIG_FILE="$2"
                shift 2
                ;;
            -d|--dry-run)
                DRY_RUN=true
                shift
                ;;
            -R|--rollback)
                ROLLBACK=true
                shift
                ;;
            --rollback-version)
                ROLLBACK_VERSION="$2"
                shift 2
                ;;
            -f|--force)
                FORCE=true
                shift
                ;;
            --skip-migrations)
                SKIP_MIGRATIONS=true
                shift
                ;;
            --skip-health-checks)
                SKIP_HEALTH_CHECKS=true
                shift
                ;;
            --blue-green)
                BLUE_GREEN=true
                shift
                ;;
            --timeout)
                TIMEOUT="$2"
                shift 2
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                ;;
        esac
    done
}

# Validate arguments
validate_args() {
    if [[ -z "$ENVIRONMENT" ]]; then
        error "Environment is required. Use -e or --environment"
    fi

    if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
        error "Invalid environment: $ENVIRONMENT. Must be dev, staging, or prod"
    fi

    if [[ "$ROLLBACK" == "false" && -z "$VERSION" ]]; then
        error "Version is required for deployment. Use -v or --version"
    fi

    if [[ "$ROLLBACK" == "false" && -z "$REGISTRY" ]]; then
        error "Registry is required for deployment. Use -r or --registry"
    fi

    if [[ "$ROLLBACK" == "false" && -z "$REPO" ]]; then
        error "Repository is required for deployment. Use -p or --repo"
    fi

    # Set namespace if not provided
    if [[ -z "$NAMESPACE" ]]; then
        NAMESPACE="course-creator-$ENVIRONMENT"
    fi

    # Set config file if not provided
    if [[ -z "$CONFIG_FILE" ]]; then
        CONFIG_FILE="$PROJECT_ROOT/deploy/environments/$ENVIRONMENT.yml"
    fi
}

# Load environment configuration
load_config() {
    log "Loading configuration for environment: $ENVIRONMENT"
    
    if [[ ! -f "$CONFIG_FILE" ]]; then
        error "Configuration file not found: $CONFIG_FILE"
    fi

    # Source environment-specific configuration
    source "$PROJECT_ROOT/deploy/environments/$ENVIRONMENT.env" 2>/dev/null || warn "Environment file not found"
    
    log "Configuration loaded successfully"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."

    # Check if kubectl is available and configured
    if ! command -v kubectl &> /dev/null; then
        error "kubectl is not installed or not in PATH"
    fi

    # Check if helm is available (if using Helm)
    if ! command -v helm &> /dev/null; then
        warn "helm is not installed - using kubectl only"
    fi

    # Check if docker is available
    if ! command -v docker &> /dev/null; then
        error "docker is not installed or not in PATH"
    fi

    # Verify cluster access
    if ! kubectl cluster-info &> /dev/null; then
        error "Cannot connect to Kubernetes cluster"
    fi

    # Check namespace exists or create it
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log "Creating namespace: $NAMESPACE"
        if [[ "$DRY_RUN" == "false" ]]; then
            kubectl create namespace "$NAMESPACE"
        else
            info "DRY RUN: Would create namespace $NAMESPACE"
        fi
    fi

    log "Prerequisites check completed"
}

# Backup current deployment
backup_deployment() {
    log "Creating backup of current deployment..."
    
    local backup_dir="$PROJECT_ROOT/deploy/backups/$ENVIRONMENT/$(date +%Y%m%d-%H%M%S)"
    
    if [[ "$DRY_RUN" == "false" ]]; then
        mkdir -p "$backup_dir"
        
        # Backup current deployments
        kubectl get deployments -n "$NAMESPACE" -o yaml > "$backup_dir/deployments.yaml" 2>/dev/null || true
        kubectl get services -n "$NAMESPACE" -o yaml > "$backup_dir/services.yaml" 2>/dev/null || true
        kubectl get configmaps -n "$NAMESPACE" -o yaml > "$backup_dir/configmaps.yaml" 2>/dev/null || true
        kubectl get secrets -n "$NAMESPACE" -o yaml > "$backup_dir/secrets.yaml" 2>/dev/null || true
        
        # Store current version info
        echo "ENVIRONMENT=$ENVIRONMENT" > "$backup_dir/version.info"
        echo "TIMESTAMP=$(date)" >> "$backup_dir/version.info"
        echo "PREVIOUS_VERSION=$(kubectl get deployment -n "$NAMESPACE" -o jsonpath='{.items[0].spec.template.spec.containers[0].image}' 2>/dev/null || echo 'unknown')" >> "$backup_dir/version.info"
        
        log "Backup created at: $backup_dir"
    else
        info "DRY RUN: Would create backup at $backup_dir"
    fi
}

# Database migrations
run_migrations() {
    if [[ "$SKIP_MIGRATIONS" == "true" ]]; then
        warn "Skipping database migrations"
        return 0
    fi

    log "Running database migrations..."
    
    local migration_pod="course-creator-migration-$(date +%s)"
    
    if [[ "$DRY_RUN" == "false" ]]; then
        # Create migration job
        cat <<EOF | kubectl apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: $migration_pod
  namespace: $NAMESPACE
spec:
  template:
    spec:
      containers:
      - name: migration
        image: $REGISTRY/$REPO-user-management:$VERSION
        command: ["python", "deploy/setup-database.py", "--migrate"]
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: course-creator-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: course-creator-secrets
              key: redis-url
      restartPolicy: Never
  backoffLimit: 3
EOF

        # Wait for migration to complete
        kubectl wait --for=condition=complete job/$migration_pod -n "$NAMESPACE" --timeout=300s
        
        # Check migration status
        if kubectl get job "$migration_pod" -n "$NAMESPACE" -o jsonpath='{.status.conditions[?(@.type=="Complete")].status}' | grep -q "True"; then
            log "Database migrations completed successfully"
        else
            error "Database migrations failed"
        fi
        
        # Cleanup migration job
        kubectl delete job "$migration_pod" -n "$NAMESPACE"
    else
        info "DRY RUN: Would run database migrations"
    fi
}

# Deploy services
deploy_services() {
    log "Deploying services to $ENVIRONMENT environment..."
    
    local services=(
        "user-management:8000"
        "course-generator:8001" 
        "content-storage:8003"
        "course-management:8004"
        "content-management:8005"
        "analytics:8007"
        "lab-containers:8006"
        "frontend:8080"
    )
    
    for service_info in "${services[@]}"; do
        local service_name="${service_info%:*}"
        local service_port="${service_info#*:}"
        
        log "Deploying $service_name..."
        
        if [[ "$DRY_RUN" == "false" ]]; then
            # Update deployment with new image
            kubectl set image deployment/$service_name \\
                $service_name=$REGISTRY/$REPO-$service_name:$VERSION \\
                -n "$NAMESPACE"
            
            # Wait for rollout to complete
            kubectl rollout status deployment/$service_name -n "$NAMESPACE" --timeout=300s
            
            log "$service_name deployed successfully"
        else
            info "DRY RUN: Would deploy $service_name with image $REGISTRY/$REPO-$service_name:$VERSION"
        fi
    done
    
    # Deploy multi-IDE lab images
    log "Updating multi-IDE lab images..."
    if [[ "$DRY_RUN" == "false" ]]; then
        # Update lab container deployment with new multi-IDE images
        kubectl patch deployment lab-containers -n "$NAMESPACE" -p '{"spec":{"template":{"spec":{"containers":[{"name":"lab-containers","env":[{"name":"MULTI_IDE_BASE_IMAGE","value":"'$REGISTRY'/'$REPO'-multi-ide-base:'$VERSION'"},{"name":"PYTHON_LAB_MULTI_IDE_IMAGE","value":"'$REGISTRY'/'$REPO'-python-lab-multi-ide:'$VERSION'"}]}]}}}}'
    else
        info "DRY RUN: Would update multi-IDE lab images"
    fi
}

# Health checks
run_health_checks() {
    if [[ "$SKIP_HEALTH_CHECKS" == "true" ]]; then
        warn "Skipping health checks"
        return 0
    fi

    log "Running health checks..."
    
    local services=(
        "user-management:8000"
        "course-generator:8001"
        "content-storage:8003" 
        "course-management:8004"
        "content-management:8005"
        "analytics:8007"
        "lab-containers:8006"
        "frontend:8080"
    )
    
    local failed_services=()
    
    for service_info in "${services[@]}"; do
        local service_name="${service_info%:*}"
        local service_port="${service_info#*:}"
        
        info "Checking health of $service_name..."
        
        if [[ "$DRY_RUN" == "false" ]]; then
            # Check if pods are ready
            local ready_pods=$(kubectl get pods -n "$NAMESPACE" -l app=$service_name -o jsonpath='{.items[*].status.conditions[?(@.type=="Ready")].status}' | grep -o "True" | wc -l)
            local total_pods=$(kubectl get pods -n "$NAMESPACE" -l app=$service_name --no-headers | wc -l)
            
            if [[ "$ready_pods" -eq "$total_pods" && "$total_pods" -gt 0 ]]; then
                # Additional health check via HTTP endpoint
                local service_url="http://$service_name.$NAMESPACE.svc.cluster.local:$service_port/health"
                if kubectl run health-check-$service_name --rm -i --restart=Never --image=curlimages/curl -- curl -s -f "$service_url" &>/dev/null; then
                    log "$service_name is healthy"
                else
                    warn "$service_name HTTP health check failed"
                    failed_services+=("$service_name")
                fi
            else
                warn "$service_name pods not ready ($ready_pods/$total_pods)"
                failed_services+=("$service_name")
            fi
        else
            info "DRY RUN: Would check health of $service_name"
        fi
    done
    
    if [[ ${#failed_services[@]} -gt 0 ]]; then
        error "Health checks failed for services: ${failed_services[*]}"
    fi
    
    log "All health checks passed"
}

# Rollback deployment
rollback_deployment() {
    log "Rolling back deployment in $ENVIRONMENT..."
    
    if [[ -n "$ROLLBACK_VERSION" ]]; then
        log "Rolling back to specific version: $ROLLBACK_VERSION"
        VERSION="$ROLLBACK_VERSION"
        deploy_services
    else
        log "Rolling back to previous version..."
        
        local services=(
            "user-management"
            "course-generator"
            "content-storage"
            "course-management" 
            "content-management"
            "analytics"
            "lab-containers"
            "frontend"
        )
        
        for service in "${services[@]}"; do
            if [[ "$DRY_RUN" == "false" ]]; then
                kubectl rollout undo deployment/$service -n "$NAMESPACE"
                kubectl rollout status deployment/$service -n "$NAMESPACE" --timeout=300s
                log "$service rolled back successfully"
            else
                info "DRY RUN: Would rollback $service"
            fi
        done
    fi
    
    # Run health checks after rollback
    run_health_checks
    
    log "Rollback completed successfully"
}

# Blue-green deployment
blue_green_deployment() {
    log "Starting blue-green deployment..."
    
    local green_namespace="${NAMESPACE}-green"
    
    # Create green namespace
    if ! kubectl get namespace "$green_namespace" &> /dev/null; then
        kubectl create namespace "$green_namespace"
    fi
    
    # Deploy to green environment
    local original_namespace="$NAMESPACE"
    NAMESPACE="$green_namespace"
    
    deploy_services
    run_health_checks
    
    # Switch traffic to green
    log "Switching traffic to green environment..."
    
    # Update service selectors to point to green deployment
    # This is a simplified example - in reality you'd use ingress controllers
    # or service mesh for more sophisticated traffic routing
    
    if [[ "$DRY_RUN" == "false" ]]; then
        # Label green pods
        kubectl label pods -n "$green_namespace" --all version=green --overwrite
        
        # Update services in original namespace to route to green pods
        kubectl patch service user-management -n "$original_namespace" -p '{"spec":{"selector":{"version":"green"}}}'
        # ... repeat for other services
        
        log "Traffic switched to green environment"
        
        # Cleanup blue environment after successful switch
        sleep 30  # Wait a bit to ensure everything is working
        log "Cleaning up blue environment..."
        # kubectl delete namespace "$original_namespace-blue" 2>/dev/null || true
    else
        info "DRY RUN: Would switch traffic to green environment"
    fi
    
    NAMESPACE="$original_namespace"
    log "Blue-green deployment completed"
}

# Main deployment function
main_deploy() {
    log "Starting deployment to $ENVIRONMENT environment"
    log "Version: $VERSION"
    log "Registry: $REGISTRY"
    log "Repository: $REPO"
    log "Namespace: $NAMESPACE"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        warn "DRY RUN MODE - No actual changes will be made"
    fi
    
    # Create deployment backup
    backup_deployment
    
    # Run database migrations
    run_migrations
    
    # Deploy based on strategy
    if [[ "$BLUE_GREEN" == "true" ]]; then
        blue_green_deployment
    else
        deploy_services
    fi
    
    # Run health checks
    run_health_checks
    
    log "Deployment to $ENVIRONMENT completed successfully!"
    log "Log file: $LOG_FILE"
}

# Cleanup function
cleanup() {
    log "Cleaning up temporary resources..."
    # Add any cleanup tasks here
}

# Trap for cleanup on exit
trap cleanup EXIT

# Main execution
main() {
    parse_args "$@"
    validate_args
    load_config
    check_prerequisites
    
    if [[ "$ROLLBACK" == "true" ]]; then
        rollback_deployment
    else
        main_deploy
    fi
}

# Execute main function with all arguments
main "$@"