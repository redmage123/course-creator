# JavaScript/Node.js Lab Environment
FROM node:18-slim

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    nano \
    vim \
    wget \
    python3 \
    python3-pip \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install global Node.js packages for labs
RUN npm install -g \
    nodemon \
    express-generator \
    create-react-app \
    @vue/cli \
    typescript \
    ts-node \
    eslint \
    prettier \
    jest

# Create lab user with limited privileges
RUN groupadd -r labuser && useradd -r -g labuser -m -d /home/labuser labuser

# Set up workspace
WORKDIR /home/labuser/workspace
RUN chown -R labuser:labuser /home/labuser

# Switch to lab user
USER labuser

# Create default lab structure
RUN mkdir -p /home/labuser/workspace/{assignments,solutions,projects,static}

# Initialize a basic package.json
RUN echo '{\
  "name": "javascript-lab",\
  "version": "1.0.0",\
  "description": "JavaScript Lab Environment",\
  "main": "index.js",\
  "scripts": {\
    "start": "node index.js",\
    "dev": "nodemon index.js",\
    "test": "jest"\
  },\
  "dependencies": {\
    "express": "^4.18.0",\
    "lodash": "^4.17.0",\
    "axios": "^1.0.0"\
  },\
  "devDependencies": {\
    "jest": "^29.0.0",\
    "nodemon": "^3.0.0"\
  }\
}' > /home/labuser/workspace/package.json

# Install lab dependencies
RUN cd /home/labuser/workspace && npm install

# Copy lab startup script
COPY --chown=labuser:labuser lab-startup.js /home/labuser/lab-startup.js

# Expose development server port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/ || exit 1

# Start lab environment
CMD ["node", "/home/labuser/lab-startup.js"]