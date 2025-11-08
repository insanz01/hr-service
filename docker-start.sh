#!/bin/bash

# HR Screening System Docker Startup Script

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Function to check Docker and Docker Compose
check_docker() {
    if ! command -v docker > /dev/null 2>&1; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    if ! command -v docker-compose > /dev/null 2>&1 && ! docker compose version > /dev/null 2>&1; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
}

# Function to create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    mkdir -p uploads logs pids
    touch uploads/.gitkeep logs/.gitkeep
    print_success "Directories created"
}

# Function to build Docker images
build_images() {
    print_status "Building Docker images with optimizations..."

    # Pull base images first to utilize cache
    print_status "Pulling base images..."
    if command -v docker-compose > /dev/null 2>&1; then
        docker-compose pull || true
    else
        docker compose pull || true
    fi

    # Build with parallel build if available
    print_status "Building application images..."
    if command -v docker-compose > /dev/null 2>&1; then
        docker-compose build --parallel
    else
        docker compose build --parallel
    fi

    print_success "Docker images built with optimizations"
}

# Function to start services
start_services() {
    local profile=""
    if [ "$1" = "full" ]; then
        profile="--profile full"
    elif [ "$1" = "monitoring" ]; then
        profile="--profile monitoring"
    elif [ "$1" = "all" ]; then
        profile="--profile full --profile monitoring"
    fi

    print_status "Starting HR Screening System services..."

    if command -v docker-compose > /dev/null 2>&1; then
        docker-compose $profile up -d
    else
        docker compose $profile up -d
    fi

    print_success "Services started"
}

# Function to stop services
stop_services() {
    print_status "Stopping HR Screening System services..."

    if command -v docker-compose > /dev/null 2>&1; then
        docker-compose down
    else
        docker compose down
    fi

    print_success "Services stopped"
}

# Function to show status
show_status() {
    print_status "HR Screening System Status"
    echo "================================"

    if command -v docker-compose > /dev/null 2>&1; then
        docker-compose ps
    else
        docker compose ps
    fi

    echo ""
    print_status "Service URLs:"
    echo "  • API:          http://localhost:5000"
    echo "  • Redis:        localhost:6379"
    echo "  • Flower:       http://localhost:5555 (if monitoring enabled)"
    echo ""
}

# Function to show logs
show_logs() {
    local service="$1"
    local follow="$2"

    local cmd="logs"
    if [ "$follow" = "follow" ]; then
        cmd="logs -f"
    fi

    if [ -z "$service" ]; then
        print_status "Showing logs for all services..."
        if command -v docker-compose > /dev/null 2>&1; then
            docker-compose $cmd
        else
            docker compose $cmd
        fi
    else
        print_status "Showing logs for $service..."
        if command -v docker-compose > /dev/null 2>&1; then
            docker-compose $cmd $service
        else
            docker compose $cmd $service
        fi
    fi
}

# Function to restart services
restart_services() {
    print_status "Restarting HR Screening System services..."
    stop_services
    sleep 2
    start_services "$1"
}

# Function to clean up Docker resources
cleanup() {
    print_status "Cleaning up Docker resources..."

    if command -v docker-compose > /dev/null 2>&1; then
        docker-compose down -v --remove-orphans
        docker-compose down --rmi all
    else
        docker compose down -v --remove-orphans
        docker compose down --rmi all
    fi

    # Remove unused images
    docker image prune -f

    print_success "Docker cleanup completed"
}

# Function to enter container shell
shell() {
    local service="$1"
    if [ -z "$service" ]; then
        service="api"
    fi

    print_status "Entering shell for $service container..."

    if command -v docker-compose > /dev/null 2>&1; then
        docker-compose exec $service /bin/bash
    else
        docker compose exec $service /bin/bash
    fi
}

# Main script logic
case "$1" in
    init)
        check_docker
        create_directories
        build_images
        print_success "Docker environment initialized. Use './docker-start.sh start' to begin."
        ;;
    start)
        check_docker
        create_directories
        start_services "$2"
        sleep 5
        show_status
        print_success "HR Screening System is now running!"
        echo ""
        echo "🚀 Quick Test:"
        echo "curl http://localhost:5000/"
        echo ""
        echo "🛑 To stop: ./docker-start.sh stop"
        echo "📋 To check status: ./docker-start.sh status"
        echo "📝 To view logs: ./docker-start.sh logs"
        ;;
    stop)
        check_docker
        stop_services
        ;;
    restart)
        check_docker
        restart_services "$2"
        ;;
    status)
        check_docker
        show_status
        ;;
    logs)
        check_docker
        if [ "$2" = "-f" ] || [ "$2" = "follow" ]; then
            show_logs "$3" "follow"
        else
            show_logs "$2"
        fi
        ;;
    shell)
        check_docker
        shell "$2"
        ;;
    rebuild)
        check_docker
        print_status "Rebuilding Docker images..."
        stop_services
        build_images
        start_services "$2"
        print_success "Services rebuilt and started"
        ;;
    cleanup)
        check_docker
        cleanup
        ;;
    *)
        echo "HR Screening System - Docker Control Script"
        echo "==========================================="
        echo ""
        echo "Usage: $0 {init|start|stop|restart|status|logs|shell|rebuild|cleanup}"
        echo ""
        echo "Commands:"
        echo "  init           - Initialize Docker environment"
        echo "  start [profile] - Start services (profiles: full, monitoring, all)"
        echo "  stop           - Stop all services"
        echo "  restart [profile] - Restart services"
        echo "  status         - Show service status"
        echo "  logs [service] - Show logs (use -f for follow)"
        echo "  shell [service] - Enter container shell (default: api)"
        echo "  rebuild [profile] - Rebuild and restart services"
        echo "  cleanup        - Clean up all Docker resources"
        echo ""
        echo "Profiles:"
        echo "  full           - Include Celery Beat (scheduled tasks)"
        echo "  monitoring     - Include Flower (Celery monitoring)"
        echo "  all            - Include both Beat and Flower"
        echo ""
        echo "Examples:"
        echo "  $0 init                    # Initialize environment"
        echo "  $0 start                   # Start basic services"
        echo "  $0 start all              # Start all services with monitoring"
        echo "  $0 logs -f                # Follow all logs"
        echo "  $0 logs api               # Show API logs"
        echo "  $0 shell worker           # Enter worker container"
        echo "  $0 status                 # Check service status"
        echo "  $0 stop                   # Stop all services"
        echo "  $0 cleanup                # Clean up everything"
        echo ""
        echo "Service URLs after start:"
        echo "  • API:        http://localhost:5000"
        echo "  • Flower:     http://localhost:5555 (if monitoring enabled)"
        exit 1
        ;;
esac