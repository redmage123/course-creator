# Lab Manager Service Dockerfile - Using mounted .venv
# No pip installs - uses pre-installed packages from mounted virtual environment

FROM course-creator-base:latest

WORKDIR /app

# Set environment variables to use mounted venv
# PATH and VIRTUAL_ENV will be set by docker-compose environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Copy application code
COPY . .

# Use existing appuser from base image and fix ownership
# Docker group will be configured at runtime in docker-compose
RUN chown -R appuser:appuser /app

# Don't set USER here - will be handled by docker-compose with proper group mapping

# The virtual environment directory will be mounted from host
# Path configured via VENV_MOUNT_PATH environment variable in docker-compose.yml
# No pip install needed!

EXPOSE 8006

CMD ["python", "main.py"]
