# Python Lab with Web-based IDEs
FROM python:3.10-slim

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    vim \
    sudo \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Create lab user
RUN useradd -m -s /bin/bash labuser && \
    echo "labuser:labpass" | chpasswd && \
    usermod -aG sudo labuser

# Install Python packages
RUN pip install --no-cache-dir \
    jupyter \
    jupyterlab \
    notebook \
    numpy \
    pandas \
    matplotlib \
    requests \
    flask \
    fastapi \
    uvicorn

# Install code-server (VS Code in browser)
RUN curl -fsSL https://code-server.dev/install.sh | sh

# Install VS Code extensions for labuser
USER labuser
RUN code-server --install-extension ms-python.python || true
USER root

# Create workspace and set permissions
RUN mkdir -p /home/labuser/workspace && \
    chown -R labuser:labuser /home/labuser

# Create startup script
COPY start-multi-ide.sh /usr/local/bin/start-multi-ide.sh
RUN chmod +x /usr/local/bin/start-multi-ide.sh

# Expose ports for IDEs
EXPOSE 8080 8081 8082

WORKDIR /home/labuser/workspace

# Start as root so startup script can fix permissions
USER root
CMD ["/usr/local/bin/start-multi-ide.sh"]