#!/bin/bash

###############################################################################
# Course Creator Platform - Webhook Setup Script
# 
# This script configures Git webhooks for automatic CI/CD pipeline triggering
###############################################################################

set -euo pipefail

# Configuration
JENKINS_URL="${JENKINS_URL:-http://localhost:8080}"
JENKINS_USER="${JENKINS_USER:-admin}"
JENKINS_PASSWORD="${JENKINS_PASSWORD:-admin}"
GITHUB_REPO="${GITHUB_REPO:-your-org/course-creator}"
GITHUB_TOKEN="${GITHUB_TOKEN:-}"
WEBHOOK_SECRET="${WEBHOOK_SECRET:-$(openssl rand -hex 20)}"

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

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check if Jenkins is running
    if ! curl -s "${JENKINS_URL}/api/json" > /dev/null; then
        error "Jenkins is not accessible at ${JENKINS_URL}"
    fi
    
    # Check if jq is installed
    if ! command -v jq &> /dev/null; then
        warn "jq is not installed. Installing..."
        sudo apt-get update && sudo apt-get install -y jq
    fi
    
    # Check if GitHub CLI is available
    if ! command -v gh &> /dev/null; then
        info "GitHub CLI not found. Install gh for easier GitHub integration."
    fi
    
    log "Prerequisites check completed"
}

# Configure Jenkins webhook settings
configure_jenkins_webhook() {
    log "Configuring Jenkins webhook settings..."
    
    # Download Jenkins CLI if not available
    if [ ! -f jenkins-cli.jar ]; then
        wget -O jenkins-cli.jar "${JENKINS_URL}/jnlpJars/jenkins-cli.jar"
    fi
    
    # Set Jenkins CLI alias
    alias jenkins-cli="java -jar jenkins-cli.jar -s ${JENKINS_URL} -auth ${JENKINS_USER}:${JENKINS_PASSWORD}"
    
    # Run webhook configuration script
    jenkins-cli groovy "$(dirname "$0")/webhook-config.groovy"
    
    log "Jenkins webhook configuration completed"
}

# Create webhook in GitHub repository
create_github_webhook() {
    log "Creating GitHub webhook..."
    
    if [ -z "$GITHUB_TOKEN" ]; then
        warn "GITHUB_TOKEN not set. Skipping automatic GitHub webhook creation."
        info "You'll need to create the webhook manually in GitHub."
        return 0
    fi
    
    local webhook_url="${JENKINS_URL}/github-webhook/"
    local webhook_payload='{
        "name": "web",
        "active": true,
        "events": [
            "push",
            "pull_request",
            "create",
            "delete"
        ],
        "config": {
            "url": "'${webhook_url}'",
            "content_type": "json",
            "secret": "'${WEBHOOK_SECRET}'",
            "insecure_ssl": "0"
        }
    }'
    
    # Create webhook using GitHub API
    local response=$(curl -s -X POST \
        -H "Authorization: token ${GITHUB_TOKEN}" \
        -H "Accept: application/vnd.github.v3+json" \
        -d "${webhook_payload}" \
        "https://api.github.com/repos/${GITHUB_REPO}/hooks")
    
    # Check if webhook was created successfully
    if echo "$response" | jq -e '.id' > /dev/null; then
        local webhook_id=$(echo "$response" | jq -r '.id')
        log "GitHub webhook created successfully (ID: ${webhook_id})"
        info "Webhook URL: ${webhook_url}"
    else
        local error_message=$(echo "$response" | jq -r '.message // "Unknown error"')
        error "Failed to create GitHub webhook: ${error_message}"
    fi
}

# Test webhook connectivity
test_webhook() {
    log "Testing webhook connectivity..."
    
    local webhook_url="${JENKINS_URL}/github-webhook/"
    
    # Test webhook endpoint accessibility
    local status_code=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${webhook_url}")
    
    if [ "$status_code" -eq 200 ] || [ "$status_code" -eq 302 ]; then
        log "Webhook endpoint is accessible (HTTP ${status_code})"
    else
        warn "Webhook endpoint returned HTTP ${status_code}"
        info "This might be normal if authentication is required"
    fi
    
    # Test Jenkins API accessibility
    if curl -s "${JENKINS_URL}/api/json" > /dev/null; then
        log "Jenkins API is accessible"
    else
        warn "Jenkins API is not accessible from external requests"
    fi
}

# Configure webhook for multiple Git providers
configure_multi_provider_webhooks() {
    log "Configuring webhooks for multiple Git providers..."
    
    # GitHub webhook (already configured above)
    info "GitHub webhook: ${JENKINS_URL}/github-webhook/"
    
    # GitLab webhook support
    info "GitLab webhook: ${JENKINS_URL}/project/course-creator-pipeline"
    
    # Generic Git webhook
    info "Generic Git webhook: ${JENKINS_URL}/git/notifyCommit?url=<git-repo-url>"
    
    # Bitbucket webhook
    info "Bitbucket webhook: ${JENKINS_URL}/bitbucket-hook/"
    
    log "Multi-provider webhook configuration completed"
}

# Generate webhook documentation
generate_webhook_docs() {
    log "Generating webhook documentation..."
    
    cat > webhook-setup-guide.md << EOF
# Git Webhook Setup Guide

## Overview
This guide explains how to set up Git webhooks for the Course Creator Platform CI/CD pipeline.

## Jenkins Webhook Endpoints

### GitHub Webhook
- **URL**: \`${JENKINS_URL}/github-webhook/\`
- **Content Type**: \`application/json\`
- **Secret**: \`${WEBHOOK_SECRET}\`
- **Events**: Push, Pull Request, Create, Delete

### GitLab Webhook
- **URL**: \`${JENKINS_URL}/project/course-creator-pipeline\`
- **Secret Token**: \`${WEBHOOK_SECRET}\`
- **Trigger**: Push events, Tag push events, Merge request events

### Generic Git Webhook
- **URL**: \`${JENKINS_URL}/git/notifyCommit?url=<git-repo-url>\`
- **Method**: GET or POST
- **Authentication**: Basic auth or API token

### Bitbucket Webhook
- **URL**: \`${JENKINS_URL}/bitbucket-hook/\`
- **Events**: Repository push

## Setup Instructions

### GitHub Setup
1. Go to your repository on GitHub
2. Navigate to Settings → Webhooks
3. Click "Add webhook"
4. Set Payload URL to: \`${JENKINS_URL}/github-webhook/\`
5. Set Content type to: \`application/json\`
6. Set Secret to: \`${WEBHOOK_SECRET}\`
7. Select "Just the push event" or customize events
8. Ensure "Active" is checked
9. Click "Add webhook"

### GitLab Setup
1. Go to your project on GitLab
2. Navigate to Settings → Webhooks
3. Set URL to: \`${JENKINS_URL}/project/course-creator-pipeline\`
4. Set Secret Token to: \`${WEBHOOK_SECRET}\`
5. Select trigger events (Push events, Tag push events, etc.)
6. Click "Add webhook"

### Testing Webhooks
1. Push a commit to your repository
2. Check Jenkins pipeline for automatic trigger
3. Monitor webhook delivery in your Git provider's interface
4. Check Jenkins logs for webhook reception

## Troubleshooting

### Common Issues
- **Webhook not triggering**: Check URL, secret, and network connectivity
- **403 Forbidden**: Verify Jenkins authentication and permissions
- **SSL errors**: Check certificate configuration or use \`insecure_ssl: 1\`
- **Timeout**: Ensure Jenkins is accessible from Git provider's servers

### Debug Commands
\`\`\`bash
# Test webhook endpoint
curl -X POST ${JENKINS_URL}/github-webhook/

# Check Jenkins logs
tail -f /var/log/jenkins/jenkins.log

# Test Git provider connectivity
curl -I https://api.github.com
\`\`\`

## Security Considerations
- Use webhook secrets to verify request authenticity
- Configure Jenkins firewall rules appropriately
- Use HTTPS in production environments
- Regularly rotate webhook secrets
- Monitor webhook activity logs

## Environment Variables
- \`JENKINS_URL\`: Jenkins server URL
- \`GITHUB_TOKEN\`: GitHub personal access token
- \`WEBHOOK_SECRET\`: Webhook secret for authentication
- \`GITHUB_REPO\`: Repository in format \`owner/repo\`

EOF

    log "Webhook documentation generated: webhook-setup-guide.md"
}

# Main setup function
main() {
    log "Starting Git webhook setup for Course Creator Platform..."
    
    # Export webhook secret for Jenkins configuration
    export WEBHOOK_SECRET
    export GITHUB_WEBHOOK_SECRET="$WEBHOOK_SECRET"
    
    check_prerequisites
    configure_jenkins_webhook
    configure_multi_provider_webhooks
    
    # Try to create GitHub webhook if token is provided
    if [ -n "$GITHUB_TOKEN" ]; then
        create_github_webhook
    fi
    
    test_webhook
    generate_webhook_docs
    
    log "Git webhook setup completed successfully!"
    
    echo ""
    echo "🎉 Setup Summary:"
    echo "=================="
    echo "Jenkins URL: ${JENKINS_URL}"
    echo "GitHub Webhook URL: ${JENKINS_URL}/github-webhook/"
    echo "Webhook Secret: ${WEBHOOK_SECRET}"
    echo "Documentation: webhook-setup-guide.md"
    echo ""
    echo "📋 Next Steps:"
    echo "1. Add webhook to your Git repository using the URLs above"
    echo "2. Test the webhook by pushing a commit"
    echo "3. Monitor Jenkins pipeline execution"
    echo "4. Review webhook-setup-guide.md for detailed instructions"
    
    if [ -z "$GITHUB_TOKEN" ]; then
        echo ""
        echo "⚠️  Manual GitHub Setup Required:"
        echo "Set GITHUB_TOKEN environment variable and re-run for automatic webhook creation"
    fi
}

# Handle script arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Options:"
        echo "  --help, -h     Show this help message"
        echo "  --test         Test existing webhook configuration"
        echo "  --docs         Generate documentation only"
        echo ""
        echo "Environment Variables:"
        echo "  JENKINS_URL    Jenkins server URL (default: http://localhost:8080)"
        echo "  JENKINS_USER   Jenkins username (default: admin)"
        echo "  JENKINS_PASSWORD Jenkins password (default: admin)"
        echo "  GITHUB_REPO    GitHub repository (format: owner/repo)"
        echo "  GITHUB_TOKEN   GitHub personal access token"
        echo "  WEBHOOK_SECRET Webhook secret (auto-generated if not set)"
        exit 0
        ;;
    --test)
        test_webhook
        exit 0
        ;;
    --docs)
        generate_webhook_docs
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac