# AI Assistant Service Dockerfile
# Uses shared base image for system packages, then uses mounted virtual environment

FROM course-creator-base:latest

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    AI_ASSISTANT_PORT=8011 \
    LOG_LEVEL=INFO

# Use mounted virtual environment - no pip installs needed
# Virtual environment will be mounted from host at runtime

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /var/log/course-creator

# Use existing appuser from base image and fix ownership
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8011

CMD ["python", "main.py"]
