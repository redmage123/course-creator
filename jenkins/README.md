# Jenkins CI/CD Pipeline Configuration

This directory contains all the configuration files and scripts needed to set up the Jenkins CI/CD pipeline for the Course Creator Platform.

## 📁 Files Overview

| File | Purpose | Usage |
|------|---------|-------|
| `jenkins-setup.sh` | Complete Jenkins setup automation | `./jenkins-setup.sh` |
| `webhook-config.groovy` | Webhook configuration script | Called by setup scripts |
| `setup-webhook.sh` | Git webhook setup automation | `./setup-webhook.sh` |
| `job-config.xml` | Jenkins pipeline job configuration | Used by setup scripts |
| `test-webhook-payload.json` | Sample webhook payload for testing | Testing webhook functionality |

## 🚀 Quick Start

### 1. Complete Jenkins Setup
```bash
# Run complete Jenkins setup (includes webhook configuration)
./jenkins-setup.sh
```

### 2. Configure Git Webhooks
```bash
# Set environment variables
export JENKINS_URL="http://your-jenkins-server:8080"
export GITHUB_REPO="your-org/course-creator"
export GITHUB_TOKEN="your-github-personal-access-token"

# Run webhook setup
./setup-webhook.sh
```

### 3. Test Webhook
```bash
# Test webhook endpoint
curl -X POST \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: push" \
  -d @test-webhook-payload.json \
  http://your-jenkins-server:8080/github-webhook/
```

## 🔧 Configuration Details

### Webhook Endpoints
- **GitHub**: `/github-webhook/`
- **GitLab**: `/project/course-creator-pipeline`
- **Bitbucket**: `/bitbucket-hook/`
- **Generic Git**: `/git/notifyCommit?url=<repo-url>`

### Required Environment Variables
```bash
export JENKINS_URL="http://your-jenkins-server:8080"
export JENKINS_USER="admin"
export JENKINS_PASSWORD="admin"
export GITHUB_REPO="your-org/course-creator"
export GITHUB_TOKEN="your-github-personal-access-token"
export WEBHOOK_SECRET="your-webhook-secret-token"
```

### Jenkins Plugins Required
- github
- github-branch-source
- git
- workflow-multibranch
- sonar
- docker-workflow
- pipeline-stage-view

## 📚 Documentation

- **Complete Webhook Setup Guide**: `../docs/WEBHOOK_SETUP.md`
- **CI/CD Pipeline Documentation**: `../docs/ci-cd-pipeline.md`
- **Jenkins Configuration**: Jenkins setup details and troubleshooting

## 🛠️ Troubleshooting

### Common Issues
1. **Webhook not triggering**: Check URL and credentials
2. **403 Forbidden**: Verify Jenkins authentication
3. **SSL errors**: Check certificate configuration
4. **Plugin missing**: Run `jenkins-setup.sh` to install required plugins

### Debug Commands
```bash
# Check Jenkins health
curl http://your-jenkins-server:8080/api/json

# Test webhook endpoint
curl -X POST http://your-jenkins-server:8080/github-webhook/

# View Jenkins logs
tail -f /var/log/jenkins/jenkins.log
```

## 🔒 Security Notes

- Always use HTTPS in production
- Configure webhook secrets for payload verification
- Use proper Jenkins authentication and authorization
- Regularly update Jenkins and plugins
- Monitor webhook delivery logs

## 📞 Support

For issues with Jenkins setup or webhook configuration, refer to:
1. `../docs/WEBHOOK_SETUP.md` - Comprehensive webhook guide
2. Jenkins logs at `/var/log/jenkins/jenkins.log`
3. GitHub webhook delivery logs in repository settings
4. SonarQube configuration at `../sonarqube/`

---

**Note**: Make sure Jenkins is accessible from the internet for webhooks to work properly.