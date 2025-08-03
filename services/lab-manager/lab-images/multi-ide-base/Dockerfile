# Multi-IDE Base Environment for Course Creator Labs
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    CODE_SERVER_VERSION=4.20.0 \
    PROJECTOR_VERSION=1.7.0

# Install system dependencies including Node.js for VSCode Server
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    nano \
    vim \
    build-essential \
    software-properties-common \
    ca-certificates \
    gnupg \
    lsb-release \
    openjdk-11-jdk \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js (required for some VSCode extensions)
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# Install code-server (VSCode Server)
RUN curl -fsSL https://code-server.dev/install.sh | sh

# Install JetBrains Projector for IntelliJ IDEA
RUN pip install --no-cache-dir projector-installer

# Create lab user with limited privileges
RUN groupadd -r labuser && useradd -r -g labuser -m -d /home/labuser labuser

# Set up workspace and IDE directories
WORKDIR /home/labuser
RUN mkdir -p /home/labuser/{workspace,ide-configs,.local/share/code-server} \
    && chown -R labuser:labuser /home/labuser

# Switch to lab user for installations
USER labuser

# Install IntelliJ IDEA Community Edition via Projector
RUN projector install --accept-license --no-auto-run 'IntelliJ IDEA Community Edition' --port 8082

# Create VSCode configuration
RUN mkdir -p /home/labuser/.local/share/code-server/User \
    && echo '{"workbench.colorTheme": "Default Dark+", "workbench.startupEditor": "none"}' > /home/labuser/.local/share/code-server/User/settings.json

# Set up workspace structure
WORKDIR /home/labuser/workspace
RUN mkdir -p {assignments,solutions,data,notebooks,projects}

# Copy IDE startup scripts
COPY --chown=labuser:labuser ide-startup.py /home/labuser/ide-startup.py
COPY --chown=labuser:labuser ide-configs/ /home/labuser/ide-configs/

# Expose ports for different IDEs
EXPOSE 8080 8081 8082 8083 8084

# Health check for multiple services
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8080/api/status || exit 1

# Start IDE management service
CMD ["python", "/home/labuser/ide-startup.py"]