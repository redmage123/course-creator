#!/bin/bash

# Script to create course_creator user in PostgreSQL database
# Loads password from .cc_env file

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Load environment variables from .cc_env file
if [ -f "$SCRIPT_DIR/.cc_env" ]; then
    set -a  # automatically export all variables
    source "$SCRIPT_DIR/.cc_env"
    set +a  # stop automatically exporting
fi

# Setup PostgreSQL path
setup_postgres_path() {
    # Check if pg_ctl is in PATH
    if command -v psql &> /dev/null; then
        return 0
    fi
    
    # Try to find PostgreSQL in common locations
    local pg_paths=(
        "/usr/lib/postgresql/*/bin"
        "/usr/pgsql-*/bin"
        "/opt/postgresql/*/bin"
        "/Applications/Postgres.app/Contents/Versions/*/bin"
    )
    
    for path_pattern in "${pg_paths[@]}"; do
        for pg_bin_dir in $path_pattern; do
            if [ -f "$pg_bin_dir/psql" ]; then
                export PATH="$pg_bin_dir:$PATH"
                return 0
            fi
        done
    done
    
    return 1
}

setup_postgres_path

# Database configuration
DB_NAME="course_creator"
DB_USER="course_user"
DB_HOST="/home/bbrelin/course-creator/postgres_data"  # Unix socket path
DB_PORT="5433"
POSTGRES_USER="bbrelin"  # Current user with superuser privileges

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if password is available
if [ -z "$DB_PASSWORD" ]; then
    echo -n "Database password not found in .cc_env file. "
    read -s -p "Enter database password for course_user: " DB_PASSWORD
    echo
fi

log_info "Setting up course_creator user in PostgreSQL database..."

# Test if PostgreSQL is running
if ! pg_isready -h "$DB_HOST" -p "$DB_PORT" -q 2>/dev/null; then
    log_error "PostgreSQL is not running on $DB_HOST:$DB_PORT"
    log_info "Start it with: ./app-control.sh start-db"
    exit 1
fi

log_info "PostgreSQL is running, proceeding with user setup..."

# Drop existing user if exists
log_info "Removing existing course_user if it exists..."
psql -h "$DB_HOST" -p "$DB_PORT" -d postgres -U "$POSTGRES_USER" -c "
    DROP USER IF EXISTS $DB_USER;
" 2>/dev/null || true

# Create the user with login privileges
log_info "Creating user '$DB_USER' with login privileges..."
psql -h "$DB_HOST" -p "$DB_PORT" -d postgres -U "$POSTGRES_USER" -c "
    CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD' LOGIN;
" 2>/dev/null || {
    log_error "Failed to create user $DB_USER"
    exit 1
}

# Create database if it doesn't exist
log_info "Creating database '$DB_NAME'..."
psql -h "$DB_HOST" -p "$DB_PORT" -d postgres -U "$POSTGRES_USER" -c "
    SELECT 'CREATE DATABASE $DB_NAME OWNER $DB_USER'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DB_NAME')
    \\gexec
" 2>/dev/null || true

# Grant database privileges
log_info "Granting database privileges..."
psql -h "$DB_HOST" -p "$DB_PORT" -d postgres -U "$POSTGRES_USER" -c "
    GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
    ALTER USER $DB_USER CREATEDB;
" 2>/dev/null || {
    log_error "Failed to grant database privileges"
    exit 1
}

# Grant schema privileges
log_info "Granting schema privileges..."
psql -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -U "$POSTGRES_USER" -c "
    GRANT ALL ON SCHEMA public TO $DB_USER;
    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $DB_USER;
    GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO $DB_USER;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO $DB_USER;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO $DB_USER;
" 2>/dev/null || {
    log_error "Failed to grant schema privileges"
    exit 1
}

# Apply database schema if it exists
if [ -f "$SCRIPT_DIR/create-course-creator-schema.sql" ]; then
    log_info "Applying database schema..."
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -U "$DB_USER" -f "$SCRIPT_DIR/create-course-creator-schema.sql" 2>/dev/null || {
        log_error "Failed to apply database schema"
        exit 1
    }
    log_success "Database schema applied successfully"
fi

# Test the connection
log_info "Testing database connection..."
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -U "$DB_USER" -c "SELECT current_user, current_database();" || {
    log_error "Database connection test failed"
    exit 1
}

log_success "Database user setup completed successfully!"
log_info "User: $DB_USER"
log_info "Database: $DB_NAME"
log_info "Connection: $DB_HOST:$DB_PORT"