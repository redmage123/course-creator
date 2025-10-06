# Metadata Service Dockerfile
# Uses shared base image for system packages

FROM course-creator-base:latest

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies as root
USER root
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Use existing appuser from base image and fix ownership
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8011

CMD ["python", "main.py"]
