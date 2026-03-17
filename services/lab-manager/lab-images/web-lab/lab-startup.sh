#!/bin/sh
# Web Lab Startup Script

echo "Setting up Web Development Lab..."

# Get lab configuration from environment
SESSION_ID=${LAB_SESSION_ID:-"default"}
USER_ID=${USER_ID:-"student"}
COURSE_ID=${COURSE_ID:-"default-course"}
LAB_CONFIG=${LAB_CONFIG:-"{}"}

echo "Session: $SESSION_ID, User: $USER_ID, Course: $COURSE_ID"

# Create session info file
cat > /home/labuser/workspace/session_info.json << EOF
{
  "session_id": "$SESSION_ID",
  "user_id": "$USER_ID",
  "course_id": "$COURSE_ID",
  "lab_type": "web",
  "config": $LAB_CONFIG
}
EOF

# Update the welcome page with session info
sed -i "s/Web Development Lab/Web Development Lab - Session: $SESSION_ID/" /home/labuser/workspace/index.html

# Set proper permissions
chown -R labuser:labuser /home/labuser/workspace

echo "Starting nginx server..."

# Start nginx in the background
nginx -g "daemon off;" &

# Keep the container running
wait