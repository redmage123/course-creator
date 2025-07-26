#!/usr/bin/env groovy

/**
 * Course Creator Platform - Jenkins Pipeline
 * 
 * This pipeline handles:
 * - Code quality analysis with SonarQube
 * - Multi-service testing (unit, integration, e2e)
 * - Security scanning
 * - Docker image building
 * - Multi-environment deployment
 * - Notification and reporting
 */

pipeline {
    agent any

    // Environment variables
    environment {
        // Application versions
        PYTHON_VERSION = '3.10'
        NODE_VERSION = '18'
        
        // Docker and deployment
        DOCKER_REGISTRY = credentials('docker-registry')
        DOCKER_REPO = 'course-creator'
        
        // SonarQube
        SONAR_HOST_URL = credentials('sonar-host-url')
        SONAR_AUTH_TOKEN = credentials('sonar-auth-token')
        
        // Database and services
        POSTGRES_CREDENTIALS = credentials('postgres-credentials')
        REDIS_URL = 'redis://localhost:6379'
        
        // Security and auth
        JWT_SECRET_KEY = credentials('jwt-secret-key')
        ANTHROPIC_API_KEY = credentials('anthropic-api-key')
        OPENAI_API_KEY = credentials('openai-api-key')
        
        // Deployment environments
        DEV_NAMESPACE = 'course-creator-dev'
        STAGING_NAMESPACE = 'course-creator-staging'
        PROD_NAMESPACE = 'course-creator-prod'
        
        // Build metadata
        BUILD_VERSION = "${env.BUILD_NUMBER}-${env.GIT_COMMIT.substring(0,7)}"
        IMAGE_TAG = "${env.BRANCH_NAME}-${BUILD_VERSION}"
        
        // Notification settings
        SLACK_CHANNEL = '#course-creator-ci'
        EMAIL_RECIPIENTS = 'devops@coursecreator.com'
    }

    // Pipeline options
    options {
        // Keep build logs for 30 days, artifacts for 7 days
        buildDiscarder(logRotator(daysToKeepStr: '30', artifactDaysToKeepStr: '7'))
        
        // Timeout the entire pipeline after 60 minutes
        timeout(time: 60, unit: 'MINUTES')
        
        // Retry on failure
        retry(1)
        
        // Skip default checkout
        skipDefaultCheckout()
        
        // Concurrent builds per branch
        disableConcurrentBuilds()
        
        // Timestamps in console output
        timestamps()
    }

    // Build parameters
    parameters {
        choice(
            name: 'DEPLOY_ENVIRONMENT',
            choices: ['none', 'dev', 'staging', 'prod'],
            description: 'Select deployment environment (none = skip deployment)'
        )
        booleanParam(
            name: 'SKIP_TESTS',
            defaultValue: false,
            description: 'Skip test execution (for emergency deployments)'
        )
        booleanParam(
            name: 'SKIP_SONAR',
            defaultValue: false,
            description: 'Skip SonarQube analysis'
        )
        booleanParam(
            name: 'FORCE_DEPLOY',
            defaultValue: false,
            description: 'Force deployment even if quality gates fail'
        )
        string(
            name: 'DOCKER_TAG_OVERRIDE',
            defaultValue: '',
            description: 'Override Docker image tag (optional)'
        )
    }

    // Pipeline stages
    stages {
        stage('Checkout & Setup') {
            steps {
                script {
                    // Custom checkout with submodules
                    checkout scm
                    
                    // Set dynamic build info
                    currentBuild.displayName = "#${env.BUILD_NUMBER} - ${env.BRANCH_NAME}"
                    currentBuild.description = "Commit: ${env.GIT_COMMIT.substring(0,7)} | Version: ${BUILD_VERSION}"
                    
                    // Store build metadata
                    writeFile file: 'build-info.json', text: """{
                        "buildNumber": "${env.BUILD_NUMBER}",
                        "gitCommit": "${env.GIT_COMMIT}",
                        "gitBranch": "${env.BRANCH_NAME}",
                        "buildVersion": "${BUILD_VERSION}",
                        "imageTag": "${IMAGE_TAG}",
                        "timestamp": "${new Date().format('yyyy-MM-dd HH:mm:ss')}"
                    }"""
                }
                
                // Setup Python environment
                sh '''
                    echo "🐍 Setting up Python environment..."
                    python${PYTHON_VERSION} -m venv .venv
                    source .venv/bin/activate
                    python -m pip install --upgrade pip
                    pip install -r requirements.txt
                    pip install -r test_requirements.txt
                '''
                
                // Setup Node.js environment
                sh '''
                    echo "📦 Setting up Node.js environment..."
                    cd frontend
                    npm ci --production=false
                '''
                
                // Verify tools
                sh '''
                    echo "🔍 Verifying tools..."
                    python --version
                    node --version
                    npm --version
                    docker --version
                    sonar-scanner --version || echo "SonarQube scanner not found - will install"
                '''
            }
        }

        stage('Code Quality & Security') {
            parallel {
                stage('Linting & Formatting') {
                    steps {
                        sh '''
                            echo "🧹 Running code linting and formatting checks..."
                            source .venv/bin/activate
                            
                            # Python formatting and linting
                            echo "Checking Python code formatting..."
                            black --check --diff services/ lab-containers/ || exit 1
                            
                            echo "Checking Python import sorting..."
                            isort --check-only --diff services/ lab-containers/ || exit 1
                            
                            echo "Running Python linting..."
                            flake8 services/ lab-containers/ --config=.flake8 --output-file=flake8-report.txt || exit 1
                            
                            # JavaScript/Frontend linting
                            echo "Running JavaScript linting..."
                            cd frontend
                            npm run lint -- --format=json --output-file=../eslint-report.json || exit 1
                        '''
                    }
                    post {
                        always {
                            // Archive linting reports
                            archiveArtifacts artifacts: 'flake8-report.txt,eslint-report.json', allowEmptyArchive: true
                        }
                    }
                }

                stage('Security Scanning') {
                    steps {
                        sh '''
                            echo "🔒 Running security scans..."
                            source .venv/bin/activate
                            
                            # Install security tools
                            pip install bandit safety semgrep
                            
                            # Bandit security scan for Python
                            echo "Running Bandit security scan..."
                            bandit -r services/ lab-containers/ -f json -o bandit-report.json || true
                            
                            # Safety check for Python dependencies
                            echo "Running Safety dependency check..."
                            safety check --json --output safety-report.json || true
                            
                            # Semgrep scan for additional security issues
                            echo "Running Semgrep scan..."
                            semgrep --config=auto --json --output=semgrep-report.json services/ lab-containers/ || true
                            
                            # Frontend security scan
                            echo "Running npm audit..."
                            cd frontend
                            npm audit --audit-level moderate --json > ../npm-audit-report.json || true
                        '''
                    }
                    post {
                        always {
                            archiveArtifacts artifacts: 'bandit-report.json,safety-report.json,semgrep-report.json,npm-audit-report.json', allowEmptyArchive: true
                        }
                    }
                }

                stage('Type Checking') {
                    steps {
                        sh '''
                            echo "🔍 Running type checking..."
                            source .venv/bin/activate
                            
                            # Python type checking with mypy
                            echo "Running mypy type checking..."
                            mypy services/ lab-containers/ --config-file=mypy.ini --html-report=mypy-report --txt-report=mypy-report || true
                        '''
                    }
                    post {
                        always {
                            publishHTML([
                                allowMissing: false,
                                alwaysLinkToLastBuild: true,
                                keepAll: true,
                                reportDir: 'mypy-report',
                                reportFiles: 'index.html',
                                reportName: 'MyPy Type Check Report'
                            ])
                        }
                    }
                }
            }
        }

        stage('SonarQube Analysis') {
            when {
                not { params.SKIP_SONAR }
            }
            steps {
                script {
                    // Install SonarQube scanner if not available
                    sh '''
                        if ! command -v sonar-scanner &> /dev/null; then
                            echo "Installing SonarQube Scanner..."
                            wget -q https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-4.8.0.2856-linux.zip
                            unzip -q sonar-scanner-cli-4.8.0.2856-linux.zip
                            sudo mv sonar-scanner-4.8.0.2856-linux /opt/sonar-scanner
                            sudo ln -sf /opt/sonar-scanner/bin/sonar-scanner /usr/local/bin/sonar-scanner
                        fi
                    '''
                }
                
                withSonarQubeEnv('SonarQube') {
                    sh '''
                        echo "📊 Running SonarQube analysis..."
                        
                        sonar-scanner \\
                            -Dsonar.projectKey=course-creator \\
                            -Dsonar.projectName="Course Creator Platform" \\
                            -Dsonar.projectVersion=${BUILD_VERSION} \\
                            -Dsonar.sources=services,lab-containers,frontend/js \\
                            -Dsonar.tests=tests \\
                            -Dsonar.python.coverage.reportPaths=coverage.xml \\
                            -Dsonar.javascript.lcov.reportPaths=frontend/coverage/lcov.info \\
                            -Dsonar.exclusions=**/node_modules/**,**/__pycache__/**,**/migrations/**,**/static/**,**/templates/** \\
                            -Dsonar.python.bandit.reportPaths=bandit-report.json \\
                            -Dsonar.python.flake8.reportPaths=flake8-report.txt \\
                            -Dsonar.eslint.reportPaths=eslint-report.json
                    '''
                }
            }
        }

        stage('Quality Gate') {
            when {
                not { params.SKIP_SONAR }
            }
            steps {
                script {
                    // Wait for SonarQube quality gate result
                    timeout(time: 10, unit: 'MINUTES') {
                        def qg = waitForQualityGate()
                        if (qg.status != 'OK' && !params.FORCE_DEPLOY) {
                            error "Pipeline aborted due to quality gate failure: ${qg.status}"
                        } else if (qg.status != 'OK' && params.FORCE_DEPLOY) {
                            echo "⚠️ Quality gate failed but FORCE_DEPLOY is enabled. Continuing..."
                            currentBuild.result = 'UNSTABLE'
                        }
                    }
                }
            }
        }

        stage('Testing') {
            when {
                not { params.SKIP_TESTS }
            }
            parallel {
                stage('Unit Tests') {
                    steps {
                        sh '''
                            echo "🧪 Running unit tests..."
                            source .venv/bin/activate
                            
                            # Run unit tests with coverage
                            python -m pytest tests/unit/ \\
                                -v \\
                                --cov=services \\
                                --cov=lab-containers \\
                                --cov-report=xml:coverage.xml \\
                                --cov-report=html:htmlcov \\
                                --cov-fail-under=80 \\
                                --junit-xml=unit-test-results.xml \\
                                --html=unit-test-report.html \\
                                --self-contained-html
                        '''
                    }
                    post {
                        always {
                            junit 'unit-test-results.xml'
                            publishHTML([
                                allowMissing: false,
                                alwaysLinkToLastBuild: true,
                                keepAll: true,
                                reportDir: 'htmlcov',
                                reportFiles: 'index.html',
                                reportName: 'Coverage Report'
                            ])
                            publishHTML([
                                allowMissing: false,
                                alwaysLinkToLastBuild: true,
                                keepAll: true,
                                reportDir: '.',
                                reportFiles: 'unit-test-report.html',
                                reportName: 'Unit Test Report'
                            ])
                        }
                    }
                }

                stage('Integration Tests') {
                    steps {
                        sh '''
                            echo "🔗 Running integration tests..."
                            source .venv/bin/activate
                            
                            # Start test services
                            docker-compose -f docker-compose.test.yml up -d postgres redis
                            sleep 10
                            
                            # Setup test database
                            export DATABASE_URL="postgresql://test_user:test_pass@localhost:5432/course_creator_test"
                            export REDIS_URL="redis://localhost:6379/1"
                            python setup-database.py --test
                            
                            # Run integration tests
                            python -m pytest tests/integration/ \\
                                -v \\
                                --junit-xml=integration-test-results.xml \\
                                --html=integration-test-report.html \\
                                --self-contained-html
                        '''
                    }
                    post {
                        always {
                            sh 'docker-compose -f docker-compose.test.yml down || true'
                            junit 'integration-test-results.xml'
                            publishHTML([
                                allowMissing: false,
                                alwaysLinkToLastBuild: true,
                                keepAll: true,
                                reportDir: '.',
                                reportFiles: 'integration-test-report.html',
                                reportName: 'Integration Test Report'
                            ])
                        }
                    }
                }

                stage('Frontend Tests') {
                    steps {
                        sh '''
                            echo "🎨 Running frontend tests..."
                            source .venv/bin/activate
                            
                            # Run Python frontend tests
                            python -m pytest tests/frontend/ \\
                                -v \\
                                --junit-xml=frontend-python-test-results.xml \\
                                --html=frontend-python-test-report.html \\
                                --self-contained-html
                            
                            # Run JavaScript tests
                            cd frontend
                            npm test -- --coverage --watchAll=false --ci --testResultsProcessor=jest-junit
                            
                            # Run E2E tests
                            npm run test:e2e
                        '''
                    }
                    post {
                        always {
                            junit 'frontend-python-test-results.xml,frontend/junit.xml'
                            publishHTML([
                                allowMissing: false,
                                alwaysLinkToLastBuild: true,
                                keepAll: true,
                                reportDir: 'frontend/coverage/lcov-report',
                                reportFiles: 'index.html',
                                reportName: 'Frontend Coverage Report'
                            ])
                        }
                    }
                }

                stage('Multi-IDE Lab Tests') {
                    steps {
                        sh '''
                            echo "🔬 Running multi-IDE lab tests..."
                            source .venv/bin/activate
                            
                            # Test lab container functionality
                            python tests/runners/run_lab_tests.py --verbose --junit-xml=lab-test-results.xml
                        '''
                    }
                    post {
                        always {
                            junit 'lab-test-results.xml'
                        }
                    }
                }

                stage('E2E Tests') {
                    steps {
                        sh '''
                            echo "🌐 Running end-to-end tests..."
                            source .venv/bin/activate
                            
                            # Start full platform for E2E tests
                            docker-compose -f docker-compose.test.yml up -d
                            sleep 30
                            
                            # Wait for services to be healthy
                            ./scripts/wait-for-services.sh
                            
                            # Run E2E tests
                            python -m pytest tests/e2e/ \\
                                -v \\
                                --junit-xml=e2e-test-results.xml \\
                                --html=e2e-test-report.html \\
                                --self-contained-html
                        '''
                    }
                    post {
                        always {
                            sh 'docker-compose -f docker-compose.test.yml down || true'
                            junit 'e2e-test-results.xml'
                            publishHTML([
                                allowMissing: false,
                                alwaysLinkToLastBuild: true,
                                keepAll: true,
                                reportDir: '.',
                                reportFiles: 'e2e-test-report.html',
                                reportName: 'E2E Test Report'
                            ])
                        }
                    }
                }
            }
        }

        stage('Build Docker Images') {
            steps {
                script {
                    def services = [
                        'user-management',
                        'course-generator', 
                        'content-storage',
                        'course-management',
                        'content-management',
                        'analytics',
                        'lab-containers',
                        'frontend'
                    ]
                    
                    def dockerTag = params.DOCKER_TAG_OVERRIDE ?: IMAGE_TAG
                    
                    echo "🐳 Building Docker images with tag: ${dockerTag}"
                    
                    // Build all service images in parallel
                    def buildSteps = [:]
                    services.each { service ->
                        buildSteps[service] = {
                            if (service == 'frontend') {
                                sh """
                                    echo "Building frontend image..."
                                    docker build -t ${DOCKER_REGISTRY}/${DOCKER_REPO}-${service}:${dockerTag} \\
                                        -t ${DOCKER_REGISTRY}/${DOCKER_REPO}-${service}:latest \\
                                        -f frontend/Dockerfile .
                                """
                            } else if (service == 'lab-containers') {
                                sh """
                                    echo "Building lab-containers image..."
                                    docker build -t ${DOCKER_REGISTRY}/${DOCKER_REPO}-${service}:${dockerTag} \\
                                        -t ${DOCKER_REGISTRY}/${DOCKER_REPO}-${service}:latest \\
                                        -f lab-containers/Dockerfile .
                                """
                            } else {
                                sh """
                                    echo "Building ${service} image..."
                                    docker build -t ${DOCKER_REGISTRY}/${DOCKER_REPO}-${service}:${dockerTag} \\
                                        -t ${DOCKER_REGISTRY}/${DOCKER_REPO}-${service}:latest \\
                                        -f services/${service}/Dockerfile .
                                """
                            }
                        }
                    }
                    
                    parallel buildSteps
                    
                    // Build multi-IDE lab images
                    sh """
                        echo "Building multi-IDE lab images..."
                        cd lab-containers/lab-images
                        
                        # Build base multi-IDE image
                        docker build -t ${DOCKER_REGISTRY}/${DOCKER_REPO}-multi-ide-base:${dockerTag} \\
                            -t ${DOCKER_REGISTRY}/${DOCKER_REPO}-multi-ide-base:latest \\
                            multi-ide-base/
                        
                        # Build Python multi-IDE image
                        docker build -t ${DOCKER_REGISTRY}/${DOCKER_REPO}-python-lab-multi-ide:${dockerTag} \\
                            -t ${DOCKER_REGISTRY}/${DOCKER_REPO}-python-lab-multi-ide:latest \\
                            python-lab-multi-ide/
                    """
                }
            }
            post {
                success {
                    echo "✅ All Docker images built successfully"
                }
                failure {
                    echo "❌ Docker image build failed"
                }
            }
        }

        stage('Security Scan Images') {
            steps {
                sh '''
                    echo "🔒 Scanning Docker images for vulnerabilities..."
                    
                    # Install Trivy if not available
                    if ! command -v trivy &> /dev/null; then
                        wget -qO- https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin
                    fi
                    
                    # Scan key images
                    trivy image --format json --output trivy-frontend-report.json ${DOCKER_REGISTRY}/${DOCKER_REPO}-frontend:${IMAGE_TAG} || true
                    trivy image --format json --output trivy-lab-containers-report.json ${DOCKER_REGISTRY}/${DOCKER_REPO}-lab-containers:${IMAGE_TAG} || true
                    trivy image --format json --output trivy-user-management-report.json ${DOCKER_REGISTRY}/${DOCKER_REPO}-user-management:${IMAGE_TAG} || true
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'trivy-*-report.json', allowEmptyArchive: true
                }
            }
        }

        stage('Push Images') {
            when {
                anyOf {
                    branch 'main'
                    branch 'develop'
                    expression { params.DEPLOY_ENVIRONMENT != 'none' }
                }
            }
            steps {
                script {
                    docker.withRegistry("https://${DOCKER_REGISTRY}", 'docker-registry-credentials') {
                        def services = [
                            'user-management', 'course-generator', 'content-storage',
                            'course-management', 'content-management', 'analytics',
                            'lab-containers', 'frontend', 'multi-ide-base', 'python-lab-multi-ide'
                        ]
                        
                        def dockerTag = params.DOCKER_TAG_OVERRIDE ?: IMAGE_TAG
                        
                        echo "📤 Pushing Docker images to registry..."
                        
                        services.each { service ->
                            sh "docker push ${DOCKER_REGISTRY}/${DOCKER_REPO}-${service}:${dockerTag}"
                            if (env.BRANCH_NAME == 'main') {
                                sh "docker push ${DOCKER_REGISTRY}/${DOCKER_REPO}-${service}:latest"
                            }
                        }
                    }
                }
            }
        }

        stage('Deploy') {
            when {
                expression { params.DEPLOY_ENVIRONMENT != 'none' }
            }
            steps {
                script {
                    def environment = params.DEPLOY_ENVIRONMENT
                    def dockerTag = params.DOCKER_TAG_OVERRIDE ?: IMAGE_TAG
                    
                    echo "🚀 Deploying to ${environment} environment..."
                    
                    // Use deployment script
                    sh """
                        chmod +x scripts/deploy.sh
                        ./scripts/deploy.sh \\
                            --environment ${environment} \\
                            --version ${dockerTag} \\
                            --registry ${DOCKER_REGISTRY} \\
                            --repo ${DOCKER_REPO}
                    """
                }
            }
        }

        stage('Post-Deploy Tests') {
            when {
                expression { params.DEPLOY_ENVIRONMENT != 'none' }
            }
            steps {
                sh '''
                    echo "🧪 Running post-deployment tests..."
                    source .venv/bin/activate
                    
                    # Smoke tests
                    python -m pytest tests/smoke/ \\
                        -v \\
                        --junit-xml=smoke-test-results.xml \\
                        --html=smoke-test-report.html \\
                        --self-contained-html
                '''
            }
            post {
                always {
                    junit 'smoke-test-results.xml'
                    publishHTML([
                        allowMissing: false,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: '.',
                        reportFiles: 'smoke-test-report.html',
                        reportName: 'Smoke Test Report'
                    ])
                }
            }
        }
    }

    // Post-build actions
    post {
        always {
            // Clean up workspace
            sh '''
                echo "🧹 Cleaning up..."
                docker system prune -f || true
                
                # Archive important files
                mkdir -p pipeline-artifacts
                cp build-info.json pipeline-artifacts/ || true
                cp *.xml pipeline-artifacts/ || true
                cp *.json pipeline-artifacts/ || true
                cp *.html pipeline-artifacts/ || true
            '''
            
            // Archive artifacts
            archiveArtifacts artifacts: 'pipeline-artifacts/*', allowEmptyArchive: true
            
            // Publish test results
            publishTestResults testResultsPattern: '*.xml'
            
            // Record issues (warnings, etc.)
            recordIssues enabledForFailure: true, tools: [
                pyLint(pattern: 'flake8-report.txt'),
                esLint(pattern: 'eslint-report.json')
            ]
        }
        
        success {
            script {
                def message = """
🎉 *Course Creator Pipeline Success* 🎉

*Branch:* ${env.BRANCH_NAME}
*Build:* #${env.BUILD_NUMBER}
*Commit:* ${env.GIT_COMMIT.substring(0,7)}
*Duration:* ${currentBuild.durationString}

*Environment:* ${params.DEPLOY_ENVIRONMENT}
*Image Tag:* ${IMAGE_TAG}

✅ All stages completed successfully!
"""
                
                // Send Slack notification
                slackSend(
                    channel: SLACK_CHANNEL,
                    color: 'good',
                    message: message
                )
                
                // Send email notification for main branch
                if (env.BRANCH_NAME == 'main') {
                    emailext(
                        subject: "✅ Course Creator Pipeline Success - Build #${env.BUILD_NUMBER}",
                        body: message,
                        to: EMAIL_RECIPIENTS
                    )
                }
            }
        }
        
        failure {
            script {
                def message = """
💥 *Course Creator Pipeline Failed* 💥

*Branch:* ${env.BRANCH_NAME}
*Build:* #${env.BUILD_NUMBER}
*Commit:* ${env.GIT_COMMIT.substring(0,7)}
*Duration:* ${currentBuild.durationString}

*Failed Stage:* ${env.STAGE_NAME}

❌ Please check the logs and fix the issues.
📊 [Build Details](${env.BUILD_URL})
"""
                
                // Send Slack notification
                slackSend(
                    channel: SLACK_CHANNEL,
                    color: 'danger',
                    message: message
                )
                
                // Send email notification
                emailext(
                    subject: "❌ Course Creator Pipeline Failed - Build #${env.BUILD_NUMBER}",
                    body: message,
                    to: EMAIL_RECIPIENTS
                )
            }
        }
        
        unstable {
            script {
                def message = """
⚠️ *Course Creator Pipeline Unstable* ⚠️

*Branch:* ${env.BRANCH_NAME}
*Build:* #${env.BUILD_NUMBER}
*Commit:* ${env.GIT_COMMIT.substring(0,7)}
*Duration:* ${currentBuild.durationString}

⚠️ Pipeline completed with warnings.
📊 [Build Details](${env.BUILD_URL})
"""
                
                slackSend(
                    channel: SLACK_CHANNEL,
                    color: 'warning',
                    message: message
                )
            }
        }
        
        cleanup {
            // Final cleanup
            sh '''
                echo "🧽 Final cleanup..."
                docker-compose -f docker-compose.test.yml down || true
                source .venv/bin/activate && deactivate || true
                rm -rf .venv || true
            '''
        }
    }
}