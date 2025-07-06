#!/bin/bash

# Course Creator Platform - Management Script
# Usage: ./start-app.sh [start|stop|restart|status]

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# PID files
BACKEND_PID_FILE=".backend.pid"
FRONTEND_PID_FILE=".frontend.pid"

# Function to print usage
usage() {
    echo -e "${BLUE}Course Creator Platform - Management Script${NC}"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo -e "  ${GREEN}start${NC}     Start both frontend and backend servers"
    echo -e "  ${RED}stop${NC}      Stop both servers"
    echo -e "  ${YELLOW}restart${NC}   Restart both servers"
    echo -e "  ${PURPLE}status${NC}    Check status of both servers"
    echo -e "  ${BLUE}help${NC}      Show this help message"
    echo ""
    echo "URLs when running:"
    echo -e "  📱 Frontend:      ${BLUE}http://localhost:3000${NC}"
    echo -e "  🔧 Backend API:   ${BLUE}http://localhost:8000${NC}"
    echo -e "  📚 Documentation: ${BLUE}http://localhost:8000/docs${NC}"
    echo -e "  ❤️  Health Check:  ${BLUE}http://localhost:8000/health${NC}"
}

# Function to check if a process is running
is_running() {
    local pid_file=$1
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0  # Process is running
        else
            rm -f "$pid_file"  # Clean up stale PID file
            return 1  # Process not running
        fi
    else
        return 1  # PID file doesn't exist
    fi
}

# Function to check server status
check_status() {
    echo -e "${PURPLE}📊 Checking Course Creator Platform Status...${NC}\n"
    
    local backend_running=false
    local frontend_running=false
    
    # Check backend
    if is_running "$BACKEND_PID_FILE"; then
        local backend_pid=$(cat "$BACKEND_PID_FILE")
        echo -e "🔧 Backend:  ${GREEN}Running${NC} (PID: $backend_pid) - http://localhost:8000"
        backend_running=true
    else
        echo -e "🔧 Backend:  ${RED}Stopped${NC}"
    fi
    
    # Check frontend
    if is_running "$FRONTEND_PID_FILE"; then
        local frontend_pid=$(cat "$FRONTEND_PID_FILE")
        echo -e "📱 Frontend: ${GREEN}Running${NC} (PID: $frontend_pid) - http://localhost:3000"
        frontend_running=true
    else
        echo -e "📱 Frontend: ${RED}Stopped${NC}"
    fi
    
    echo ""
    
    if [ "$backend_running" = true ] && [ "$frontend_running" = true ]; then
        echo -e "${GREEN}✅ Platform Status: All services running${NC}"
        return 0
    elif [ "$backend_running" = true ] || [ "$frontend_running" = true ]; then
        echo -e "${YELLOW}⚠️  Platform Status: Partially running${NC}"
        return 1
    else
        echo -e "${RED}❌ Platform Status: All services stopped${NC}"
        return 2
    fi
}

# Function to stop servers
stop_servers() {
    echo -e "${RED}🛑 Stopping Course Creator Platform...${NC}"
    
    local stopped_any=false
    
    # Stop backend
    if is_running "$BACKEND_PID_FILE"; then
        local backend_pid=$(cat "$BACKEND_PID_FILE")
        echo "Stopping backend (PID: $backend_pid)..."
        kill "$backend_pid" 2>/dev/null
        sleep 2
        
        # Force kill if still running
        if ps -p "$backend_pid" > /dev/null 2>&1; then
            echo "Force stopping backend..."
            kill -9 "$backend_pid" 2>/dev/null
        fi
        
        rm -f "$BACKEND_PID_FILE"
        echo -e "${GREEN}✅ Backend stopped${NC}"
        stopped_any=true
    else
        echo -e "${YELLOW}⚠️  Backend was not running${NC}"
    fi
    
    # Stop frontend
    if is_running "$FRONTEND_PID_FILE"; then
        local frontend_pid=$(cat "$FRONTEND_PID_FILE")
        echo "Stopping frontend (PID: $frontend_pid)..."
        kill "$frontend_pid" 2>/dev/null
        sleep 2
        
        # Force kill if still running
        if ps -p "$frontend_pid" > /dev/null 2>&1; then
            echo "Force stopping frontend..."
            kill -9 "$frontend_pid" 2>/dev/null
        fi
        
        rm -f "$FRONTEND_PID_FILE"
        echo -e "${GREEN}✅ Frontend stopped${NC}"
        stopped_any=true
    else
        echo -e "${YELLOW}⚠️  Frontend was not running${NC}"
    fi
    
    if [ "$stopped_any" = true ]; then
        echo -e "\n${GREEN}🎉 Platform stopped successfully${NC}"
    else
        echo -e "\n${YELLOW}ℹ️  Platform was already stopped${NC}"
    fi
}

# Function to start servers
start_servers() {
    echo -e "${BLUE}🚀 Starting Course Creator Platform...${NC}"
    
    # Check if already running
    if is_running "$BACKEND_PID_FILE" || is_running "$FRONTEND_PID_FILE"; then
        echo -e "${YELLOW}⚠️  Some services are already running. Use 'restart' to restart them.${NC}"
        check_status
        return 1
    fi
    
    # Check if required directories exist
    if [ ! -d "course-creator-frontnd" ]; then
        echo -e "${RED}❌ Frontend directory 'course-creator-frontnd' not found${NC}"
        return 1
    fi
    
    if [ ! -f "main.py" ]; then
        echo -e "${RED}❌ Backend main.py not found${NC}"
        return 1
    fi
    
    echo -e "${BLUE}📊 Starting FastAPI Backend...${NC}"
    # Start backend in background
    uvicorn main:app --reload --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
    local backend_pid=$!
    echo "$backend_pid" > "$BACKEND_PID_FILE"
    echo -e "${GREEN}✅ Backend started (PID: $backend_pid) - http://localhost:8000${NC}"
    
    # Wait a moment for backend to start
    sleep 3
    
    echo -e "${BLUE}⚛️  Starting React Frontend...${NC}"
    # Start frontend in background
    cd course-creator-frontnd
    npm start > ../frontend.log 2>&1 &
    local frontend_pid=$!
    echo "$frontend_pid" > "../$FRONTEND_PID_FILE"
    cd ..
    echo -e "${GREEN}✅ Frontend started (PID: $frontend_pid) - http://localhost:3000${NC}"
    
    echo -e "\n${GREEN}🎉 Course Creator Platform is running!${NC}"
    echo -e "📱 Frontend:      ${BLUE}http://localhost:3000${NC}"
    echo -e "🔧 Backend API:   ${BLUE}http://localhost:8000${NC}"
    echo -e "📚 Documentation: ${BLUE}http://localhost:8000/docs${NC}"
    echo -e "❤️  Health Check:  ${BLUE}http://localhost:8000/health${NC}"
    echo -e "\n${YELLOW}💡 Use './start-app.sh status' to check status${NC}"
    echo -e "${YELLOW}💡 Use './start-app.sh stop' to stop servers${NC}"
    echo -e "${YELLOW}💡 Logs: backend.log, frontend.log${NC}"
}

# Function to restart servers
restart_servers() {
    echo -e "${YELLOW}🔄 Restarting Course Creator Platform...${NC}\n"
    stop_servers
    echo ""
    sleep 2
    start_servers
}

# Cleanup function for interactive start
cleanup() {
    echo -e "\n${YELLOW}🛑 Received interrupt signal...${NC}"
    stop_servers
    exit 0
}

# Interactive start function (keeps script running)
start_interactive() {
    start_servers
    if [ $? -eq 0 ]; then
        echo -e "\n${YELLOW}Running in interactive mode. Press Ctrl+C to stop both servers${NC}\n"
        
        # Set trap to cleanup on script exit
        trap cleanup SIGINT SIGTERM
        
        # Keep script running
        while true; do
            sleep 5
            # Check if processes are still running
            if ! is_running "$BACKEND_PID_FILE" && ! is_running "$FRONTEND_PID_FILE"; then
                echo -e "${RED}❌ Both services have stopped unexpectedly${NC}"
                break
            fi
        done
    fi
}

# Main script logic
case "${1:-start}" in
    "start")
        if [ "$2" = "-i" ] || [ "$2" = "--interactive" ]; then
            start_interactive
        else
            start_servers
        fi
        ;;
    "stop")
        stop_servers
        ;;
    "restart")
        restart_servers
        ;;
    "status")
        check_status
        ;;
    "help"|"-h"|"--help")
        usage
        ;;
    *)
        echo -e "${RED}❌ Unknown command: $1${NC}\n"
        usage
        exit 1
        ;;
esac
