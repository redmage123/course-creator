# Observability Quick Reference Card

## 🚀 Quick Start

```bash
# Start monitoring
docker-compose up -d prometheus grafana

# Verify
python3 monitoring/verify_observability.py

# Access
open http://localhost:9090  # Prometheus
open http://localhost:3002  # Grafana (admin/admin)
```

## 📊 Service Ports

| Service | Port | Protocol |
|---------|------|----------|
| Prometheus | 9090 | HTTP |
| Grafana | 3002 | HTTP |
| All microservices | 8000-8016 | HTTPS/HTTP |

## 📝 Code Snippets

### Setup Logging
```python
from shared.observability import setup_logging, get_logger

setup_logging(service_name="my-service", log_level="INFO")
logger = get_logger(__name__)
```

### Log with Context
```python
logger.info("User created", extra={
    'extra_fields': {'user_id': 123, 'email': 'user@example.com'}
})
```

### Track Operations
```python
from shared.observability import track_operation

with track_operation("database_query", extra_fields={'table': 'users'}):
    result = db.query("SELECT * FROM users")
```

### Add Metrics Endpoint
```python
from prometheus_client import Counter, generate_latest
from fastapi import Response

REQUEST_COUNT = Counter('http_requests_total', 'Total requests', ['method', 'status'])

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type="text/plain")
```

### Track Requests
```python
REQUEST_COUNT.labels(method="GET", status=200).inc()
```

## 🔍 Useful Commands

### Docker
```bash
# Service status
docker-compose ps prometheus grafana

# Logs
docker-compose logs -f prometheus
docker-compose logs -f grafana

# Restart
docker-compose restart prometheus grafana
```

### Testing
```bash
# Test metrics endpoint
curl -k https://localhost:8000/metrics

# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# View logs
tail -f /var/log/course-creator/user-management.log | jq '.'
```

## 📈 PromQL Queries

```promql
# Service health
up{service="user-management"}

# Request rate (per second)
rate(http_requests_total[5m])

# P95 latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Error rate
rate(http_requests_total{status=~"5.."}[5m])

# Memory usage (MB)
process_resident_memory_bytes / 1024 / 1024

# CPU usage (%)
rate(process_cpu_seconds_total[5m]) * 100
```

## 🏥 Health Checks

### Prometheus
- Targets: http://localhost:9090/targets
- Health: http://localhost:9090/-/healthy
- API: http://localhost:9090/api/v1/query?query=up

### Grafana
- Health: http://localhost:3002/api/health
- Login: http://localhost:3002 (admin/admin)
- Dashboards: http://localhost:3002/dashboards

### Services
```bash
# Check service health
curl -k https://localhost:8000/health

# Check service metrics
curl -k https://localhost:8000/metrics
```

## 🔧 Troubleshooting

### Prometheus Not Scraping
1. Check target: http://localhost:9090/targets
2. Verify service: `docker-compose ps`
3. Test endpoint: `curl -k https://localhost:8000/metrics`
4. Check logs: `docker-compose logs prometheus`

### Grafana Dashboard Not Loading
1. Test datasource: Configuration → Data Sources → Test
2. Verify query: Run in Prometheus first
3. Check time range: Top-right corner
4. Review logs: `docker-compose logs grafana`

### Missing Logs
1. Check directory: `ls -la /var/log/course-creator/`
2. Verify permissions: `ls -la /var/log/`
3. Check setup: Verify `setup_logging()` is called
4. Review startup: `docker-compose logs your-service`

## 📚 Documentation

- **Full Guide**: [monitoring/README.md](README.md)
- **Quick Start**: [monitoring/QUICKSTART.md](QUICKSTART.md)
- **Example Code**: [monitoring/examples/service_integration.py](examples/service_integration.py)
- **Verification**: `python3 monitoring/verify_observability.py`

## 🎯 Common Tasks

### View Dashboard
1. Open http://localhost:3002
2. Login: admin/admin
3. Dashboards → Browse → Platform Overview

### Create Alert
1. Open Grafana
2. Alerting → Alert rules → New alert rule
3. Configure query and conditions
4. Set notification channel

### Export Dashboard
1. Open dashboard
2. Dashboard settings → JSON Model
3. Copy JSON
4. Save to `monitoring/grafana/dashboards/`

### View Service Logs
```bash
# Raw logs
tail -f /var/log/course-creator/service-name.log

# Parsed JSON
tail -f /var/log/course-creator/service-name.log | jq '.'

# Filter errors
tail -f /var/log/course-creator/service-name.log | jq 'select(.level=="ERROR")'

# Follow correlation
tail -f /var/log/course-creator/service-name.log | jq 'select(.correlation_id=="abc-123")'
```

## 🔐 Default Credentials

- **Grafana**: admin / admin (change on first login)
- **Prometheus**: No authentication (configure in production)

## 📞 Support

1. Check [QUICKSTART.md](QUICKSTART.md)
2. Review [README.md](README.md)
3. Run verification: `python3 monitoring/verify_observability.py`
4. Check logs: `docker-compose logs <service>`
5. Consult [/home/bbrelin/course-creator/CLAUDE.md](../CLAUDE.md)
