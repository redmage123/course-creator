#!/bin/bash

# Course Creator Platform Control Script
# Manages microservices without Docker

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Load environment variables from .cc_env file
if [ -f "$SCRIPT_DIR/.cc_env" ]; then
    set -a  # automatically export all variables
    source "$SCRIPT_DIR/.cc_env"
    set +a  # stop automatically exporting
fi

# Service configuration
SERVICES=(
    "user-management:8000"
    "course-generator:8001"
    "content-storage:8003"
    "course-management:8004"
    "content-management:8005"
)

FRONTEND_PORT=3000
PID_DIR="$SCRIPT_DIR/.pids"
LOG_DIR="$SCRIPT_DIR/logs"

# Database configuration
DB_NAME="course_creator"
DB_USER="course_user"
DB_PASSWORD="${DB_PASSWORD:-}"
DB_HOST="localhost"
DB_PORT="5433"
DB_DATA_DIR="$SCRIPT_DIR/postgres_data"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Ensure directories exist
mkdir -p "$PID_DIR" "$LOG_DIR"

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

setup_postgres_path() {
    # Check if pg_ctl is in PATH
    if command -v pg_ctl &> /dev/null; then
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
            if [ -f "$pg_bin_dir/pg_ctl" ]; then
                log_info "Found PostgreSQL at: $pg_bin_dir"
                export PATH="$pg_bin_dir:$PATH"
                return 0
            fi
        done
    done
    
    return 1
}

check_postgres() {
    if ! setup_postgres_path; then
        log_error "PostgreSQL is not installed or not found in common locations."
        log_info "On Ubuntu/Debian: sudo apt-get install postgresql postgresql-contrib"
        log_info "On macOS: brew install postgresql"
        log_info "Or add PostgreSQL bin directory to your PATH"
        return 1
    fi
    return 0
}

init_database() {
    log_info "Initializing PostgreSQL database..."
    
    # Create data directory if it doesn't exist
    if [ ! -d "$DB_DATA_DIR" ]; then
        mkdir -p "$DB_DATA_DIR"
        log_info "Creating PostgreSQL data directory at $DB_DATA_DIR"
        
        # Initialize database cluster
        initdb -D "$DB_DATA_DIR" --auth-host=md5 --auth-local=peer
        
        # Create basic postgresql.conf settings
        echo "port = $DB_PORT" >> "$DB_DATA_DIR/postgresql.conf"
        echo "logging_collector = on" >> "$DB_DATA_DIR/postgresql.conf"
        echo "log_directory = 'log'" >> "$DB_DATA_DIR/postgresql.conf"
        echo "unix_socket_directories = '$DB_DATA_DIR'" >> "$DB_DATA_DIR/postgresql.conf"
        
        log_success "Database cluster initialized"
    fi
}

start_database() {
    setup_postgres_path
    local pid_file="$PID_DIR/postgres.pid"
    local log_file="$LOG_DIR/postgres.log"
    
    if [ -f "$pid_file" ] && kill -0 "$(cat "$pid_file")" 2>/dev/null; then
        log_warning "PostgreSQL is already running"
        return 0
    fi
    
    log_info "Starting PostgreSQL database..."
    
    # Start PostgreSQL
    pg_ctl -D "$DB_DATA_DIR" -l "$log_file" -o "-p $DB_PORT" start
    
    # Wait for PostgreSQL to start
    sleep 3
    
    # Get the PID
    local postgres_pid=$(pg_ctl -D "$DB_DATA_DIR" status | grep "PID" | grep -o '[0-9]*' | head -1)
    if [ -n "$postgres_pid" ]; then
        echo "$postgres_pid" > "$pid_file"
        log_success "PostgreSQL started (PID: $postgres_pid)"
        
        # Create database and user if they don't exist
        setup_database
    else
        log_error "Failed to start PostgreSQL"
        return 1
    fi
}

setup_database() {
    log_info "Setting up database and user..."
    
    # Wait a bit more for PostgreSQL to be ready
    sleep 2
    
    # Set postgres password from environment
    export PGPASSWORD="$POSTGRES_PASSWORD"
    
    # Create user and database
    psql -h "$DB_HOST" -p "$DB_PORT" -d postgres -U postgres -c "
        DO \$\$
        BEGIN
            IF NOT EXISTS (SELECT FROM pg_catalog.pg_user WHERE usename = '$DB_USER') THEN
                CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD' LOGIN;
            ELSE
                ALTER USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
            END IF;
        END
        \$\$;
    " 2>/dev/null || true
    
    psql -h "$DB_HOST" -p "$DB_PORT" -d postgres -U postgres -c "
        SELECT 'CREATE DATABASE $DB_NAME OWNER $DB_USER'
        WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DB_NAME')
        \\gexec
    " 2>/dev/null || true
    
    # Grant privileges
    psql -h "$DB_HOST" -p "$DB_PORT" -d postgres -U postgres -c "
        GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
        ALTER USER $DB_USER CREATEDB;
    " 2>/dev/null || true
    
    # Grant schema privileges
    psql -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -U postgres -c "
        GRANT ALL ON SCHEMA public TO $DB_USER;
        GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $DB_USER;
        GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO $DB_USER;
        ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO $DB_USER;
        ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO $DB_USER;
    " 2>/dev/null || true
    
    # Run schema if schema file exists
    if [ -f "$SCRIPT_DIR/create-course-creator-schema.sql" ]; then
        log_info "Applying database schema..."
        PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -U "$DB_USER" -f "$SCRIPT_DIR/create-course-creator-schema.sql" 2>/dev/null || true
        log_success "Database schema applied"
    fi
    
    log_success "Database setup completed"
}

stop_database() {
    setup_postgres_path
    local pid_file="$PID_DIR/postgres.pid"
    
    if [ ! -f "$pid_file" ]; then
        log_warning "PostgreSQL is not running (no PID file)"
        return 0
    fi
    
    local pid=$(cat "$pid_file")
    log_info "Stopping PostgreSQL (PID: $pid)..."
    
    pg_ctl -D "$DB_DATA_DIR" stop -m fast
    
    if [ $? -eq 0 ]; then
        rm -f "$pid_file"
        log_success "PostgreSQL stopped"
    else
        log_error "Failed to stop PostgreSQL"
        return 1
    fi
}

database_status() {
    setup_postgres_path
    local pid_file="$PID_DIR/postgres.pid"
    
    if [ -f "$pid_file" ] && kill -0 "$(cat "$pid_file")" 2>/dev/null; then
        local pid=$(cat "$pid_file")
        if pg_isready -h "$DB_HOST" -p "$DB_PORT" -q; then
            echo -e "  postgresql: ${GREEN}RUNNING${NC} (PID: $pid, Port: $DB_PORT, Health: OK)"
        else
            echo -e "  postgresql: ${YELLOW}RUNNING${NC} (PID: $pid, Port: $DB_PORT, Health: NOT READY)"
        fi
    else
        echo -e "  postgresql: ${RED}STOPPED${NC}"
    fi
}

check_db_password() {
    if [ -z "$DB_PASSWORD" ]; then
        echo -n "Database password not found in .cc_env file. "
        read -s -p "Enter database password: " DB_PASSWORD
        echo
        export DB_PASSWORD
    fi
}

check_python_env() {
    if [ ! -d ".venv" ]; then
        log_error "Virtual environment not found. Please create one with: python -m venv .venv"
        exit 1
    fi
    
    if [ -z "$VIRTUAL_ENV" ]; then
        log_info "Activating virtual environment..."
        source .venv/bin/activate
    fi
}

install_dependencies() {
    log_info "Installing Python dependencies for all services..."
    
    for service_config in "${SERVICES[@]}"; do
        service_name="${service_config%:*}"
        service_dir="services/$service_name"
        
        if [ -d "$service_dir" ] && [ -f "$service_dir/requirements.txt" ]; then
            log_info "Installing dependencies for $service_name..."
            pip install -r "$service_dir/requirements.txt" > "$LOG_DIR/$service_name-install.log" 2>&1
            log_success "Dependencies installed for $service_name"
        else
            log_warning "No requirements.txt found for $service_name"
        fi
    done
}

start_service() {
    local service_name="$1"
    local port="$2"
    local service_dir="services/$service_name"
    
    if [ ! -d "$service_dir" ]; then
        log_error "Service directory not found: $service_dir"
        return 1
    fi
    
    local pid_file="$PID_DIR/$service_name.pid"
    local log_file="$LOG_DIR/$service_name.log"
    
    if [ -f "$pid_file" ] && kill -0 "$(cat "$pid_file")" 2>/dev/null; then
        log_warning "$service_name is already running (PID: $(cat "$pid_file"))"
        return 0
    fi
    
    log_info "Starting $service_name on port $port..."
    
    # Start the service
    cd "$service_dir"
    
    # Export environment variables for the service
    export DB_PASSWORD="$DB_PASSWORD"
    export POSTGRES_PASSWORD="$POSTGRES_PASSWORD"
    export JWT_SECRET_KEY="$JWT_SECRET_KEY"
    export ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY"
    export HOST_IP="$HOST_IP"
    
    # Set PYTHONPATH to include the service directory for imports
    export PYTHONPATH="$PWD:$PYTHONPATH"
    
    if [ -f "main.py" ]; then
        python main.py > "$log_file" 2>&1 &
    elif [ -f "run.py" ]; then
        python run.py > "$log_file" 2>&1 &
    else
        log_error "No main.py or run.py found in $service_dir"
        cd "$SCRIPT_DIR"
        return 1
    fi
    
    local pid=$!
    echo "$pid" > "$pid_file"
    cd "$SCRIPT_DIR"
    
    # Wait a moment and check if service started successfully
    sleep 2
    if kill -0 "$pid" 2>/dev/null; then
        # Check if service is responding
        if curl -s "http://localhost:$port/health" > /dev/null 2>&1; then
            log_success "$service_name started successfully (PID: $pid, Port: $port)"
        else
            log_warning "$service_name started but health check failed (PID: $pid, Port: $port)"
        fi
    else
        log_error "$service_name failed to start"
        rm -f "$pid_file"
        return 1
    fi
}

stop_service() {
    local service_name="$1"
    local pid_file="$PID_DIR/$service_name.pid"
    
    if [ ! -f "$pid_file" ]; then
        log_warning "$service_name is not running (no PID file)"
        return 0
    fi
    
    local pid
    pid=$(cat "$pid_file")
    
    if kill -0 "$pid" 2>/dev/null; then
        log_info "Stopping $service_name (PID: $pid)..."
        kill "$pid"
        
        # Wait for graceful shutdown
        local count=0
        while kill -0 "$pid" 2>/dev/null && [ $count -lt 10 ]; do
            sleep 1
            count=$((count + 1))
        done
        
        # Force kill if still running
        if kill -0 "$pid" 2>/dev/null; then
            log_warning "Force killing $service_name..."
            kill -9 "$pid"
        fi
        
        log_success "$service_name stopped"
    else
        log_warning "$service_name was not running"
    fi
    
    rm -f "$pid_file"
}

start_frontend() {
    local pid_file="$PID_DIR/frontend.pid"
    local log_file="$LOG_DIR/frontend.log"
    
    if [ ! -d "frontend" ]; then
        log_warning "Frontend directory not found"
        return 0
    fi
    
    if [ -f "$pid_file" ] && kill -0 "$(cat "$pid_file")" 2>/dev/null; then
        log_warning "Frontend is already running (PID: $(cat "$pid_file"))"
        return 0
    fi
    
    log_info "Starting frontend server on port $FRONTEND_PORT..."
    
    cd frontend
    python -m http.server "$FRONTEND_PORT" > "$log_file" 2>&1 &
    local pid=$!
    echo "$pid" > "$pid_file"
    cd "$SCRIPT_DIR"
    
    sleep 1
    if kill -0 "$pid" 2>/dev/null; then
        log_success "Frontend started successfully (PID: $pid, Port: $FRONTEND_PORT)"
    else
        log_error "Frontend failed to start"
        rm -f "$pid_file"
        return 1
    fi
}

stop_frontend() {
    local pid_file="$PID_DIR/frontend.pid"
    
    if [ ! -f "$pid_file" ]; then
        log_warning "Frontend is not running (no PID file)"
        return 0
    fi
    
    local pid
    pid=$(cat "$pid_file")
    
    if kill -0 "$pid" 2>/dev/null; then
        log_info "Stopping frontend (PID: $pid)..."
        kill "$pid"
        log_success "Frontend stopped"
    else
        log_warning "Frontend was not running"
    fi
    
    rm -f "$pid_file"
}

start_all() {
    log_info "Starting Course Creator Platform with database..."
    check_python_env
    check_postgres
    check_db_password
    
    # Export database password for services
    export DB_PASSWORD
    
    # Initialize database if needed
    init_database
    
    # Start PostgreSQL database first
    start_database
    
    # Wait for database to be ready
    sleep 2
    
    # Start services in dependency order
    for service_config in "${SERVICES[@]}"; do
        service_name="${service_config%:*}"
        port="${service_config#*:}"
        start_service "$service_name" "$port"
    done
    
    # Start frontend
    start_frontend
    
    echo
    log_success "Platform started successfully!"
    echo
    echo "🌐 Access URLs:"
    for service_config in "${SERVICES[@]}"; do
        service_name="${service_config%:*}"
        port="${service_config#*:}"
        echo "  $service_name: http://localhost:$port"
    done
    echo "  Frontend: http://localhost:$FRONTEND_PORT"
    echo
    echo "🗄️  Database:"
    echo "  PostgreSQL: localhost:$DB_PORT (Database: $DB_NAME, User: $DB_USER)"
    echo
    echo "📋 Management:"
    echo "  Status: $0 status"
    echo "  Logs: $0 logs [service-name]"
    echo "  Stop: $0 stop"
}

stop_all() {
    log_info "Stopping Course Creator Platform..."
    
    # Stop frontend
    stop_frontend
    
    # Stop services in reverse order
    for ((i=${#SERVICES[@]}-1; i>=0; i--)); do
        service_config="${SERVICES[i]}"
        service_name="${service_config%:*}"
        stop_service "$service_name"
    done
    
    # Stop database last
    stop_database
    
    log_success "Platform stopped"
}

restart_service() {
    local service_name="$1"
    
    if [ -z "$service_name" ]; then
        log_error "Service name required for restart"
        return 1
    fi
    
    # Find the service port
    local port=""
    for service_config in "${SERVICES[@]}"; do
        if [[ "$service_config" == "$service_name:"* ]]; then
            port="${service_config#*:}"
            break
        fi
    done
    
    if [ -z "$port" ]; then
        log_error "Unknown service: $service_name"
        return 1
    fi
    
    log_info "Restarting $service_name..."
    stop_service "$service_name"
    sleep 1
    start_service "$service_name" "$port"
}

restart_all() {
    log_info "Restarting Course Creator Platform..."
    stop_all
    sleep 2
    start_all
}

show_status() {
    echo "📊 Course Creator Platform Status"
    echo "================================="
    
    local all_running=true
    
    # Check database first
    database_status
    
    # Check services
    for service_config in "${SERVICES[@]}"; do
        service_name="${service_config%:*}"
        port="${service_config#*:}"
        pid_file="$PID_DIR/$service_name.pid"
        
        if [ -f "$pid_file" ] && kill -0 "$(cat "$pid_file")" 2>/dev/null; then
            local pid
            pid=$(cat "$pid_file")
            
            # Check if service is responding
            if curl -s "http://localhost:$port/health" > /dev/null 2>&1; then
                echo -e "  $service_name: ${GREEN}RUNNING${NC} (PID: $pid, Port: $port, Health: OK)"
            else
                echo -e "  $service_name: ${YELLOW}RUNNING${NC} (PID: $pid, Port: $port, Health: FAIL)"
                all_running=false
            fi
        else
            echo -e "  $service_name: ${RED}STOPPED${NC}"
            all_running=false
        fi
    done
    
    # Check frontend
    local frontend_pid_file="$PID_DIR/frontend.pid"
    if [ -f "$frontend_pid_file" ] && kill -0 "$(cat "$frontend_pid_file")" 2>/dev/null; then
        echo -e "  frontend: ${GREEN}RUNNING${NC} (PID: $(cat "$frontend_pid_file"), Port: $FRONTEND_PORT)"
    else
        echo -e "  frontend: ${RED}STOPPED${NC}"
        all_running=false
    fi
    
    echo
    if [ "$all_running" = true ]; then
        echo -e "Overall Status: ${GREEN}ALL SERVICES RUNNING${NC}"
    else
        echo -e "Overall Status: ${RED}SOME SERVICES DOWN${NC}"
    fi
}

show_logs() {
    local service_name="$1"
    
    if [ -z "$service_name" ]; then
        echo "📋 Available log files:"
        for log_file in "$LOG_DIR"/*.log; do
            if [ -f "$log_file" ]; then
                echo "  $(basename "$log_file" .log)"
            fi
        done
        echo
        echo "Usage: $0 logs <service-name>"
        echo "       $0 logs all"
        return
    fi
    
    if [ "$service_name" = "all" ]; then
        for log_file in "$LOG_DIR"/*.log; do
            if [ -f "$log_file" ]; then
                echo "=== $(basename "$log_file") ==="
                tail -n 20 "$log_file"
                echo
            fi
        done
    else
        local log_file="$LOG_DIR/$service_name.log"
        if [ -f "$log_file" ]; then
            echo "=== $service_name logs (last 50 lines) ==="
            tail -n 50 "$log_file"
        else
            log_error "Log file not found: $log_file"
        fi
    fi
}

clean_all() {
    log_info "Cleaning up platform data..."
    
    # Stop all services first
    stop_all
    
    # Clean PID files
    rm -rf "$PID_DIR"
    mkdir -p "$PID_DIR"
    
    # Clean logs
    rm -rf "$LOG_DIR"
    mkdir -p "$LOG_DIR"
    
    log_success "Cleanup completed"
}

# Main command handling
case "${1:-}" in
    start)
        if [ -n "$2" ]; then
            # Start specific service
            for service_config in "${SERVICES[@]}"; do
                if [[ "$service_config" == "$2:"* ]]; then
                    port="${service_config#*:}"
                    check_python_env
                    start_service "$2" "$port"
                    exit $?
                fi
            done
            log_error "Unknown service: $2"
            exit 1
        else
            start_all
        fi
        ;;
    stop)
        if [ -n "$2" ]; then
            # Stop specific service
            stop_service "$2"
        else
            stop_all
        fi
        ;;
    restart)
        if [ -n "$2" ]; then
            # Restart specific service
            restart_service "$2"
        else
            restart_all
        fi
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs "$2"
        ;;
    clean)
        clean_all
        ;;
    install-deps)
        check_python_env
        install_dependencies
        ;;
    init-db)
        check_postgres
        init_database
        ;;
    start-db)
        check_postgres
        init_database
        start_database
        ;;
    stop-db)
        stop_database
        ;;
    *)
        echo "Course Creator Platform Control Script"
        echo
        echo "Usage: $0 {start|stop|restart|status|logs|clean|install-deps|init-db|start-db|stop-db} [service-name]"
        echo
        echo "Commands:"
        echo "  start [service]  Start database, all services and frontend (or specific service)"
        echo "  stop [service]   Stop all services, frontend and database (or specific service)"
        echo "  restart [service] Restart entire platform including database (or specific service)"
        echo "  status           Show status of database and all services"
        echo "  logs [service]   Show logs for a service (or 'all')"
        echo "  clean            Stop services and clean up logs/pids"
        echo "  install-deps     Install Python dependencies for all services"
        echo
        echo "Database Commands:"
        echo "  init-db          Initialize PostgreSQL database cluster"
        echo "  start-db         Start only the PostgreSQL database"
        echo "  stop-db          Stop only the PostgreSQL database"
        echo
        echo "Service Names:"
        for service_config in "${SERVICES[@]}"; do
            service_name="${service_config%:*}"
            echo "  $service_name"
        done
        echo
        echo "Examples:"
        echo "  $0 start"
        echo "  $0 start course-generator"
        echo "  $0 restart course-generator"
        echo "  $0 status"
        echo "  $0 logs user-management"
        echo "  $0 logs all"
        echo
        echo "Environment:"
        echo "  Create .cc_env file with DB_PASSWORD and other secrets"
        echo "  Example: echo 'DB_PASSWORD=your_password' > .cc_env"
        exit 1
        ;;
esac