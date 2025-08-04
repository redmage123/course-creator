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
# Find the group with GID 999 and add appuser to it for Docker socket access
RUN DOCKER_GID=999 && \
    DOCKER_GROUP=$(getent group $DOCKER_GID | cut -d: -f1) && \
    if [ -z "$DOCKER_GROUP" ]; then \
        groupadd -g $DOCKER_GID docker; \
        DOCKER_GROUP=docker; \
    fi && \
    usermod -aG $DOCKER_GROUP appuser && \
    chown -R appuser:appuser /app
USER appuser

# The virtual environment directory will be mounted from host
# Path configured via VENV_MOUNT_PATH environment variable in docker-compose.yml
# No pip install needed!

EXPOSE 8006

CMD ["python", "main.py"]
