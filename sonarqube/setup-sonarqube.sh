#!/bin/bash

###############################################################################
# Course Creator Platform - SonarQube Setup Script
# 
# This script sets up SonarQube with custom quality profiles and gates
# for the Course Creator platform
###############################################################################

set -euo pipefail

# Configuration
SONAR_URL="${SONAR_URL:-http://localhost:9000}"
SONAR_USER="${SONAR_USER:-admin}"
SONAR_PASSWORD="${SONAR_PASSWORD:-admin}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Check if SonarQube is running
check_sonar_server() {
    log "Checking SonarQube server availability..."
    
    local retries=30
    local count=0
    
    while [ $count -lt $retries ]; do
        if curl -s -f "${SONAR_URL}/api/system/status" > /dev/null; then
            log "SonarQube server is running"
            return 0
        fi
        
        info "Waiting for SonarQube server... ($((count + 1))/$retries)"
        sleep 10
        count=$((count + 1))
    done
    
    error "SonarQube server is not available at ${SONAR_URL}"
}

# Wait for SonarQube to be ready
wait_for_sonar() {
    log "Waiting for SonarQube to be fully ready..."
    
    local retries=60
    local count=0
    
    while [ $count -lt $retries ]; do
        local status=$(curl -s -u "${SONAR_USER}:${SONAR_PASSWORD}" \
            "${SONAR_URL}/api/system/status" | \
            grep -o '"status":"[^"]*"' | cut -d'"' -f4)
        
        if [ "$status" = "UP" ]; then
            log "SonarQube is ready"
            return 0
        fi
        
        info "SonarQube status: $status. Waiting... ($((count + 1))/$retries)"
        sleep 5
        count=$((count + 1))
    done
    
    error "SonarQube failed to become ready"
}

# Create SonarQube project
create_project() {
    log "Creating Course Creator project in SonarQube..."
    
    # Check if project already exists
    local project_exists=$(curl -s -u "${SONAR_USER}:${SONAR_PASSWORD}" \
        "${SONAR_URL}/api/projects/search?projects=course-creator" | \
        grep -o '"total":[0-9]*' | cut -d':' -f2)
    
    if [ "$project_exists" -gt 0 ]; then
        warn "Project already exists, skipping creation"
        return 0
    fi
    
    # Create the project
    curl -X POST -u "${SONAR_USER}:${SONAR_PASSWORD}" \
        "${SONAR_URL}/api/projects/create" \
        -d "project=course-creator" \
        -d "name=Course Creator Platform" \
        -d "visibility=private" || error "Failed to create project"
    
    log "Project created successfully"
}

# Import quality profiles
import_quality_profiles() {
    log "Importing custom quality profiles..."
    
    # Import Python profile
    if [ -f "$SCRIPT_DIR/quality-profiles/python-profile.xml" ]; then
        info "Importing Python quality profile..."
        curl -X POST -u "${SONAR_USER}:${SONAR_PASSWORD}" \
            "${SONAR_URL}/api/qualityprofiles/restore" \
            -F "backup=@$SCRIPT_DIR/quality-profiles/python-profile.xml" || \
            warn "Failed to import Python quality profile"
    fi
    
    # Import JavaScript profile
    if [ -f "$SCRIPT_DIR/quality-profiles/javascript-profile.xml" ]; then
        info "Importing JavaScript quality profile..."
        curl -X POST -u "${SONAR_USER}:${SONAR_PASSWORD}" \
            "${SONAR_URL}/api/qualityprofiles/restore" \
            -F "backup=@$SCRIPT_DIR/quality-profiles/javascript-profile.xml" || \
            warn "Failed to import JavaScript quality profile"
    fi
    
    log "Quality profiles imported"
}

# Create quality gate
create_quality_gate() {
    log "Creating Course Creator quality gate..."
    
    # Check if quality gate exists
    local gate_exists=$(curl -s -u "${SONAR_USER}:${SONAR_PASSWORD}" \
        "${SONAR_URL}/api/qualitygates/list" | \
        grep -o '"name":"Course Creator Quality Gate"' | wc -l)
    
    if [ "$gate_exists" -gt 0 ]; then
        warn "Quality gate already exists, skipping creation"
        return 0
    fi
    
    # Create quality gate
    local gate_id=$(curl -X POST -u "${SONAR_USER}:${SONAR_PASSWORD}" \
        "${SONAR_URL}/api/qualitygates/create" \
        -d "name=Course Creator Quality Gate" | \
        grep -o '"id":[0-9]*' | cut -d':' -f2)
    
    if [ -z "$gate_id" ]; then
        error "Failed to create quality gate"
    fi
    
    info "Created quality gate with ID: $gate_id"
    
    # Add conditions to quality gate
    add_quality_gate_conditions "$gate_id"
    
    log "Quality gate created successfully"
}

# Add conditions to quality gate
add_quality_gate_conditions() {
    local gate_id="$1"
    
    info "Adding conditions to quality gate..."
    
    # Coverage conditions
    curl -X POST -u "${SONAR_USER}:${SONAR_PASSWORD}" \
        "${SONAR_URL}/api/qualitygates/create_condition" \
        -d "gateId=$gate_id" \
        -d "metric=new_coverage" \
        -d "op=LT" \
        -d "error=75" > /dev/null
    
    curl -X POST -u "${SONAR_USER}:${SONAR_PASSWORD}" \
        "${SONAR_URL}/api/qualitygates/create_condition" \
        -d "gateId=$gate_id" \
        -d "metric=coverage" \
        -d "op=LT" \
        -d "error=70" > /dev/null
    
    # Security conditions
    curl -X POST -u "${SONAR_USER}:${SONAR_PASSWORD}" \
        "${SONAR_URL}/api/qualitygates/create_condition" \
        -d "gateId=$gate_id" \
        -d "metric=new_vulnerabilities" \
        -d "op=GT" \
        -d "error=0" > /dev/null
    
    curl -X POST -u "${SONAR_USER}:${SONAR_PASSWORD}" \
        "${SONAR_URL}/api/qualitygates/create_condition" \
        -d "gateId=$gate_id" \
        -d "metric=new_security_hotspots_reviewed" \
        -d "op=LT" \
        -d "error=100" > /dev/null
    
    # Bug conditions
    curl -X POST -u "${SONAR_USER}:${SONAR_PASSWORD}" \
        "${SONAR_URL}/api/qualitygates/create_condition" \
        -d "gateId=$gate_id" \
        -d "metric=new_bugs" \
        -d "op=GT" \
        -d "error=0" > /dev/null
    
    # Code smell conditions
    curl -X POST -u "${SONAR_USER}:${SONAR_PASSWORD}" \
        "${SONAR_URL}/api/qualitygates/create_condition" \
        -d "gateId=$gate_id" \
        -d "metric=new_code_smells" \
        -d "op=GT" \
        -d "error=10" > /dev/null
    
    # Technical debt conditions
    curl -X POST -u "${SONAR_USER}:${SONAR_PASSWORD}" \
        "${SONAR_URL}/api/qualitygates/create_condition" \
        -d "gateId=$gate_id" \
        -d "metric=new_technical_debt" \
        -d "op=GT" \
        -d "error=16h" > /dev/null
    
    # Maintainability rating conditions
    curl -X POST -u "${SONAR_USER}:${SONAR_PASSWORD}" \
        "${SONAR_URL}/api/qualitygates/create_condition" \
        -d "gateId=$gate_id" \
        -d "metric=new_maintainability_rating" \
        -d "op=GT" \
        -d "error=1" > /dev/null
    
    # Reliability rating conditions
    curl -X POST -u "${SONAR_USER}:${SONAR_PASSWORD}" \
        "${SONAR_URL}/api/qualitygates/create_condition" \
        -d "gateId=$gate_id" \
        -d "metric=new_reliability_rating" \
        -d "op=GT" \
        -d "error=1" > /dev/null
    
    # Security rating conditions
    curl -X POST -u "${SONAR_USER}:${SONAR_PASSWORD}" \
        "${SONAR_URL}/api/qualitygates/create_condition" \
        -d "gateId=$gate_id" \
        -d "metric=new_security_rating" \
        -d "op=GT" \
        -d "error=1" > /dev/null
    
    # Duplication conditions
    curl -X POST -u "${SONAR_USER}:${SONAR_PASSWORD}" \
        "${SONAR_URL}/api/qualitygates/create_condition" \
        -d "gateId=$gate_id" \
        -d "metric=new_duplicated_lines_density" \
        -d "op=GT" \
        -d "error=5" > /dev/null
    
    info "Quality gate conditions added"
}

# Associate project with quality profiles and gate
configure_project() {
    log "Configuring project settings..."
    
    # Set quality profiles for the project
    info "Setting Python quality profile..."
    curl -X POST -u "${SONAR_USER}:${SONAR_PASSWORD}" \
        "${SONAR_URL}/api/qualityprofiles/add_project" \
        -d "project=course-creator" \
        -d "qualityProfile=Course Creator Python Profile" \
        -d "language=py" > /dev/null || warn "Failed to set Python quality profile"
    
    info "Setting JavaScript quality profile..."
    curl -X POST -u "${SONAR_USER}:${SONAR_PASSWORD}" \
        "${SONAR_URL}/api/qualityprofiles/add_project" \
        -d "project=course-creator" \
        -d "qualityProfile=Course Creator JavaScript Profile" \
        -d "language=js" > /dev/null || warn "Failed to set JavaScript quality profile"
    
    # Associate project with quality gate
    info "Setting quality gate..."
    curl -X POST -u "${SONAR_USER}:${SONAR_PASSWORD}" \
        "${SONAR_URL}/api/qualitygates/select" \
        -d "projectKey=course-creator" \
        -d "gateName=Course Creator Quality Gate" > /dev/null || \
        warn "Failed to set quality gate"
    
    log "Project configuration completed"
}

# Configure webhooks for Jenkins integration
configure_webhooks() {
    log "Configuring webhooks for Jenkins integration..."
    
    # Check if webhook already exists
    local webhook_exists=$(curl -s -u "${SONAR_USER}:${SONAR_PASSWORD}" \
        "${SONAR_URL}/api/webhooks/list?project=course-creator" | \
        grep -o '"name":"Jenkins Webhook"' | wc -l)
    
    if [ "$webhook_exists" -gt 0 ]; then
        warn "Jenkins webhook already exists, skipping creation"
        return 0
    fi
    
    # Create webhook for Jenkins
    curl -X POST -u "${SONAR_USER}:${SONAR_PASSWORD}" \
        "${SONAR_URL}/api/webhooks/create" \
        -d "project=course-creator" \
        -d "name=Jenkins Webhook" \
        -d "url=http://jenkins:8080/sonarqube-webhook/" > /dev/null || \
        warn "Failed to create Jenkins webhook"
    
    log "Webhook configuration completed"
}

# Setup analysis exclusions
configure_exclusions() {
    log "Configuring analysis exclusions..."
    
    # Set exclusion patterns
    curl -X POST -u "${SONAR_USER}:${SONAR_PASSWORD}" \
        "${SONAR_URL}/api/settings/set" \
        -d "component=course-creator" \
        -d "key=sonar.exclusions" \
        -d "value=**/*_test.py,**/tests/**,**/test_*.py,**/*.min.js,**/node_modules/**,**/vendor/**,**/migrations/**,**/__pycache__/**,**/venv/**,**/env/**,**/.pytest_cache/**,**/coverage/**,**/htmlcov/**,**/dist/**,**/build/**" > /dev/null
    
    # Set test inclusion patterns
    curl -X POST -u "${SONAR_USER}:${SONAR_PASSWORD}" \
        "${SONAR_URL}/api/settings/set" \
        -d "component=course-creator" \
        -d "key=sonar.test.inclusions" \
        -d "value=**/*_test.py,**/tests/**,**/test_*.py,**/*.test.js,**/*.spec.js" > /dev/null
    
    # Set coverage exclusions
    curl -X POST -u "${SONAR_USER}:${SONAR_PASSWORD}" \
        "${SONAR_URL}/api/settings/set" \
        -d "component=course-creator" \
        -d "key=sonar.coverage.exclusions" \
        -d "value=**/*_test.py,**/tests/**,**/test_*.py,**/*.test.js,**/*.spec.js,**/migrations/**,**/manage.py,**/wsgi.py,**/asgi.py,**/settings/**,**/config/**" > /dev/null
    
    log "Exclusions configured"
}

# Generate authentication token
generate_token() {
    log "Generating authentication token for Jenkins..."
    
    # Generate token
    local token=$(curl -X POST -u "${SONAR_USER}:${SONAR_PASSWORD}" \
        "${SONAR_URL}/api/user_tokens/generate" \
        -d "name=jenkins-token" | \
        grep -o '"token":"[^"]*"' | cut -d'"' -f4)
    
    if [ -n "$token" ]; then
        info "Generated token: $token"
        echo "SONAR_TOKEN=$token" > "$SCRIPT_DIR/sonar-token.env"
        log "Token saved to sonar-token.env"
    else
        warn "Failed to generate token"
    fi
}

# Install SonarQube plugins (if needed)
install_plugins() {
    log "Installing SonarQube plugins..."
    
    # List of plugins to install
    local plugins=(
        "python"
        "javascript"
        "typescript"
        "html"
        "css"
        "json"
        "yaml"
        "docker"
        "secrets"
        "security"
    )
    
    for plugin in "${plugins[@]}"; do
        info "Checking plugin: $plugin"
        
        # Check if plugin is installed
        local installed=$(curl -s -u "${SONAR_USER}:${SONAR_PASSWORD}" \
            "${SONAR_URL}/api/plugins/installed" | \
            grep -o "\"key\":\"$plugin\"" | wc -l)
        
        if [ "$installed" -eq 0 ]; then
            info "Installing plugin: $plugin"
            curl -X POST -u "${SONAR_USER}:${SONAR_PASSWORD}" \
                "${SONAR_URL}/api/plugins/install" \
                -d "key=$plugin" > /dev/null || warn "Failed to install plugin: $plugin"
        else
            info "Plugin $plugin is already installed"
        fi
    done
    
    log "Plugin installation completed"
}

# Validate setup
validate_setup() {
    log "Validating SonarQube setup..."
    
    # Check project exists
    local project_count=$(curl -s -u "${SONAR_USER}:${SONAR_PASSWORD}" \
        "${SONAR_URL}/api/projects/search?projects=course-creator" | \
        grep -o '"total":[0-9]*' | cut -d':' -f2)
    
    if [ "$project_count" -eq 0 ]; then
        error "Project validation failed"
    fi
    
    # Check quality gate exists
    local gate_exists=$(curl -s -u "${SONAR_USER}:${SONAR_PASSWORD}" \
        "${SONAR_URL}/api/qualitygates/list" | \
        grep -o '"name":"Course Creator Quality Gate"' | wc -l)
    
    if [ "$gate_exists" -eq 0 ]; then
        error "Quality gate validation failed"
    fi
    
    log "Setup validation passed"
}

# Main setup function
main() {
    log "Starting SonarQube setup for Course Creator Platform..."
    
    check_sonar_server
    wait_for_sonar
    install_plugins
    create_project
    import_quality_profiles
    create_quality_gate
    configure_project
    configure_webhooks
    configure_exclusions
    generate_token
    validate_setup
    
    log "SonarQube setup completed successfully!"
    log "SonarQube URL: ${SONAR_URL}"
    log "Project: course-creator"
    log "Quality Gate: Course Creator Quality Gate"
    
    info "Next steps:"
    info "1. Update Jenkins credentials with the generated token"
    info "2. Configure SonarQube server URL in Jenkins"
    info "3. Run the Jenkins pipeline to test integration"
    info "4. Review quality profiles and gates in SonarQube UI"
    info "5. Set up email notifications in SonarQube"
}

# Execute main function
main "$@"