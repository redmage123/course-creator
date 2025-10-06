# Simple Python Lab Environment with web-based access
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV HOME=/home/labuser

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    vim \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# Create lab user
RUN useradd -m -s /bin/bash labuser && \
    echo "labuser:labpass" | chpasswd && \
    usermod -aG sudo labuser

# Install Python packages for basic lab functionality
RUN pip install --no-cache-dir \
    jupyter \
    jupyterlab \
    notebook \
    numpy \
    pandas \
    matplotlib \
    requests \
    flask

# Install code-server (VS Code in browser)
RUN curl -fsSL https://code-server.dev/install.sh | sh

# Create workspace directory
RUN mkdir -p /home/labuser/workspace && \
    chown -R labuser:labuser /home/labuser

# Create simple startup script
COPY start-simple.sh /usr/local/bin/start-simple.sh
RUN chmod +x /usr/local/bin/start-simple.sh

# Expose ports for IDEs
EXPOSE 8080 8081 8082

WORKDIR /home/labuser/workspace
USER labuser

CMD ["/usr/local/bin/start-simple.sh"]