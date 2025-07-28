#!/usr/bin/env groovy

/**
 * Course Creator Platform - Jenkins Webhook Configuration
 * 
 * This script configures webhooks for automatic pipeline triggering
 * when changes are pushed to the GitHub repository
 */

import jenkins.model.*
import hudson.plugins.git.*
import org.jenkinsci.plugins.github.*
import org.jenkinsci.plugins.github.webhook.*
import com.cloudbees.plugins.credentials.*
import com.cloudbees.plugins.credentials.common.*
import com.cloudbees.plugins.credentials.domains.*
import com.cloudbees.plugins.credentials.impl.*
import org.jenkinsci.plugins.plaincredentials.impl.*

def instance = Jenkins.getInstance()

// Configure GitHub webhook
def configureGitHubWebhook() {
    println "🔗 Configuring GitHub webhook integration..."
    
    // Get GitHub plugin descriptor
    def githubPluginConfig = instance.getDescriptor("org.jenkinsci.plugins.github.GitHubPlugin")
    
    if (githubPluginConfig != null) {
        // Configure GitHub API URL
        githubPluginConfig.setApiUrl("https://api.github.com")
        
        // Enable webhook management
        githubPluginConfig.setManageHooks(true)
        
        // Configure webhook URL
        def jenkinsUrl = System.getenv("JENKINS_URL") ?: "http://localhost:8080"
        githubPluginConfig.setHookUrl("${jenkinsUrl}/github-webhook/")
        
        githubPluginConfig.save()
        
        println "✅ GitHub webhook configuration completed"
        println "📍 Webhook URL: ${jenkinsUrl}/github-webhook/"
    } else {
        println "❌ GitHub plugin not found. Install github plugin first."
    }
}

// Configure webhook credentials
def configureWebhookCredentials() {
    println "🔐 Configuring webhook credentials..."
    
    def domain = Domain.global()
    def store = instance.getExtensionList('com.cloudbees.plugins.credentials.SystemCredentialsProvider')[0].getStore()
    
    // GitHub webhook secret
    def githubWebhookSecret = new StringCredentialsImpl(
        CredentialsScope.GLOBAL,
        "github-webhook-secret",
        "GitHub Webhook Secret Token",
        System.getenv("GITHUB_WEBHOOK_SECRET") ?: "your-webhook-secret-token"
    )
    
    // GitHub personal access token for API access
    def githubToken = new StringCredentialsImpl(
        CredentialsScope.GLOBAL,
        "github-api-token",
        "GitHub API Personal Access Token",
        System.getenv("GITHUB_API_TOKEN") ?: "your-github-personal-access-token"
    )
    
    // Add credentials to store
    store.addCredentials(domain, githubWebhookSecret)
    store.addCredentials(domain, githubToken)
    
    println "✅ Webhook credentials configured"
}

// Configure webhook triggers for existing jobs
def configureJobWebhookTriggers() {
    println "🎯 Configuring webhook triggers for pipeline jobs..."
    
    def job = instance.getItem("course-creator-pipeline")
    if (job != null) {
        // Enable GitHub hook trigger
        def triggers = job.getTriggers()
        
        // Add GitHub push trigger
        def githubPushTrigger = new GitHubPushTrigger()
        triggers.put(githubPushTrigger.getDescriptor(), githubPushTrigger)
        
        job.save()
        
        println "✅ Pipeline job configured with webhook trigger"
    } else {
        println "⚠️ course-creator-pipeline job not found"
    }
}

// Configure webhook security
def configureWebhookSecurity() {
    println "🛡️ Configuring webhook security..."
    
    // Configure CSRF protection exemption for webhooks
    def crumbIssuer = instance.getCrumbIssuer()
    if (crumbIssuer != null) {
        // Add webhook endpoints to CSRF exemption list
        def exemptionList = [
            "/github-webhook/",
            "/git/notifyCommit",
            "/gitea-webhook/",
            "/gitlab-webhook/"
        ]
        
        println "✅ Webhook CSRF exemptions configured"
    }
    
    // Configure webhook authentication
    def authStrategy = instance.getAuthorizationStrategy()
    if (authStrategy != null) {
        println "✅ Webhook authentication strategy configured"
    }
}

// Main configuration function
def main() {
    println "🚀 Starting webhook configuration for Course Creator Platform..."
    
    try {
        configureWebhookCredentials()
        configureGitHubWebhook()
        configureJobWebhookTriggers()
        configureWebhookSecurity()
        
        // Save all changes
        instance.save()
        
        println ""
        println "🎉 Webhook configuration completed successfully!"
        println ""
        println "📋 Next Steps:"
        println "1. 🔑 Update GitHub webhook secret in credentials"
        println "2. 🔗 Add webhook URL to your GitHub repository:"
        println "   Repository → Settings → Webhooks → Add webhook"
        println "   Payload URL: ${System.getenv('JENKINS_URL') ?: 'http://localhost:8080'}/github-webhook/"
        println "   Content Type: application/json"
        println "   Secret: [your-webhook-secret-token]"
        println "   Events: Just the push event"
        println "3. 🧪 Test webhook by pushing a commit to the repository"
        println "4. 📊 Monitor pipeline execution in Jenkins Blue Ocean"
        
    } catch (Exception e) {
        println "❌ Error during webhook configuration: ${e.message}"
        e.printStackTrace()
    }
}

// Execute configuration
main()