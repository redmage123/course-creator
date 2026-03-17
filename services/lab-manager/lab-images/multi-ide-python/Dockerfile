# Multi-IDE Python Lab Environment
FROM ubuntu:22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV HOME=/home/labuser
ENV SHELL=/bin/bash

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # Basic tools
    curl \
    wget \
    git \
    vim \
    nano \
    htop \
    unzip \
    software-properties-common \
    # Python and build tools
    python3 \
    python3-pip \
    python3-dev \
    python3-venv \
    build-essential \
    # Node.js for VSCode Server
    nodejs \
    npm \
    # Java for IntelliJ (optional)
    openjdk-11-jdk \
    # Additional tools
    supervisor \
    nginx \
    && rm -rf /var/lib/apt/lists/*

# Create lab user
RUN useradd -m -s /bin/bash labuser && \
    echo "labuser:labpass" | chpasswd && \
    usermod -aG sudo labuser

# Install Python packages
RUN pip3 install --no-cache-dir \
    jupyter \
    jupyterlab \
    notebook \
    ipython \
    numpy \
    pandas \
    matplotlib \
    scipy \
    scikit-learn \
    requests \
    flask \
    fastapi \
    uvicorn

# Install code-server (VS Code in browser)
RUN curl -fsSL https://code-server.dev/install.sh | sh

# Set up VS Code extensions
USER labuser
RUN code-server --install-extension ms-python.python --force
RUN code-server --install-extension ms-python.pylint --force
USER root

# Create workspace directory
RUN mkdir -p /home/labuser/workspace && \
    chown -R labuser:labuser /home/labuser

# Set up supervisor configuration for multi-service management
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expose ports for different IDEs
# 8080: VS Code Server
# 8081: JupyterLab
# 8082: Jupyter Notebook
# 8083: Custom web terminal
EXPOSE 8080 8081 8082 8083

# Create startup script
COPY start-ides.sh /usr/local/bin/start-ides.sh
RUN chmod +x /usr/local/bin/start-ides.sh

WORKDIR /home/labuser/workspace
USER labuser

CMD ["/usr/local/bin/start-ides.sh"]