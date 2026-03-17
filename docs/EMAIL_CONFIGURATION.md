# Email Configuration Guide

This document explains how to configure the email service for the Course Creator platform using Hydra configuration management.

## Configuration Overview

The email service is now configured through Hydra configuration files (`conf/config.yaml`) with environment variable support. This provides a centralized, type-safe configuration approach that follows the platform's architecture.

## Hydra Configuration Structure

The email configuration is located in the `email` section of `services/course-management/conf/config.yaml`:

```yaml
email:
  from_address: ${oc.env:EMAIL_FROM_ADDRESS,"noreply@courseplatform.com"}
  smtp:
    server: ${oc.env:SMTP_SERVER,"localhost"}
    port: ${oc.env:SMTP_PORT,587}
    user: ${oc.env:SMTP_USER,null}
    password: ${oc.env:SMTP_PASSWORD,null}
    use_tls: ${oc.env:SMTP_USE_TLS,true}
  use_mock: ${oc.env:USE_MOCK_EMAIL,false}
```

## Environment Variables

Configuration values can be overridden using environment variables:

### SMTP Server Configuration

| Environment Variable | Description | Default | Example |
|---------------------|-------------|---------|---------|
| `EMAIL_FROM_ADDRESS` | Sender email address | `noreply@courseplatform.com` | `courses@university.edu` |
| `EMAIL_SENDER` | Alternative sender address | (none) | `notifications@training.com` |
| `SMTP_SERVER` | SMTP server hostname | `localhost` | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP server port | `587` | `587` or `465` |
| `SMTP_USER` | SMTP authentication username | (none) | `your-email@domain.com` |
| `SMTP_PASSWORD` | SMTP authentication password | (none) | `your-app-password` |
| `SMTP_USE_TLS` | Enable TLS encryption | `true` | `true` or `false` |
| `USE_MOCK_EMAIL` | Use mock email service for testing | `false` | `true` or `false` |

## Configuration Examples

### Production SMTP Configuration

```bash
# Sender address (students will see this as "From")
export EMAIL_FROM_ADDRESS="courses@university.edu"

# SMTP server settings
export SMTP_SERVER="smtp.university.edu"
export SMTP_PORT="587"
export SMTP_USER="courses@university.edu"
export SMTP_PASSWORD="your-smtp-password"
export SMTP_USE_TLS="true"

# Disable mock email for production
export USE_MOCK_EMAIL="false"
```

### Gmail Configuration

```bash
# Sender address
export EMAIL_FROM_ADDRESS="your-course-platform@gmail.com"

# Gmail SMTP settings
export SMTP_SERVER="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_USER="your-course-platform@gmail.com"
export SMTP_PASSWORD="your-app-password"  # Use Gmail App Password
export SMTP_USE_TLS="true"
```

### Development Configuration

```bash
# Use mock email service for development/testing
export USE_MOCK_EMAIL="true"
export EMAIL_FROM_ADDRESS="dev-courses@localhost"
```

### Custom Organization Configuration

```bash
# Custom organization sender
export EMAIL_FROM_ADDRESS="training@techcorp.com"
export SMTP_SERVER="mail.techcorp.com"
export SMTP_PORT="587"
export SMTP_USER="training@techcorp.com"
export SMTP_PASSWORD="secure-password"
export SMTP_USE_TLS="true"
```

## Email Templates

The system sends the following types of emails with the configured sender address:

1. **Enrollment Confirmation** - When students are enrolled in courses
2. **Course Reminders** - Before course start dates
3. **Course Completion** - When courses are completed

### Email Example

```
From: courses@university.edu
To: student@example.com
Subject: Welcome to Python Programming Fundamentals - Course Enrollment Confirmation

Dear Alice Johnson,

You have been enrolled in the course "Python Programming Fundamentals" (Fall 2025 Session).

[... course details ...]

Best regards,
Dr. Jane Smith
Computer Science Department
Tech University
```

## Security Considerations

### SMTP Authentication

- Always use secure passwords or app-specific passwords
- Enable TLS encryption (`SMTP_USE_TLS=true`)
- Use port 587 (STARTTLS) or 465 (SSL/TLS) for encrypted connections

### Sender Address Best Practices

- Use a dedicated email address for course notifications
- Ensure the sender address is from the same domain as your SMTP server
- Consider using descriptive addresses like `courses@`, `training@`, or `notifications@`
- Avoid using personal email addresses for automated notifications

### Environment Variable Security

- Store sensitive environment variables securely
- Use `.env` files for local development (never commit to git)
- Use secure secret management systems in production
- Rotate SMTP passwords regularly

## Testing Email Configuration

### Mock Email Service

For development and testing, enable the mock email service:

```bash
export USE_MOCK_EMAIL="true"
```

This will log email content without actually sending emails.

### Test Configuration

Create a simple test to verify your email configuration:

```python
from email_service import create_email_service
import asyncio

async def test_email_config():
    service = create_email_service(use_mock=False)
    print(f"SMTP Server: {service.smtp_server}:{service.smtp_port}")
    print(f"From Address: {service.from_email}")
    print(f"SMTP User: {service.smtp_user}")
    print(f"TLS Enabled: {service.use_tls}")

asyncio.run(test_email_config())
```

## Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Verify SMTP_USER and SMTP_PASSWORD are correct
   - For Gmail, use App Passwords instead of regular passwords
   - Check if 2FA is enabled and configure accordingly

2. **Connection Refused**
   - Verify SMTP_SERVER and SMTP_PORT are correct
   - Check firewall settings
   - Ensure TLS settings match server requirements

3. **Emails Not Delivered**
   - Check spam folders
   - Verify sender address is not blacklisted
   - Ensure sender domain has proper SPF/DKIM records

4. **Wrong Sender Address**
   - Verify EMAIL_FROM_ADDRESS environment variable is set
   - Check environment variable precedence order
   - Restart services after changing environment variables

### Debug Mode

Enable debug logging to troubleshoot email issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

This will show detailed SMTP communication logs.

## Production Deployment

### Docker Configuration

When deploying with Docker, pass environment variables:

```bash
docker run -e EMAIL_FROM_ADDRESS="courses@university.edu" \
           -e SMTP_SERVER="smtp.university.edu" \
           -e SMTP_USER="courses@university.edu" \
           -e SMTP_PASSWORD="password" \
           your-course-platform
```

### Kubernetes Configuration

Use ConfigMaps for non-sensitive values and Secrets for passwords:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: email-config
data:
  EMAIL_FROM_ADDRESS: "courses@university.edu"
  SMTP_SERVER: "smtp.university.edu"
  SMTP_PORT: "587"
  SMTP_USE_TLS: "true"

---
apiVersion: v1
kind: Secret
metadata:
  name: email-secrets
type: Opaque
data:
  SMTP_USER: <base64-encoded-username>
  SMTP_PASSWORD: <base64-encoded-password>
```

## Support

For additional help with email configuration:

1. Check the application logs for detailed error messages
2. Verify network connectivity to SMTP servers
3. Contact your IT department for organization-specific SMTP settings
4. Refer to your email provider's SMTP documentation