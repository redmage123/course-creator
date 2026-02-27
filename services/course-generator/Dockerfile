# Course Generator Service Dockerfile - Using mounted .venv
# No pip installs - uses pre-installed packages from mounted virtual environment
#
# PLAYWRIGHT BROWSER SUPPORT:
# This service requires Playwright for JavaScript execution in SPAs.
# The Chromium browser dependencies are installed at build time.
# The browser itself is installed at first startup (via entrypoint).

FROM course-creator-base:latest

WORKDIR /app

# Install Playwright browser dependencies
# These system packages are required for Chromium to run in headless mode
USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Chromium dependencies
    libnss3 \
    libnspr4 \
    libdbus-1-3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libatspi2.0-0 \
    # Fonts for proper text rendering
    fonts-liberation \
    fonts-noto-color-emoji \
    # Clean up
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create Playwright cache directory with proper permissions
RUN mkdir -p /home/appuser/.cache/ms-playwright \
    && chown -R appuser:appuser /home/appuser

# Set environment variables to use mounted venv
# PATH and VIRTUAL_ENV will be set by docker-compose environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PLAYWRIGHT_BROWSERS_PATH=/home/appuser/.cache/ms-playwright

# Copy application code
COPY . .

# Create entrypoint script that installs Playwright browser on first run
RUN echo '#!/bin/bash\n\
# Install Playwright Chromium if not already installed\n\
if [ ! -d "$PLAYWRIGHT_BROWSERS_PATH/chromium"* ] 2>/dev/null; then\n\
    echo "Installing Playwright Chromium browser..."\n\
    python -m playwright install chromium || echo "Warning: Playwright browser install failed"\n\
fi\n\
exec python main.py\n\
' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Create non-root user directories and set permissions
RUN chown -R appuser:appuser /app

USER appuser

# The virtual environment directory will be mounted from host
# Path configured via VENV_MOUNT_PATH environment variable in docker-compose.yml
# No pip install needed!

EXPOSE 8001

CMD ["/app/entrypoint.sh"]