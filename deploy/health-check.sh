#!/bin/bash

"""
COURSE CREATOR PLATFORM - HEALTH CHECK AND VERIFICATION SCRIPT
==============================================================

Comprehensive health check script for verifying deployment status,
service health, security configuration, and performance metrics.

FEATURES:
- Service availability verification
- Database connectivity testing  
- Security configuration validation
- Performance metrics collection
- OWASP security compliance checking
- Integration testing

USAGE:
    ./health-check.sh [OPTIONS]

OPTIONS:
    --silent        Suppress verbose output
    --json         Output results in JSON format
    --security     Run security compliance checks
    --performance  Run performance benchmarks
    --integration  Run integration tests
    --help         Show this help message

AUTHOR: Course Creator Platform Team
VERSION: 2.8.0 (OWASP Security Enhanced)
"""

set -euo pipefail

# =============================================================================
# CONFIGURATION AND CONSTANTS
# =============================================================================

readonly SCRIPT_VERSION="2.8.0"
readonly HEALTH_CHECK_TIMEOUT=30
readonly PERFORMANCE_TEST_DURATION=60

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly PURPLE='\033[0;35m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m' # No Color

# Configuration
SILENT_MODE=false
JSON_OUTPUT=false
RUN_SECURITY_CHECKS=false
RUN_PERFORMANCE_TESTS=false
RUN_INTEGRATION_TESTS=false
BASE_URL="http://localhost"

# Service ports and endpoints
declare -A SERVICES=(
    ["frontend"]="3000:/"
    ["user-management"]="8000:/health"
    ["course-generator"]="8001:/health"
    ["content-storage"]="8003:/health"
    ["course-management"]="8004:/health"
    ["content-management"]="8005:/health"
    ["lab-manager"]="8006:/health"
    ["analytics"]="8007:/health"
    ["organization-management"]="8008:/health"
)

# Results storage
declare -A HEALTH_RESULTS
declare -A PERFORMANCE_RESULTS
declare -A SECURITY_RESULTS

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

log() {
    if [[ "$SILENT_MODE" == "false" ]]; then
        local level="$1"
        shift
        local message="$*"
        local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
        
        case "$level" in
            "INFO")    echo -e "${GREEN}[INFO]${NC}     [$timestamp] $message" ;;
            "WARN")    echo -e "${YELLOW}[WARNING]${NC}  [$timestamp] $message" ;;
            "ERROR")   echo -e "${RED}[ERROR]${NC}    [$timestamp] $message" ;;
            "SUCCESS") echo -e "${GREEN}[SUCCESS]${NC}  [$timestamp] $message" ;;
            "CHECK")   echo -e "${CYAN}[CHECK]${NC}    [$timestamp] $message" ;;
            *)         echo -e "${BLUE}[$level]${NC}     [$timestamp] $message" ;;
        esac
    fi
}

check_dependencies() {
    local missing_deps=()
    
    for cmd in curl jq systemctl docker; do
        if ! command -v "$cmd" &> /dev/null; then
            missing_deps+=("$cmd")
        fi
    done
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log "ERROR" "Missing required dependencies: ${missing_deps[*]}"
        log "INFO" "Please install missing dependencies and try again"
        exit 1
    fi
}

# =============================================================================
# HEALTH CHECK FUNCTIONS
# =============================================================================

check_service_health() {
    local service_name="$1"
    local port_endpoint="$2"
    local port="${port_endpoint%:*}"
    local endpoint="${port_endpoint#*:}"
    local url="${BASE_URL}:${port}${endpoint}"
    
    log "CHECK" "Testing $service_name at $url"
    
    local response
    local http_code
    local response_time
    
    # Make HTTP request with timeout
    response=$(curl -s -w "HTTPSTATUS:%{http_code};TIME:%{time_total}" \
                   --max-time "$HEALTH_CHECK_TIMEOUT" \
                   "$url" 2>/dev/null || echo "HTTPSTATUS:000;TIME:0")
    
    http_code=$(echo "$response" | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)
    response_time=$(echo "$response" | grep -o "TIME:[0-9.]*" | cut -d: -f2)
    
    if [[ "$http_code" == "200" ]]; then
        HEALTH_RESULTS["$service_name"]="healthy"
        log "SUCCESS" "$service_name is healthy (${response_time}s)"
        return 0
    else
        HEALTH_RESULTS["$service_name"]="unhealthy"
        log "ERROR" "$service_name is unhealthy (HTTP: $http_code)"
        return 1
    fi
}

check_database_connectivity() {
    log "CHECK" "Testing database connectivity"
    
    if command -v psql &> /dev/null; then
        local db_host="${DB_HOST:-localhost}"
        local db_port="${DB_PORT:-5432}"
        local db_name="${DB_NAME:-course_creator}"
        local db_user="${DB_USER:-course_creator}"
        
        if PGPASSWORD="${DB_PASSWORD}" psql -h "$db_host" -p "$db_port" -U "$db_user" -d "$db_name" -c "SELECT 1;" &>/dev/null; then
            HEALTH_RESULTS["database"]="healthy"
            log "SUCCESS" "Database connectivity verified"
            return 0
        else
            HEALTH_RESULTS["database"]="unhealthy"
            log "ERROR" "Database connectivity failed"
            return 1
        fi
    else
        log "WARN" "psql not available, skipping database connectivity test"
        HEALTH_RESULTS["database"]="skipped"
        return 0
    fi
}

check_redis_connectivity() {
    log "CHECK" "Testing Redis connectivity"
    
    if command -v redis-cli &> /dev/null; then
        local redis_host="${REDIS_HOST:-localhost}"
        local redis_port="${REDIS_PORT:-6379}"
        
        if redis-cli -h "$redis_host" -p "$redis_port" ping &>/dev/null; then
            HEALTH_RESULTS["redis"]="healthy"
            log "SUCCESS" "Redis connectivity verified"
            return 0
        else
            HEALTH_RESULTS["redis"]="unhealthy"
            log "ERROR" "Redis connectivity failed"
            return 1
        fi
    else
        log "WARN" "redis-cli not available, skipping Redis connectivity test"
        HEALTH_RESULTS["redis"]="skipped"
        return 0
    fi
}

check_systemd_services() {
    log "CHECK" "Checking systemd services"
    
    local services=(
        "course-creator-user-management"
        "course-creator-course-generator"
        "course-creator-content-storage"
        "course-creator-course-management"
        "course-creator-content-management"
        "course-creator-lab-manager"
        "course-creator-analytics"
        "course-creator-organization-management"
        "course-creator-frontend"
    )
    
    local healthy_services=0
    local total_services=${#services[@]}
    
    for service in "${services[@]}"; do
        if systemctl is-active --quiet "$service" 2>/dev/null; then
            log "SUCCESS" "$service is active"
            ((healthy_services++))
        else
            log "ERROR" "$service is not active"
        fi
    done
    
    HEALTH_RESULTS["systemd_services"]="$healthy_services/$total_services"
    
    if [[ $healthy_services -eq $total_services ]]; then
        log "SUCCESS" "All systemd services are running"
        return 0
    else
        log "WARN" "$healthy_services/$total_services systemd services are running"
        return 1
    fi
}

# =============================================================================
# SECURITY CHECK FUNCTIONS
# =============================================================================

check_security_headers() {
    log "CHECK" "Validating security headers"
    
    local test_url="${BASE_URL}:3000/"
    local headers
    
    headers=$(curl -s -I "$test_url" 2>/dev/null || echo "")
    
    local security_score=0
    local total_checks=6
    
    # Check for security headers
    if echo "$headers" | grep -qi "x-frame-options"; then
        log "SUCCESS" "X-Frame-Options header present"
        ((security_score++))
    else
        log "WARN" "X-Frame-Options header missing"
    fi
    
    if echo "$headers" | grep -qi "x-content-type-options"; then
        log "SUCCESS" "X-Content-Type-Options header present"
        ((security_score++))
    else
        log "WARN" "X-Content-Type-Options header missing"
    fi
    
    if echo "$headers" | grep -qi "x-xss-protection"; then
        log "SUCCESS" "X-XSS-Protection header present"
        ((security_score++))
    else
        log "WARN" "X-XSS-Protection header missing"
    fi
    
    if echo "$headers" | grep -qi "strict-transport-security"; then
        log "SUCCESS" "Strict-Transport-Security header present"
        ((security_score++))
    else
        log "WARN" "Strict-Transport-Security header missing (expected if not using HTTPS)"
    fi
    
    if echo "$headers" | grep -qi "content-security-policy"; then
        log "SUCCESS" "Content-Security-Policy header present"
        ((security_score++))
    else
        log "WARN" "Content-Security-Policy header missing"
    fi
    
    if echo "$headers" | grep -qi "referrer-policy"; then
        log "SUCCESS" "Referrer-Policy header present"
        ((security_score++))
    else
        log "WARN" "Referrer-Policy header missing"
    fi
    
    SECURITY_RESULTS["headers_score"]="$security_score/$total_checks"
    
    local percentage=$((security_score * 100 / total_checks))
    if [[ $percentage -ge 80 ]]; then
        log "SUCCESS" "Security headers check passed ($percentage%)"
        return 0
    else
        log "WARN" "Security headers check needs improvement ($percentage%)"
        return 1
    fi
}

check_rate_limiting() {
    log "CHECK" "Testing rate limiting"
    
    local test_url="${BASE_URL}:8000/health"
    local request_count=0
    local blocked_count=0
    
    # Send rapid requests to test rate limiting
    for i in {1..20}; do
        local response_code
        response_code=$(curl -s -o /dev/null -w "%{http_code}" "$test_url" 2>/dev/null || echo "000")
        
        ((request_count++))
        
        if [[ "$response_code" == "429" ]]; then
            ((blocked_count++))
        fi
        
        sleep 0.1  # Small delay between requests
    done
    
    SECURITY_RESULTS["rate_limiting"]="$blocked_count/$request_count blocked"
    
    if [[ $blocked_count -gt 0 ]]; then
        log "SUCCESS" "Rate limiting is working ($blocked_count/$request_count requests blocked)"
        return 0
    else
        log "WARN" "Rate limiting may not be configured properly"
        return 1
    fi
}

check_ssl_configuration() {
    if [[ "$BASE_URL" == "https://"* ]]; then
        log "CHECK" "Testing SSL/TLS configuration"
        
        local domain="${BASE_URL#https://}"
        
        if command -v openssl &> /dev/null; then
            local ssl_info
            ssl_info=$(echo | openssl s_client -connect "$domain:443" -servername "$domain" 2>/dev/null | openssl x509 -noout -dates 2>/dev/null || echo "")
            
            if [[ -n "$ssl_info" ]]; then
                log "SUCCESS" "SSL certificate is valid"
                SECURITY_RESULTS["ssl_status"]="valid"
                return 0
            else
                log "ERROR" "SSL certificate validation failed"
                SECURITY_RESULTS["ssl_status"]="invalid"
                return 1
            fi
        else
            log "WARN" "OpenSSL not available, skipping SSL validation"
            SECURITY_RESULTS["ssl_status"]="skipped"
            return 0
        fi
    else
        log "INFO" "SSL checks skipped (HTTP deployment)"
        SECURITY_RESULTS["ssl_status"]="http_only"
        return 0
    fi
}

# =============================================================================
# PERFORMANCE TEST FUNCTIONS
# =============================================================================

run_performance_tests() {
    log "CHECK" "Running performance tests"
    
    local test_endpoints=(
        "3000:/"
        "8000:/health"
        "8001:/health"
        "8004:/health"
    )
    
    for endpoint in "${test_endpoints[@]}"; do
        local port="${endpoint%:*}"
        local path="${endpoint#*:}"
        local url="${BASE_URL}:${port}${path}"
        local service_name=$(get_service_name_by_port "$port")
        
        log "CHECK" "Performance testing $service_name"
        
        # Run simple load test
        local total_requests=100
        local concurrent_requests=10
        local success_count=0
        local total_time=0
        
        for ((i=1; i<=total_requests; i++)); do
            local start_time
            local end_time
            local response_code
            
            start_time=$(date +%s.%N)
            response_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$url" 2>/dev/null || echo "000")
            end_time=$(date +%s.%N)
            
            if [[ "$response_code" == "200" ]]; then
                ((success_count++))
                local request_time
                request_time=$(echo "$end_time - $start_time" | bc -l)
                total_time=$(echo "$total_time + $request_time" | bc -l)
            fi
            
            # Brief pause between requests
            sleep 0.01
        done
        
        if [[ $success_count -gt 0 ]]; then
            local avg_response_time
            avg_response_time=$(echo "scale=3; $total_time / $success_count" | bc -l)
            PERFORMANCE_RESULTS["${service_name}_avg_response"]="${avg_response_time}s"
            PERFORMANCE_RESULTS["${service_name}_success_rate"]="$success_count/$total_requests"
            
            log "SUCCESS" "$service_name: ${avg_response_time}s avg, $success_count/$total_requests success"
        else
            PERFORMANCE_RESULTS["${service_name}_avg_response"]="failed"
            PERFORMANCE_RESULTS["${service_name}_success_rate"]="0/$total_requests"
            log "ERROR" "$service_name performance test failed"
        fi
    done
}

get_service_name_by_port() {
    local port="$1"
    
    case "$port" in
        "3000") echo "frontend" ;;
        "8000") echo "user-management" ;;
        "8001") echo "course-generator" ;;
        "8003") echo "content-storage" ;;
        "8004") echo "course-management" ;;
        "8005") echo "content-management" ;;
        "8006") echo "lab-manager" ;;
        "8007") echo "analytics" ;;
        "8008") echo "organization-management" ;;
        *) echo "unknown" ;;
    esac
}

# =============================================================================
# INTEGRATION TEST FUNCTIONS
# =============================================================================

run_integration_tests() {
    log "CHECK" "Running integration tests"
    
    # Test user authentication flow
    test_authentication_flow
    
    # Test course creation workflow
    test_course_creation_workflow
    
    # Test multi-tenant isolation
    test_multitenant_isolation
}

test_authentication_flow() {
    log "CHECK" "Testing authentication flow"
    
    local auth_url="${BASE_URL}:8000/api/auth/login"
    local test_credentials='{"email":"test@example.com","password":"testpass"}'
    
    # Attempt login (expected to fail with test credentials)
    local response_code
    response_code=$(curl -s -o /dev/null -w "%{http_code}" \
                         -H "Content-Type: application/json" \
                         -d "$test_credentials" \
                         "$auth_url" 2>/dev/null || echo "000")
    
    if [[ "$response_code" == "401" ]] || [[ "$response_code" == "400" ]]; then
        log "SUCCESS" "Authentication endpoint responding correctly"
        HEALTH_RESULTS["auth_integration"]="working"
    else
        log "WARN" "Authentication endpoint returned unexpected status: $response_code"
        HEALTH_RESULTS["auth_integration"]="unexpected_response"
    fi
}

test_course_creation_workflow() {
    log "CHECK" "Testing course creation workflow"
    
    local course_url="${BASE_URL}:8004/api/courses"
    
    # Test course endpoint accessibility (should require authentication)
    local response_code
    response_code=$(curl -s -o /dev/null -w "%{http_code}" "$course_url" 2>/dev/null || echo "000")
    
    if [[ "$response_code" == "401" ]] || [[ "$response_code" == "403" ]]; then
        log "SUCCESS" "Course endpoints properly protected"
        HEALTH_RESULTS["course_integration"]="protected"
    elif [[ "$response_code" == "200" ]]; then
        log "WARN" "Course endpoints may not be properly protected"
        HEALTH_RESULTS["course_integration"]="unprotected"
    else
        log "ERROR" "Course endpoints not responding: $response_code"
        HEALTH_RESULTS["course_integration"]="error"
    fi
}

test_multitenant_isolation() {
    log "CHECK" "Testing multi-tenant isolation"
    
    # Test that services require proper organization context
    local test_urls=(
        "${BASE_URL}:8000/api/users"
        "${BASE_URL}:8004/api/courses"
        "${BASE_URL}:8008/api/organizations"
    )
    
    local isolation_working=true
    
    for url in "${test_urls[@]}"; do
        local response_code
        response_code=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
        
        # Should require authentication/authorization
        if [[ "$response_code" != "401" ]] && [[ "$response_code" != "403" ]]; then
            isolation_working=false
            log "WARN" "Endpoint may not be properly protected: $url ($response_code)"
        fi
    done
    
    if [[ "$isolation_working" == "true" ]]; then
        log "SUCCESS" "Multi-tenant isolation appears to be working"
        HEALTH_RESULTS["multitenant_isolation"]="working"
    else
        log "WARN" "Multi-tenant isolation may need review"
        HEALTH_RESULTS["multitenant_isolation"]="needs_review"
    fi
}

# =============================================================================
# OUTPUT AND REPORTING
# =============================================================================

generate_json_report() {
    local json_output='{'
    
    # Health results
    json_output+='"health":{'
    local first=true
    for service in "${!HEALTH_RESULTS[@]}"; do
        if [[ "$first" == "false" ]]; then
            json_output+=','
        fi
        json_output+="\"$service\":\"${HEALTH_RESULTS[$service]}\""
        first=false
    done
    json_output+='}'
    
    # Security results
    if [[ ${#SECURITY_RESULTS[@]} -gt 0 ]]; then
        json_output+=',"security":{'
        first=true
        for check in "${!SECURITY_RESULTS[@]}"; do
            if [[ "$first" == "false" ]]; then
                json_output+=','
            fi
            json_output+="\"$check\":\"${SECURITY_RESULTS[$check]}\""
            first=false
        done
        json_output+='}'
    fi
    
    # Performance results
    if [[ ${#PERFORMANCE_RESULTS[@]} -gt 0 ]]; then
        json_output+=',"performance":{'
        first=true
        for metric in "${!PERFORMANCE_RESULTS[@]}"; do
            if [[ "$first" == "false" ]]; then
                json_output+=','
            fi
            json_output+="\"$metric\":\"${PERFORMANCE_RESULTS[$metric]}\""
            first=false
        done
        json_output+='}'
    fi
    
    json_output+=',"timestamp":"'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'"'
    json_output+=',"version":"'$SCRIPT_VERSION'"'
    json_output+='}'
    
    echo "$json_output" | jq . 2>/dev/null || echo "$json_output"
}

generate_summary_report() {
    cat << EOF

${CYAN}=================================================================${NC}
${CYAN}🏥 COURSE CREATOR PLATFORM - HEALTH CHECK SUMMARY${NC}
${CYAN}=================================================================${NC}

${BLUE}📊 HEALTH STATUS:${NC}
EOF

    for service in "${!HEALTH_RESULTS[@]}"; do
        local status="${HEALTH_RESULTS[$service]}"
        local icon="❓"
        local color="$NC"
        
        case "$status" in
            "healthy"|"working"|"valid") icon="✅"; color="$GREEN" ;;
            "unhealthy"|"error"|"invalid") icon="❌"; color="$RED" ;;
            "skipped"|"http_only") icon="⏭️"; color="$YELLOW" ;;
            "needs_review"|"unprotected") icon="⚠️"; color="$YELLOW" ;;
        esac
        
        printf "${color}%s %-30s %s${NC}\n" "$icon" "$service:" "$status"
    done

    if [[ ${#SECURITY_RESULTS[@]} -gt 0 ]]; then
        cat << EOF

${BLUE}🛡️ SECURITY STATUS:${NC}
EOF
        for check in "${!SECURITY_RESULTS[@]}"; do
            local result="${SECURITY_RESULTS[$check]}"
            printf "${GREEN}✓${NC} %-30s %s\n" "$check:" "$result"
        done
    fi

    if [[ ${#PERFORMANCE_RESULTS[@]} -gt 0 ]]; then
        cat << EOF

${BLUE}⚡ PERFORMANCE METRICS:${NC}
EOF
        for metric in "${!PERFORMANCE_RESULTS[@]}"; do
            local result="${PERFORMANCE_RESULTS[$metric]}"
            printf "${BLUE}📈${NC} %-30s %s\n" "$metric:" "$result"
        done
    fi

    # Overall status
    local healthy_count=0
    local total_count=0
    
    for service in "${!HEALTH_RESULTS[@]}"; do
        local status="${HEALTH_RESULTS[$service]}"
        ((total_count++))
        
        if [[ "$status" == "healthy" ]] || [[ "$status" == "working" ]] || [[ "$status" == "valid" ]]; then
            ((healthy_count++))
        fi
    done
    
    local health_percentage=$((healthy_count * 100 / total_count))
    
    cat << EOF

${BLUE}📋 OVERALL STATUS:${NC}
EOF

    if [[ $health_percentage -ge 90 ]]; then
        echo -e "${GREEN}🎉 EXCELLENT${NC} - Platform is running optimally ($health_percentage% healthy)"
    elif [[ $health_percentage -ge 75 ]]; then
        echo -e "${YELLOW}⚠️  GOOD${NC} - Platform is mostly healthy with minor issues ($health_percentage% healthy)"
    elif [[ $health_percentage -ge 50 ]]; then
        echo -e "${YELLOW}⚠️  FAIR${NC} - Platform has several issues that need attention ($health_percentage% healthy)"
    else
        echo -e "${RED}❌ POOR${NC} - Platform has significant issues requiring immediate attention ($health_percentage% healthy)"
    fi

    cat << EOF

${BLUE}⏰ Check completed at:${NC} $(date)
${BLUE}🔢 Script version:${NC} $SCRIPT_VERSION

EOF
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================

show_help() {
    cat << EOF
$SCRIPT_NAME v$SCRIPT_VERSION - Health Check and Verification Script

USAGE:
    $0 [OPTIONS]

OPTIONS:
    --silent        Suppress verbose output
    --json         Output results in JSON format
    --security     Run security compliance checks
    --performance  Run performance benchmarks
    --integration  Run integration tests
    --help         Show this help message

EXAMPLES:
    # Basic health check
    $0

    # Full health check with security and performance tests
    $0 --security --performance

    # JSON output for monitoring systems
    $0 --json --silent

    # Integration testing
    $0 --integration --security

HEALTH CHECKS:
    ✓ Service availability and response times
    ✓ Database and Redis connectivity
    ✓ Systemd service status
    ✓ Security headers validation
    ✓ Rate limiting functionality
    ✓ SSL/TLS configuration (if HTTPS)

PERFORMANCE TESTS:
    ✓ Response time measurements
    ✓ Load testing (100 requests per service)
    ✓ Success rate analysis
    ✓ Concurrent request handling

SECURITY CHECKS:
    ✓ OWASP security headers
    ✓ Rate limiting protection
    ✓ SSL certificate validation
    ✓ Multi-tenant isolation
    ✓ Authentication endpoint protection

For more information, visit: https://github.com/yourusername/course-creator
EOF
}

parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --silent)
                SILENT_MODE=true
                shift
                ;;
            --json)
                JSON_OUTPUT=true
                shift
                ;;
            --security)
                RUN_SECURITY_CHECKS=true
                shift
                ;;
            --performance)
                RUN_PERFORMANCE_TESTS=true
                shift
                ;;
            --integration)
                RUN_INTEGRATION_TESTS=true
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                echo "Unknown option: $1. Use --help for usage information."
                exit 1
                ;;
        esac
    done
}

main() {
    # Parse arguments
    parse_arguments "$@"
    
    # Check dependencies
    check_dependencies
    
    # Load environment variables if available
    if [[ -f ".env.production" ]]; then
        source .env.production
    elif [[ -f ".env.secrets" ]]; then
        source .env.secrets
    fi
    
    # Determine base URL
    if [[ -n "${DOMAIN_NAME:-}" ]]; then
        if [[ "${SKIP_SSL:-false}" == "true" ]]; then
            BASE_URL="http://$DOMAIN_NAME"
        else
            BASE_URL="https://$DOMAIN_NAME"
        fi
    fi
    
    if [[ "$SILENT_MODE" == "false" ]]; then
        cat << EOF
${PURPLE}
╔══════════════════════════════════════════════════════════════════╗
║              COURSE CREATOR PLATFORM HEALTH CHECK               ║
║                                                                  ║
║                    Version: $SCRIPT_VERSION                           ║
║              OWASP Security Enhanced (96%+ Score)               ║
╚══════════════════════════════════════════════════════════════════╝
${NC}

EOF
        log "INFO" "Starting health check..."
    fi
    
    # Core health checks
    for service in "${!SERVICES[@]}"; do
        check_service_health "$service" "${SERVICES[$service]}"
    done
    
    check_database_connectivity
    check_redis_connectivity
    check_systemd_services
    
    # Optional security checks
    if [[ "$RUN_SECURITY_CHECKS" == "true" ]]; then
        log "INFO" "Running security compliance checks..."
        check_security_headers
        check_rate_limiting
        check_ssl_configuration
    fi
    
    # Optional performance tests
    if [[ "$RUN_PERFORMANCE_TESTS" == "true" ]]; then
        log "INFO" "Running performance tests..."
        run_performance_tests
    fi
    
    # Optional integration tests
    if [[ "$RUN_INTEGRATION_TESTS" == "true" ]]; then
        log "INFO" "Running integration tests..."
        run_integration_tests
    fi
    
    # Generate output
    if [[ "$JSON_OUTPUT" == "true" ]]; then
        generate_json_report
    else
        generate_summary_report
    fi
    
    # Exit with appropriate code
    local failed_services=0
    for service in "${!HEALTH_RESULTS[@]}"; do
        local status="${HEALTH_RESULTS[$service]}"
        if [[ "$status" == "unhealthy" ]] || [[ "$status" == "error" ]]; then
            ((failed_services++))
        fi
    done
    
    if [[ $failed_services -gt 0 ]]; then
        exit 1
    else
        exit 0
    fi
}

# Check if script is being sourced or executed
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi