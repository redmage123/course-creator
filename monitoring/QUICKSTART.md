# Observability Quick Start Guide

This guide gets you up and running with the Course Creator Platform's observability infrastructure in minutes.

## Prerequisites

- Docker and Docker Compose installed
- Course Creator Platform environment set up
- Basic familiarity with Prometheus and Grafana (helpful but not required)

## 1. Verify Setup

```bash
# From the course-creator root directory
python3 monitoring/verify_observability.py
```

Expected output: All checks should pass with ✅

## 2. Start Monitoring Services

```bash
# Start Prometheus and Grafana
docker-compose up -d prometheus grafana

# Verify services are running
docker-compose ps prometheus grafana

# Check logs
docker-compose logs -f prometheus grafana
```

## 3. Access Dashboards

### Prometheus UI
- URL: http://localhost:9090
- No authentication required
- Use to:
  - View raw metrics
  - Run PromQL queries
  - Check service health: http://localhost:9090/targets
  - Test queries: http://localhost:9090/graph

### Grafana UI
- URL: http://localhost:3002
- Default credentials:
  - Username: `admin`
  - Password: `admin` (you'll be prompted to change this)
- Use to:
  - View pre-built dashboards
  - Create custom visualizations
  - Set up alerts
  - Share dashboards with team

## 4. Quick Health Check

### Check Prometheus is Scraping Services

1. Open http://localhost:9090/targets
2. Look for your services in the list
3. Status should be "UP" (green)

If services show "DOWN":
- Verify services are running: `docker-compose ps`
- Check service exposes /metrics endpoint: `curl -k https://localhost:8000/metrics`
- Review Prometheus logs: `docker-compose logs prometheus`

### View Your First Dashboard

1. Open http://localhost:3002
2. Login with admin/admin
3. Navigate to Dashboards → Browse
4. Open "Course Creator Platform Overview"
5. You should see:
   - Service health gauges
   - Request rate graphs
   - Request duration charts
   - Service distribution pie chart

## 5. Add Observability to a Service

### Method 1: Using the Example (Recommended)

```bash
# Copy the example integration to your service
cp monitoring/examples/service_integration.py services/your-service/

# Review and adapt to your needs
# Key sections:
# - STEP 1: Define metrics
# - STEP 2: Setup logging
# - STEP 3: Add /metrics endpoint
# - STEP 4: Add middleware
# - STEP 5: Use in endpoints
```

### Method 2: Manual Integration

Add to your service's `main.py`:

```python
from shared.observability import setup_logging, get_logger, track_operation

# At startup
setup_logging(
    service_name="your-service",
    log_level="INFO"
)

# In your code
logger = get_logger(__name__)

# Basic logging
logger.info("User created", extra={'extra_fields': {'user_id': 123}})

# Track operations
with track_operation("database_query"):
    result = db.query("SELECT * FROM users")
```

### Add Prometheus Metrics

```python
from prometheus_client import Counter, Histogram, generate_latest
from fastapi import Response

# Define metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total requests',
    ['service', 'method', 'endpoint', 'status']
)

# Add /metrics endpoint
@app.get("/metrics")
async def metrics():
    return Response(
        content=generate_latest(),
        media_type="text/plain"
    )

# Use in code
REQUEST_COUNT.labels(
    service="your-service",
    method="GET",
    endpoint="/users",
    status=200
).inc()
```

## 6. Verify Your Service is Being Monitored

```bash
# 1. Check your service exposes metrics
curl -k https://localhost:YOUR_PORT/metrics

# 2. Verify Prometheus is scraping it
# Open http://localhost:9090/targets
# Find your service in the list

# 3. Query your metrics in Prometheus
# Open http://localhost:9090/graph
# Enter: up{service="your-service"}
# Click "Execute"

# 4. View logs
tail -f /var/log/course-creator/your-service.log
```

## 7. Common PromQL Queries

### Service Health
```promql
# Is my service up?
up{service="user-management"}

# How many services are up?
count(up == 1)
```

### Request Metrics
```promql
# Request rate (requests per second)
rate(http_requests_total{service="user-management"}[5m])

# Request rate by endpoint
sum by (endpoint) (rate(http_requests_total[5m]))

# Error rate (5xx errors)
rate(http_requests_total{status_code=~"5.."}[5m])
```

### Performance Metrics
```promql
# P95 request latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Average request duration
rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])
```

### Resource Metrics
```promql
# Memory usage (MB)
process_resident_memory_bytes / 1024 / 1024

# CPU usage (percentage)
rate(process_cpu_seconds_total[5m]) * 100
```

## 8. Create Custom Dashboards

1. Open Grafana: http://localhost:3002
2. Click "+" → "Dashboard"
3. Click "Add visualization"
4. Select "Prometheus" datasource
5. Enter a PromQL query (e.g., `rate(http_requests_total[5m])`)
6. Customize visualization type (graph, gauge, table, etc.)
7. Click "Apply"
8. Add more panels as needed
9. Click "Save dashboard"
10. Export JSON: Dashboard settings → JSON Model
11. Save to `monitoring/grafana/dashboards/your-dashboard.json`

## 9. View Structured Logs

### Option 1: View Raw Logs
```bash
# View service logs
tail -f /var/log/course-creator/your-service.log

# Parse JSON logs with jq
tail -f /var/log/course-creator/your-service.log | jq '.'

# Filter by level
tail -f /var/log/course-creator/your-service.log | jq 'select(.level=="ERROR")'

# Filter by correlation ID
tail -f /var/log/course-creator/your-service.log | jq 'select(.correlation_id=="abc-123")'
```

### Option 2: Docker Logs
```bash
# View container logs
docker-compose logs -f your-service

# Follow logs from all services
docker-compose logs -f

# Filter by keyword
docker-compose logs -f | grep ERROR
```

## 10. Troubleshooting

### Prometheus Not Scraping Services

**Problem**: Services show as "DOWN" in Prometheus targets

**Solutions**:
1. Verify service is running: `docker-compose ps`
2. Check service health: `curl -k https://localhost:PORT/health`
3. Test metrics endpoint: `curl -k https://localhost:PORT/metrics`
4. Check Prometheus config: `cat monitoring/prometheus.yml`
5. Review Prometheus logs: `docker-compose logs prometheus`
6. Restart Prometheus: `docker-compose restart prometheus`

### Grafana Dashboard Not Loading

**Problem**: Dashboard shows "No data" or fails to load

**Solutions**:
1. Verify Prometheus datasource:
   - Go to Configuration → Data Sources
   - Click "Prometheus"
   - Click "Test" button
   - Should show "Data source is working"
2. Check PromQL query syntax in panel edit mode
3. Verify time range (top-right corner)
4. Check if metrics exist: Query in Prometheus first
5. Review Grafana logs: `docker-compose logs grafana`

### Missing Logs

**Problem**: Service logs not appearing in log files

**Solutions**:
1. Check log directory exists: `ls -la /var/log/course-creator/`
2. Verify directory permissions: `ls -la /var/log/`
3. Check service has LOG_DIR env var: `docker-compose config | grep LOG_DIR`
4. Review service startup logs: `docker-compose logs your-service | head -50`
5. Verify observability module is imported and setup_logging() is called

### High Memory Usage

**Problem**: Prometheus or Grafana consuming too much memory

**Solutions**:
1. Reduce retention time in `prometheus.yml` (default: 30d)
2. Increase scrape interval (default: 15s)
3. Limit stored metrics using relabeling
4. Archive old data and restart services
5. Monitor resource usage: `docker stats`

## 11. Production Readiness Checklist

Before deploying to production:

- [ ] Change Grafana admin password from default
- [ ] Configure secure authentication (OAuth, LDAP, etc.)
- [ ] Set up persistent storage for metrics and dashboards
- [ ] Configure backup strategy for Grafana dashboards
- [ ] Set up alerting rules and notification channels
- [ ] Enable HTTPS for Grafana and Prometheus
- [ ] Implement access control and RBAC
- [ ] Configure log retention and rotation policies
- [ ] Set up log aggregation (ELK, Loki, etc.)
- [ ] Document custom dashboards and alerts
- [ ] Train team on dashboard usage and alert response
- [ ] Test disaster recovery procedures
- [ ] Monitor the monitoring (meta-monitoring)

## 12. Additional Resources

### Documentation
- [Monitoring README](README.md) - Comprehensive documentation
- [Example Integration](examples/service_integration.py) - Complete service example
- [Prometheus Docs](https://prometheus.io/docs/)
- [Grafana Docs](https://grafana.com/docs/)
- [PromQL Guide](https://prometheus.io/docs/prometheus/latest/querying/basics/)

### Useful Commands
```bash
# Restart monitoring services
docker-compose restart prometheus grafana

# View all metrics from a service
curl -k https://localhost:8000/metrics

# Query Prometheus API
curl 'http://localhost:9090/api/v1/query?query=up'

# Reload Prometheus config without restart
curl -X POST http://localhost:9090/-/reload

# Backup Grafana dashboards
docker-compose exec grafana grafana-cli admin export-dashboards

# View resource usage
docker stats prometheus grafana
```

## Getting Help

If you encounter issues:

1. Check this quickstart guide
2. Review [monitoring/README.md](README.md)
3. Search Prometheus/Grafana documentation
4. Check service logs: `docker-compose logs <service-name>`
5. Consult platform documentation: `/home/bbrelin/course-creator/CLAUDE.md`

## Next Steps

Once observability is working:

1. **Add Alerting**: Configure alerts for critical metrics
2. **Create Dashboards**: Build role-specific dashboards (dev, ops, business)
3. **Instrument Code**: Add custom metrics for business logic
4. **Log Aggregation**: Set up centralized log management
5. **Distributed Tracing**: Implement full request tracing across services
6. **Performance Tuning**: Use metrics to identify bottlenecks
7. **Capacity Planning**: Use historical data for resource forecasting

Happy monitoring! 📊📈
