# Python Lab Environment
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    nano \
    vim \
    wget \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install common Python packages for labs
RUN pip install --no-cache-dir \
    jupyter \
    jupyterlab \
    numpy \
    pandas \
    matplotlib \
    seaborn \
    requests \
    flask \
    fastapi \
    pytest \
    black \
    pylint

# Create lab user with limited privileges
RUN groupadd -r labuser && useradd -r -g labuser -m -d /home/labuser labuser

# Set up workspace
WORKDIR /home/labuser/workspace
RUN chown -R labuser:labuser /home/labuser

# Switch to lab user
USER labuser

# Create default lab structure
RUN mkdir -p /home/labuser/workspace/{assignments,solutions,data,notebooks}

# Copy lab startup script
COPY --chown=labuser:labuser lab-startup.py /home/labuser/lab-startup.py

# Expose JupyterLab port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/ || exit 1

# Start JupyterLab
CMD ["python", "/home/labuser/lab-startup.py"]