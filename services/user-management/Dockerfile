# User Management Service Dockerfile - Using shared base image and mounted .venv
# No pip installs - uses pre-installed packages from mounted virtual environment
# No system package downloads - uses cached base image

FROM course-creator-base:latest

# Copy application code
COPY . .

# Use existing appuser from base image and set ownership
RUN chown -R appuser:appuser /app
USER appuser

# The virtual environment directory will be mounted from host
# Path configured via VENV_MOUNT_PATH environment variable
# No pip install needed!

EXPOSE 8000

CMD ["python", "main.py"]