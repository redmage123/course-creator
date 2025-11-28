# Course Creator Platform Observability

This directory contains the observability infrastructure for the Course Creator Platform, including monitoring, logging, and metrics collection configurations.

## Components

### Prometheus (Port 9090)
- **Purpose**: Metrics collection and time-series database
- **Access**: http://localhost:9090
- **Configuration**: `prometheus.yml`
- **Retention**: 30 days
- **Scrape Interval**: 15 seconds

### Grafana (Port 3002)
- **Purpose**: Metrics visualization and dashboarding
- **Access**: http://localhost:3002
- **Default Credentials**:
  - Username: `admin`
  - Password: `admin` (change on first login)
- **Dashboards**: Pre-configured platform overview dashboard

### Structured Logging
- **Location**: `/home/bbrelin/course-creator/shared/observability.py`
- **Features**:
  - JSON-formatted logs
  - Correlation ID tracking
  - Request tracing
  - Performance timing
  - Log rotation (100MB per file, 10 backups)

## Quick Start

### Starting Monitoring Services

```bash
# Start all services including monitoring
docker-compose up -d prometheus grafana

# Check service health
docker-compose ps prometheus grafana

# View Prometheus logs
docker-compose logs -f prometheus

# View Grafana logs
docker-compose logs -f grafana
```

### Accessing Dashboards

1. **Prometheus UI**: http://localhost:9090
   - View raw metrics
   - Run PromQL queries
   - Check service targets
   - View alerts (when configured)

2. **Grafana UI**: http://localhost:3002
   - Login with admin/admin
   - Navigate to "Dashboards"
   - Open "Course Creator Platform Overview"

## Service Metrics

### Monitored Services

All 16 microservices are configured for metrics collection:

| Service | Port | Protocol | Type |
|---------|------|----------|------|
| user-management | 8000 | HTTPS | Core |
| course-generator | 8001 | HTTPS | AI |
| content-storage | 8003 | HTTPS | Storage |
| course-management | 8004 | HTTPS | Core |
| content-management | 8005 | HTTPS | Core |
| lab-manager | 8006 | HTTPS | Labs |
| analytics | 8007 | HTTPS | Analytics |
| organization-management | 8008 | HTTPS | Core |
| rag-service | 8009 | HTTPS | AI |
| demo-service | 8010 | HTTPS | Demo |
| ai-assistant-service | 8011 | HTTP | AI |
| knowledge-graph-service | 8012 | HTTPS | AI |
| nlp-preprocessing | 8013 | HTTPS | AI |
| metadata-service | 8014 | HTTPS | Metadata |
| local-llm-service | 8015 | HTTP | AI |
| nimcp-service | 8016 | HTTP | AI |

### Standard Metrics

Each service should expose these standard metrics:

- `http_requests_total` - Total HTTP requests by method, path, status
- `http_request_duration_seconds` - Request duration histogram
- `http_requests_in_flight` - Current in-flight requests
- `process_cpu_seconds_total` - CPU usage
- `process_resident_memory_bytes` - Memory usage
- `process_open_fds` - Open file descriptors

## Using Structured Logging

### Setup in Your Service

```python
from shared.observability import setup_logging, get_logger, track_operation

# At application startup
setup_logging(
    service_name="your-service-name",
    log_level="INFO",
    enable_console=True,
    enable_json=True
)

# In your modules
logger = get_logger(__name__)

# Basic logging
logger.info("User created", extra={'extra_fields': {'user_id': user_id}})

# Track operations with timing
with track_operation("database_query", extra_fields={"table": "users"}):
    result = db.query("SELECT * FROM users")

# HTTP request logging
from shared.observability import log_request

log_request(
    logger,
    method="POST",
    path="/api/v1/users",
    status_code=201,
    duration=0.125,
    user_id=42
)
```

### Log Fields

Standard structured log format:

```json
{
  "timestamp": "2025-11-27T10:30:45.123Z",
  "level": "INFO",
  "logger": "user_management.api",
  "message": "User created successfully",
  "service": "user-management",
  "environment": "docker",
  "hostname": "abc123",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": 42,
  "organization_id": 1,
  "location": {
    "file": "/app/api/endpoints.py",
    "line": 123,
    "function": "create_user"
  },
  "data": {
    "email": "user@example.com",
    "role": "student"
  }
}
```

## Prometheus Queries

### Useful PromQL Examples

```promql
# Service uptime
up{service="user-management"}

# Request rate per service
rate(http_requests_total[5m])

# P95 request latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Error rate
rate(http_requests_total{status=~"5.."}[5m])

# Memory usage by service
process_resident_memory_bytes / 1024 / 1024

# CPU usage by service
rate(process_cpu_seconds_total[5m])
```

## Adding Metrics to Services

### Step 1: Install prometheus_client

```bash
pip install prometheus-client
```

### Step 2: Add Metrics Endpoint

```python
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import Response

# Define metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

# Add /metrics endpoint
@app.get("/metrics")
async def metrics():
    return Response(
        content=generate_latest(),
        media_type="text/plain"
    )

# Use in middleware
@app.middleware("http")
async def track_requests(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()

    REQUEST_DURATION.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)

    return response
```

## Grafana Dashboard Management

### Creating Custom Dashboards

1. Navigate to http://localhost:3002
2. Click "+" → "Dashboard"
3. Add panels with Prometheus queries
4. Save dashboard
5. Export JSON: Dashboard settings → JSON Model
6. Save to `monitoring/grafana/dashboards/`

### Dashboard Variables

Use Grafana variables for dynamic filtering:

- `$service` - Filter by service name
- `$method` - Filter by HTTP method
- `$status_code` - Filter by status code
- `$time_range` - Adjust time window

## Alerting (Future Enhancement)

To add alerting:

1. Create alert rules in `monitoring/alerts/`
2. Configure Alertmanager
3. Add notification channels (Slack, email, PagerDuty)
4. Define alert thresholds and conditions

Example alert rule:

```yaml
groups:
  - name: course_creator_alerts
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate on {{ $labels.service }}"
          description: "{{ $labels.service }} has error rate above 5%"
```

## Log Aggregation (Future Enhancement)

For centralized log management, consider adding:

- **ELK Stack** (Elasticsearch, Logstash, Kibana)
- **Loki** (Grafana's log aggregation system)
- **Fluentd** for log forwarding

## Troubleshooting

### Prometheus Not Scraping Services

1. Check service health:
   ```bash
   curl -k https://localhost:8000/health
   ```

2. Verify service exposes /metrics endpoint:
   ```bash
   curl -k https://localhost:8000/metrics
   ```

3. Check Prometheus targets: http://localhost:9090/targets

4. Review Prometheus logs:
   ```bash
   docker-compose logs prometheus
   ```

### Grafana Dashboard Not Loading

1. Verify Prometheus datasource: Configuration → Data Sources
2. Test connection to Prometheus
3. Check dashboard JSON syntax
4. Review Grafana logs:
   ```bash
   docker-compose logs grafana
   ```

### Missing Logs

1. Check log directory permissions:
   ```bash
   ls -la /var/log/course-creator/
   ```

2. Verify service has LOG_DIR environment variable
3. Check disk space:
   ```bash
   df -h
   ```

## Best Practices

1. **Metrics**:
   - Use consistent naming (snake_case)
   - Add meaningful labels
   - Don't over-instrument (high cardinality issues)
   - Monitor collection latency

2. **Logging**:
   - Use structured logging (JSON)
   - Include correlation IDs
   - Log at appropriate levels
   - Don't log sensitive data (passwords, tokens)
   - Use log rotation

3. **Dashboards**:
   - Create role-specific views (dev, ops, business)
   - Use consistent time ranges
   - Add context with annotations
   - Document dashboard variables

4. **Performance**:
   - Keep scrape intervals reasonable (15-60s)
   - Use recording rules for expensive queries
   - Monitor monitoring system resource usage
   - Archive old data periodically

## Additional Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [PromQL Tutorial](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Structured Logging Best Practices](https://www.structuredlogging.io/)
- [Python Logging Cookbook](https://docs.python.org/3/howto/logging-cookbook.html)

## Support

For issues or questions:
1. Check service logs: `docker-compose logs <service-name>`
2. Review Prometheus targets: http://localhost:9090/targets
3. Test metrics endpoint manually: `curl -k https://localhost:<port>/metrics`
4. Consult platform documentation: `/home/bbrelin/course-creator/CLAUDE.md`
