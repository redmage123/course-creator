# content-management Service Dockerfile - Using mounted .venv
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

# Create non-root user
RUN \
    chown -R appuser:appuser /app
USER appuser

# The virtual environment directory will be mounted from host
# Path configured via VENV_MOUNT_PATH environment variable in docker-compose.yml
# No pip install needed!

EXPOSE 8005

CMD ["python", "main.py"]
