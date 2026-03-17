#!/bin/bash

# Multi-IDE startup script for student lab containers
echo "Starting Multi-IDE Python Lab Environment..."

# Ensure workspace directory exists and has proper permissions
mkdir -p /home/labuser/workspace
chown -R labuser:labuser /home/labuser/workspace

# Create log directories
sudo mkdir -p /var/log/supervisor
sudo chown -R labuser:labuser /var/log/supervisor

# Start supervisor to manage all services
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf