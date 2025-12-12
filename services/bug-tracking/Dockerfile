# Bug Tracking Service Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies including CA certificates for SSL verification
RUN apt-get update && apt-get install -y \
    git \
    curl \
    ca-certificates \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && git config --global --add safe.directory /workspace \
    && git config --global user.email "bug-tracker@coursecreator.ai" \
    && git config --global user.name "Bug Tracker Bot"

# Install GitHub CLI for PR creation
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
    && chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
    && apt-get update \
    && apt-get install gh -y \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY . .

# Set Python path for imports
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8017

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f https://localhost:8017/health --insecure || exit 1

# Run the service
CMD ["python", "main.py"]
