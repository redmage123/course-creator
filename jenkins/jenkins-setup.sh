#!/bin/bash

###############################################################################
# Course Creator Platform - Jenkins Setup Script
# 
# This script sets up Jenkins with all required plugins and configurations
# for the Course Creator CI/CD pipeline
###############################################################################

set -euo pipefail

# Configuration
JENKINS_URL="${JENKINS_URL:-http://localhost:8080}"
JENKINS_USER="${JENKINS_USER:-admin}"
JENKINS_PASSWORD="${JENKINS_PASSWORD:-admin}"
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

# Check if Jenkins CLI is available
check_jenkins_cli() {
    log "Checking Jenkins CLI availability..."
    
    if ! command -v jenkins-cli &> /dev/null; then
        info "Downloading Jenkins CLI..."
        wget -O jenkins-cli.jar "${JENKINS_URL}/jnlpJars/jenkins-cli.jar"
        alias jenkins-cli="java -jar jenkins-cli.jar -s ${JENKINS_URL} -auth ${JENKINS_USER}:${JENKINS_PASSWORD}"
    fi
}

# Install required Jenkins plugins
install_plugins() {
    log "Installing required Jenkins plugins..."
    
    local plugins=(
        "workflow-aggregator"           # Pipeline plugin
        "pipeline-stage-view"           # Pipeline stage view
        "blueocean"                     # Blue Ocean UI
        "docker-plugin"                 # Docker plugin
        "docker-workflow"               # Docker Pipeline plugin
        "kubernetes"                    # Kubernetes plugin
        "sonar"                         # SonarQube plugin
        "build-timeout"                 # Build timeout plugin
        "timestamper"                   # Timestamps plugin
        "ws-cleanup"                    # Workspace cleanup
        "ant"                           # Ant plugin
        "gradle"                        # Gradle plugin
        "workflow-support"              # Pipeline support
        "pipeline-milestone-step"       # Pipeline milestone step
        "pipeline-input-step"           # Pipeline input step
        "pipeline-stage-step"           # Pipeline stage step
        "github"                        # GitHub plugin
        "github-branch-source"          # GitHub branch source
        "git"                           # Git plugin
        "ssh-slaves"                    # SSH slaves plugin
        "matrix-auth"                   # Matrix authorization
        "pam-auth"                      # PAM authentication
        "ldap"                          # LDAP plugin
        "email-ext"                     # Extended email
        "mailer"                        # Mailer plugin
        "slack"                         # Slack notifications
        "junit"                         # JUnit plugin
        "jacoco"                        # JaCoCo code coverage
        "cobertura"                     # Cobertura coverage
        "htmlpublisher"                 # HTML Publisher
        "publish-over-ssh"              # Publish over SSH
        "credentials"                   # Credentials plugin
        "credentials-binding"           # Credentials binding
        "plain-credentials"             # Plain credentials
        "ssh-credentials"               # SSH credentials
        "docker-commons"                # Docker commons
        "docker-build-step"             # Docker build step
        "lockable-resources"            # Lockable resources
        "build-name-setter"             # Build name setter
        "build-user-vars-plugin"        # Build user vars
        "ansicolor"                     # ANSI color
        "xvfb"                          # Xvfb plugin
        "parameterized-trigger"         # Parameterized trigger
        "rebuild"                       # Rebuild plugin
        "copyartifact"                  # Copy artifact
        "join"                          # Join plugin
        "conditional-buildstep"         # Conditional build step
        "run-condition"                 # Run condition
        "flexible-publish"              # Flexible publish
        "build-pipeline-plugin"         # Build pipeline
        "dashboard-view"                # Dashboard view
        "view-job-filters"              # View job filters
        "nested-view"                   # Nested view
        "sectioned-view"                # Sectioned view
        "extra-columns"                 # Extra columns
        "compact-columns"               # Compact columns
        "console-column-plugin"         # Console column
        "all-changes"                   # All changes
        "favorite"                      # Favorite plugin
        "cloudbees-folder"              # CloudBees folder
        "antisamy-markup-formatter"     # AntiSamy markup formatter
        "build-blocker-plugin"          # Build blocker
        "config-file-provider"          # Config file provider
        "external-monitor-job"          # External monitor job
        "icon-shim"                     # Icon shim
        "javadoc"                       # Javadoc plugin
        "maven-plugin"                  # Maven plugin
        "monitoring"                    # Monitoring plugin
        "resource-disposer"             # Resource disposer
        "subversion"                    # Subversion plugin
        "ssh-agent"                     # SSH agent
        "windows-slaves"                # Windows slaves
        "workflow-basic-steps"          # Workflow basic steps
        "workflow-cps"                  # Workflow CPS
        "workflow-cps-global-lib"       # Workflow CPS global lib
        "workflow-durable-task-step"    # Workflow durable task step
        "workflow-job"                  # Workflow job
        "workflow-multibranch"          # Workflow multibranch
        "workflow-scm-step"             # Workflow SCM step
        "workflow-step-api"             # Workflow step API
    )
    
    for plugin in "${plugins[@]}"; do
        info "Installing plugin: $plugin"
        jenkins-cli install-plugin "$plugin" || warn "Failed to install plugin: $plugin"
    done
    
    log "Restarting Jenkins to activate plugins..."
    jenkins-cli restart
    
    # Wait for Jenkins to come back online
    sleep 60
    while ! curl -s "${JENKINS_URL}/api/json" > /dev/null; do
        info "Waiting for Jenkins to restart..."
        sleep 10
    done
}

# Configure Jenkins security
configure_security() {
    log "Configuring Jenkins security..."
    
    # Configure security realm and authorization strategy
    cat > security-config.groovy << 'EOF'
import jenkins.model.*
import hudson.security.*
import hudson.security.csrf.DefaultCrumbIssuer
import jenkins.security.s2m.AdminWhitelistRule

def instance = Jenkins.getInstance()

// Enable CSRF protection
instance.setCrumbIssuer(new DefaultCrumbIssuer(true))

// Configure security realm (local database)
def hudsonRealm = new HudsonPrivateSecurityRealm(false)
hudsonRealm.createAccount('admin', 'admin')
instance.setSecurityRealm(hudsonRealm)

// Configure authorization strategy (matrix-based)
def strategy = new GlobalMatrixAuthorizationStrategy()
strategy.add(Jenkins.ADMINISTER, 'admin')
strategy.add(Jenkins.READ, 'authenticated')
instance.setAuthorizationStrategy(strategy)

// Configure slave-to-master security
instance.getInjector().getInstance(AdminWhitelistRule.class).setMasterKillSwitch(false)

instance.save()
EOF

    jenkins-cli groovy security-config.groovy
    rm security-config.groovy
}

# Configure SonarQube integration
configure_sonarqube() {
    log "Configuring SonarQube integration..."
    
    cat > sonarqube-config.groovy << 'EOF'
import jenkins.model.*
import hudson.plugins.sonar.*
import hudson.plugins.sonar.model.TriggersConfig

def instance = Jenkins.getInstance()
def sonarDescriptor = instance.getDescriptor(SonarGlobalConfiguration.class)

// Configure SonarQube server
def sonarInstallation = new SonarInstallation(
    "SonarQube",                    // Name
    "http://localhost:9000",         // Server URL
    "sonar-auth-token",             // Server authentication token credential ID
    "",                             // Additional analysis properties
    "",                             // Additional command line arguments
    new TriggersConfig(),           // Triggers configuration
    "",                             // SonarQube Scanner for MSBuild version
    "",                             // Additional analysis properties for MSBuild
    ""                              // Database URL (if needed)
)

sonarDescriptor.setInstallations(sonarInstallation)
sonarDescriptor.setBuildWrapperEnabled(true)
sonarDescriptor.save()

println "SonarQube configuration completed"
EOF

    jenkins-cli groovy sonarqube-config.groovy
    rm sonarqube-config.groovy
}

# Configure Docker integration
configure_docker() {
    log "Configuring Docker integration..."
    
    cat > docker-config.groovy << 'EOF'
import jenkins.model.*
import com.nirima.jenkins.plugins.docker.*
import com.nirima.jenkins.plugins.docker.launcher.*

def instance = Jenkins.getInstance()

// Configure Docker cloud
def dockerCloud = new DockerCloud(
    "docker",                       // Name
    [                               // Docker templates
        new DockerTemplate(
            "course-creator-agent",  // Image
            "docker",               // Docker Cloud name
            "",                     // Label string
            "",                     // Remote FS root
            "22",                   // Instance cap string
            new DockerComputerSSHLauncher(
                "", "", "", "", "", "", "", ""
            )
        )
    ],
    "unix:///var/run/docker.sock", // Server URL
    100,                            // Container cap
    10,                             // Connect timeout
    10,                             // Read timeout
    "",                             // Credentials ID
    "",                             // Version
    ""                              // API version
)

instance.clouds.add(dockerCloud)
instance.save()

println "Docker configuration completed"
EOF

    jenkins-cli groovy docker-config.groovy
    rm docker-config.groovy
}

# Configure credentials
configure_credentials() {
    log "Configuring Jenkins credentials..."
    
    # Docker registry credentials
    cat > docker-credentials.xml << 'EOF'
<com.cloudbees.plugins.credentials.impl.UsernamePasswordCredentialsImpl>
  <scope>GLOBAL</scope>
  <id>docker-registry-credentials</id>
  <description>Docker Registry Credentials</description>
  <username>docker-user</username>
  <password>docker-password</password>
</com.cloudbees.plugins.credentials.impl.UsernamePasswordCredentialsImpl>
EOF

    jenkins-cli create-credentials-by-xml system::system::jenkins < docker-credentials.xml
    rm docker-credentials.xml

    # GitHub credentials
    cat > github-credentials.xml << 'EOF'
<com.cloudbees.plugins.credentials.impl.UsernamePasswordCredentialsImpl>
  <scope>GLOBAL</scope>
  <id>github-credentials</id>
  <description>GitHub Credentials</description>
  <username>github-user</username>
  <password>github-token</password>
</com.cloudbees.plugins.credentials.impl.UsernamePasswordCredentialsImpl>
EOF

    jenkins-cli create-credentials-by-xml system::system::jenkins < github-credentials.xml
    rm github-credentials.xml

    # SonarQube token
    cat > sonar-credentials.xml << 'EOF'
<org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl>
  <scope>GLOBAL</scope>
  <id>sonar-auth-token</id>
  <description>SonarQube Authentication Token</description>
  <secret>your-sonarqube-token</secret>
</org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl>
EOF

    jenkins-cli create-credentials-by-xml system::system::jenkins < sonar-credentials.xml
    rm sonar-credentials.xml

    # JWT secret key
    cat > jwt-credentials.xml << 'EOF'
<org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl>
  <scope>GLOBAL</scope>
  <id>jwt-secret-key</id>
  <description>JWT Secret Key</description>
  <secret>your-jwt-secret-key</secret>
</org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl>
EOF

    jenkins-cli create-credentials-by-xml system::system::jenkins < jwt-credentials.xml
    rm jwt-credentials.xml

    # API keys
    cat > anthropic-credentials.xml << 'EOF'
<org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl>
  <scope>GLOBAL</scope>
  <id>anthropic-api-key</id>
  <description>Anthropic API Key</description>
  <secret>your-anthropic-api-key</secret>
</org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl>
EOF

    jenkins-cli create-credentials-by-xml system::system::jenkins < anthropic-credentials.xml
    rm anthropic-credentials.xml

    cat > openai-credentials.xml << 'EOF'
<org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl>
  <scope>GLOBAL</scope>
  <id>openai-api-key</id>
  <description>OpenAI API Key</description>
  <secret>your-openai-api-key</secret>
</org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl>
EOF

    jenkins-cli create-credentials-by-xml system::system::jenkins < openai-credentials.xml
    rm openai-credentials.xml

    # Database credentials
    cat > postgres-credentials.xml << 'EOF'
<org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl>
  <scope>GLOBAL</scope>
  <id>postgres-credentials</id>
  <description>PostgreSQL Database Credentials</description>
  <secret>postgresql://user:password@localhost:5432/course_creator</secret>
</org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl>
EOF

    jenkins-cli create-credentials-by-xml system::system::jenkins < postgres-credentials.xml
    rm postgres-credentials.xml
}

# Create the main pipeline job
create_pipeline_job() {
    log "Creating Course Creator pipeline job..."
    
    jenkins-cli create-job "course-creator-pipeline" < "$SCRIPT_DIR/job-config.xml"
    
    log "Pipeline job created successfully"
}

# Configure global tools
configure_global_tools() {
    log "Configuring global tools..."
    
    cat > tools-config.groovy << 'EOF'
import jenkins.model.*
import hudson.tools.*
import hudson.plugins.sonar.*
import hudson.plugins.sonar.SonarRunnerInstallation

def instance = Jenkins.getInstance()

// Configure SonarQube Scanner
def sonarRunnerDescriptor = instance.getDescriptor(SonarRunnerInstallation.class)
def sonarRunner = new SonarRunnerInstallation(
    "SonarQube Scanner",            // Name
    "",                             // Home directory (empty for auto-install)
    [new InstallSourceProperty([   // Installation sources
        new SonarRunnerInstaller("4.6.2.2472")
    ])]
)
sonarRunnerDescriptor.setInstallations(sonarRunner)

instance.save()

println "Global tools configuration completed"
EOF

    jenkins-cli groovy tools-config.groovy
    rm tools-config.groovy
}

# Configure Slack notifications
configure_slack() {
    log "Configuring Slack notifications..."
    
    cat > slack-config.groovy << 'EOF'
import jenkins.model.*
import jenkins.plugins.slack.*

def instance = Jenkins.getInstance()
def slackDescriptor = instance.getDescriptor(SlackNotifier.class)

// Configure Slack settings
slackDescriptor.baseUrl = "https://hooks.slack.com/services/"
slackDescriptor.teamDomain = "your-team"
slackDescriptor.token = "your-slack-token"
slackDescriptor.tokenCredentialId = "slack-token"
slackDescriptor.botUser = false
slackDescriptor.room = "#course-creator-ci"

slackDescriptor.save()

println "Slack configuration completed"
EOF

    jenkins-cli groovy slack-config.groovy
    rm slack-config.groovy
}

# Configure webhooks
configure_webhooks() {
    log "Configuring Git webhooks..."
    
    # Run webhook configuration
    jenkins-cli groovy webhook-config.groovy
    
    log "Webhook configuration completed"
}

# Main setup function
main() {
    log "Starting Jenkins setup for Course Creator Platform..."
    
    check_jenkins_cli
    install_plugins
    configure_security
    configure_sonarqube
    configure_docker
    configure_credentials
    configure_global_tools
    configure_slack
    create_pipeline_job
    configure_webhooks
    
    log "Jenkins setup completed successfully!"
    log "Access Jenkins at: ${JENKINS_URL}"
    log "Pipeline job: ${JENKINS_URL}/job/course-creator-pipeline/"
    
    info "Next steps:"
    info "1. Update credentials with actual values"
    info "2. Run ./setup-webhook.sh to configure Git webhooks"
    info "3. Update SonarQube server URL and token"
    info "4. Configure Slack webhook token"
    info "5. Test the pipeline by pushing to repository"
    info "6. Monitor webhook delivery in repository settings"
}

# Execute main function
main "$@"