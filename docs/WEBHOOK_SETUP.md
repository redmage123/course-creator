# Git Webhook Setup for CI/CD Pipeline

**Version**: 2.2.0  
**Last Updated**: 2025-07-28

## Overview

The Course Creator Platform uses Git webhooks to automatically trigger CI/CD pipeline builds when changes are pushed to the repository. This document provides comprehensive instructions for setting up webhooks with various Git providers.

## 🎯 Quick Setup

### Automated Setup
```bash
# Set environment variables
export JENKINS_URL="http://your-jenkins-server:8080"
export GITHUB_REPO="your-org/course-creator"
export GITHUB_TOKEN="your-github-personal-access-token"

# Run automated webhook setup
cd jenkins/
./setup-webhook.sh
```

### Manual Setup
1. Configure Jenkins webhook settings
2. Add webhook to your Git repository
3. Test webhook connectivity
4. Monitor pipeline execution

## 🔧 Jenkins Configuration

### Required Plugins
The following Jenkins plugins are required for webhook functionality:
- `github` - GitHub integration
- `github-branch-source` - GitHub branch source
- `git` - Git plugin
- `workflow-multibranch` - Multibranch pipeline support

### Webhook Endpoints

| Provider | Endpoint | Method | Content Type |
|----------|----------|--------|--------------|
| GitHub | `/github-webhook/` | POST | application/json |
| GitLab | `/project/course-creator-pipeline` | POST | application/json |
| Bitbucket | `/bitbucket-hook/` | POST | application/x-www-form-urlencoded |
| Generic Git | `/git/notifyCommit?url=<repo-url>` | GET/POST | any |

## 🐙 GitHub Webhook Setup

### Manual Configuration
1. Navigate to your repository on GitHub
2. Go to **Settings** → **Webhooks**
3. Click **Add webhook**
4. Configure webhook settings:
   - **Payload URL**: `https://your-jenkins-server/github-webhook/`
   - **Content type**: `application/json`
   - **Secret**: Your webhook secret token
   - **SSL verification**: Enable SSL verification
   - **Which events**: Select events to trigger builds

### Webhook Events
Configure these events to trigger pipeline builds:
- **Push events** - Trigger on commits to any branch
- **Pull request events** - Trigger on PR creation/updates
- **Create events** - Trigger on branch/tag creation
- **Delete events** - Trigger on branch/tag deletion

### Example GitHub Webhook Configuration
```json
{
  "name": "web",
  "active": true,
  "events": [
    "push",
    "pull_request",
    "create",
    "delete"
  ],
  "config": {
    "url": "https://your-jenkins-server/github-webhook/",
    "content_type": "json",
    "secret": "your-webhook-secret-token",
    "insecure_ssl": "0"
  }
}
```

## 🦊 GitLab Webhook Setup

### Manual Configuration
1. Navigate to your project on GitLab
2. Go to **Settings** → **Webhooks**
3. Configure webhook settings:
   - **URL**: `https://your-jenkins-server/project/course-creator-pipeline`
   - **Secret Token**: Your webhook secret token
   - **Trigger events**: Select events to trigger builds
   - **SSL verification**: Enable SSL verification

### GitLab Webhook Events
- **Push events** - Commits pushed to repository
- **Tag push events** - Tags pushed to repository
- **Merge request events** - MR creation/updates
- **Wiki page events** - Wiki changes

## 🪣 Bitbucket Webhook Setup

### Manual Configuration
1. Navigate to your repository on Bitbucket
2. Go to **Repository settings** → **Webhooks**
3. Click **Add webhook**
4. Configure webhook settings:
   - **Title**: Course Creator CI/CD
   - **URL**: `https://your-jenkins-server/bitbucket-hook/`
   - **Status**: Active
   - **Triggers**: Repository push

## 🔒 Security Configuration

### Webhook Secrets
Always use webhook secrets to verify request authenticity:

```bash
# Generate secure webhook secret
WEBHOOK_SECRET=$(openssl rand -hex 20)

# Set in Jenkins credentials
jenkins-cli create-credentials-by-xml system::system::jenkins << EOF
<org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl>
  <scope>GLOBAL</scope>
  <id>github-webhook-secret</id>
  <description>GitHub Webhook Secret Token</description>
  <secret>${WEBHOOK_SECRET}</secret>
</org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl>
EOF
```

### Network Security
- Configure firewall rules to allow webhook traffic
- Use HTTPS in production environments
- Implement IP whitelisting for Git providers
- Monitor webhook delivery logs

### Authentication Methods
1. **Webhook Secrets** - Cryptographic verification
2. **IP Whitelisting** - Restrict source IPs
3. **SSL/TLS** - Encrypt webhook payloads
4. **API Tokens** - Authenticate API requests

## 🚀 Pipeline Triggers

### Jenkinsfile Configuration
```groovy
pipeline {
    agent any
    
    triggers {
        // GitHub webhook trigger
        githubPush()
        
        // Poll SCM as fallback (every 5 minutes)
        pollSCM('H/5 * * * *')
        
        // Periodic build for main branch (daily at 2 AM)
        cron(env.BRANCH_NAME == 'main' ? 'H 2 * * *' : '')
    }
    
    stages {
        // Pipeline stages...
    }
}
```

### Trigger Types
- **Push Triggers** - Build on every push
- **Pull Request Triggers** - Build on PR events
- **Tag Triggers** - Build on tag creation
- **Scheduled Triggers** - Periodic builds
- **Manual Triggers** - Manual pipeline execution

## 🧪 Testing Webhooks

### Webhook Testing Steps
1. **Push Test Commit**
   ```bash
   git commit --allow-empty -m "Test webhook trigger"
   git push origin main
   ```

2. **Check Webhook Delivery**
   - GitHub: Repository → Settings → Webhooks → Recent Deliveries
   - GitLab: Project → Settings → Webhooks → Test
   - Bitbucket: Repository settings → Webhooks → View requests

3. **Monitor Jenkins Pipeline**
   - Check Jenkins Blue Ocean for triggered builds
   - Review build logs for webhook reception
   - Verify pipeline execution stages

### Debugging Commands
```bash
# Test Jenkins webhook endpoint
curl -X POST https://your-jenkins-server/github-webhook/

# Check Jenkins webhook logs
tail -f /var/log/jenkins/jenkins.log | grep webhook

# Test Git provider connectivity
curl -I https://api.github.com
curl -I https://gitlab.com/api/v4
curl -I https://api.bitbucket.org/2.0

# Validate webhook payload
curl -X POST \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: push" \
  -d @test-payload.json \
  https://your-jenkins-server/github-webhook/
```

## 📊 Monitoring and Maintenance

### Webhook Monitoring
- Monitor webhook delivery success rates
- Track pipeline trigger patterns
- Alert on webhook failures
- Log webhook payload analysis

### Maintenance Tasks
- **Regular Secret Rotation** - Rotate webhook secrets quarterly
- **SSL Certificate Updates** - Maintain valid SSL certificates
- **Plugin Updates** - Keep Jenkins plugins updated
- **Connectivity Testing** - Periodic webhook connectivity tests

### Webhook Analytics
```bash
# Webhook delivery statistics
jenkins-cli groovy -e "
  def job = Jenkins.instance.getItem('course-creator-pipeline')
  def builds = job.getBuilds()
  def webhookBuilds = builds.findAll { it.getCause(hudson.triggers.SCMTrigger.SCMTriggerCause) }
  println \"Webhook-triggered builds: \${webhookBuilds.size()}\"
"
```

## 🛠️ Troubleshooting

### Common Issues

#### Webhook Not Triggering
**Symptoms**: Pipeline doesn't start after push  
**Solutions**:
- Verify webhook URL and credentials
- Check Jenkins webhook endpoint accessibility
- Confirm network connectivity from Git provider
- Review webhook delivery logs

#### 403 Forbidden Error
**Symptoms**: Webhook returns HTTP 403  
**Solutions**:
- Verify Jenkins authentication settings
- Check CSRF protection configuration
- Confirm webhook secret matches
- Review Jenkins authorization strategy

#### SSL Certificate Errors
**Symptoms**: SSL verification failures  
**Solutions**:
- Update SSL certificates
- Configure proper certificate chain
- Temporarily disable SSL verification for testing
- Use Let's Encrypt for automatic certificate management

#### Payload Format Errors
**Symptoms**: Pipeline fails to parse webhook payload  
**Solutions**:
- Verify Content-Type headers
- Check payload format expectations
- Review Jenkins webhook plugin documentation
- Test with sample payloads

### Debug Checklist
- [ ] Jenkins is accessible from internet
- [ ] Webhook URL is correctly configured
- [ ] Secret token matches between repository and Jenkins
- [ ] Required Jenkins plugins are installed
- [ ] Firewall allows webhook traffic
- [ ] SSL certificates are valid
- [ ] Pipeline job exists and is configured correctly

## 📚 Additional Resources

### Documentation Links
- [Jenkins GitHub Plugin](https://plugins.jenkins.io/github/)
- [GitHub Webhooks Documentation](https://docs.github.com/en/developers/webhooks-and-events/webhooks)
- [GitLab Webhooks Documentation](https://docs.gitlab.com/ee/user/project/integrations/webhooks.html)
- [Bitbucket Webhooks Documentation](https://support.atlassian.com/bitbucket-cloud/docs/manage-webhooks/)

### Useful Scripts
- `jenkins/setup-webhook.sh` - Automated webhook setup
- `jenkins/webhook-config.groovy` - Jenkins webhook configuration
- `jenkins/jenkins-setup.sh` - Complete Jenkins setup

### Environment Variables
```bash
# Required environment variables
export JENKINS_URL="https://your-jenkins-server"
export GITHUB_REPO="your-org/course-creator"
export GITHUB_TOKEN="your-github-token"
export WEBHOOK_SECRET="your-webhook-secret"
export JENKINS_USER="admin"
export JENKINS_PASSWORD="admin-password"
```

## 🎯 Best Practices

### Webhook Configuration
1. **Use HTTPS** for all webhook URLs
2. **Implement Secret Verification** for payload authentication
3. **Configure Appropriate Events** to avoid unnecessary builds
4. **Set Reasonable Timeouts** for webhook responses
5. **Monitor Webhook Health** with regular testing

### Pipeline Optimization
1. **Branch-specific Triggers** - Different triggers for different branches
2. **Conditional Builds** - Skip builds for documentation-only changes
3. **Parallel Execution** - Use parallel stages for faster builds
4. **Build Caching** - Cache dependencies and artifacts
5. **Resource Management** - Optimize resource usage

### Security Best Practices
1. **Regular Secret Rotation** - Change webhook secrets regularly
2. **IP Whitelisting** - Restrict webhook sources
3. **Audit Logging** - Log all webhook activities
4. **Access Control** - Limit webhook configuration permissions
5. **Secure Storage** - Store secrets in Jenkins credentials

---

**Need Help?** Check the troubleshooting section or contact the DevOps team for assistance with webhook configuration.