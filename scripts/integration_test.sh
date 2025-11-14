#!/usr/bin/env bash

# Integration Test Setup and Runner Script
# This script helps set up and run Docker-based integration tests

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.test.yml"
POSTGRES_CONTAINER="queryhub-test-postgres"
POSTGRES_DSN="postgresql+asyncpg://testuser:testpass@localhost:5434/testdb"
MAX_WAIT=30

# Function to print colored output
print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✅${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}❌${NC} $1"
}

# Function to check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    print_success "Docker is running"
}

# Function to check if containers are running
check_containers() {
    if docker ps | grep -q "$POSTGRES_CONTAINER"; then
        return 0
    else
        return 1
    fi
}

# Function to start containers
start_containers() {
    print_info "Starting Docker containers..."
    docker-compose -f "$COMPOSE_FILE" up -d
    
    print_info "Waiting for PostgreSQL to be ready..."
    local attempts=0
    while [ $attempts -lt $MAX_WAIT ]; do
        if docker exec "$POSTGRES_CONTAINER" pg_isready -U testuser -d testdb >/dev/null 2>&1; then
            print_success "PostgreSQL is ready"
            return 0
        fi
        attempts=$((attempts + 1))
        sleep 1
        echo -n "."
    done
    
    echo ""
    print_error "PostgreSQL failed to become ready after ${MAX_WAIT} seconds"
    return 1
}

# Function to stop containers
stop_containers() {
    print_info "Stopping Docker containers..."
    docker-compose -f "$COMPOSE_FILE" down
    print_success "Containers stopped"
}

# Function to stop containers and remove volumes
cleanup_containers() {
    print_info "Stopping Docker containers and removing volumes..."
    docker-compose -f "$COMPOSE_FILE" down -v
    print_success "Containers stopped and volumes removed"
}

# Function to show container status
show_status() {
    print_info "Container status:"
    docker-compose -f "$COMPOSE_FILE" ps
}

# Function to show logs
show_logs() {
    print_info "Container logs:"
    docker-compose -f "$COMPOSE_FILE" logs "$@"
}

# Function to verify test data
verify_data() {
    print_info "Verifying test data..."
    
    echo "Sales metrics:"
    docker exec "$POSTGRES_CONTAINER" psql -U testuser -d testdb -c "SELECT COUNT(*) FROM sales_metrics;"
    
    echo -e "\nCustomer feedback:"
    docker exec "$POSTGRES_CONTAINER" psql -U testuser -d testdb -c "SELECT COUNT(*) FROM customer_feedback;"
    
    echo -e "\nSystem health:"
    docker exec "$POSTGRES_CONTAINER" psql -U testuser -d testdb -c "SELECT COUNT(*) FROM system_health;"
    
    print_success "Test data verification complete"
}

# Function to run integration tests
run_tests() {
    print_info "Running integration tests..."
    pytest tests/test_docker_integration.py -v -m integration "$@"
}

# Function to open PostgreSQL shell
open_shell() {
    print_info "Opening PostgreSQL shell..."
    docker exec -it "$POSTGRES_CONTAINER" psql -U testuser -d testdb
}

# Function to run a sample report
run_sample_report() {
    print_info "Running sample sales dashboard report..."
    export POSTGRES_DSN
    queryhub execute-report \
        --config-dir tests/fixtures/docker_integration \
        --templates-dir templates \
        sales_dashboard
}

# Main script
case "${1:-}" in
    start)
        check_docker
        start_containers
        verify_data
        ;;
    stop)
        stop_containers
        ;;
    cleanup)
        cleanup_containers
        ;;
    restart)
        stop_containers
        start_containers
        verify_data
        ;;
    status)
        check_docker
        show_status
        ;;
    logs)
        shift
        show_logs "$@"
        ;;
    verify)
        check_docker
        if ! check_containers; then
            print_error "Containers are not running. Start them first with: $0 start"
            exit 1
        fi
        verify_data
        ;;
    test)
        check_docker
        if ! check_containers; then
            print_warning "Containers are not running. Starting them now..."
            start_containers
        fi
        shift
        run_tests "$@"
        ;;
    shell)
        check_docker
        if ! check_containers; then
            print_error "Containers are not running. Start them first with: $0 start"
            exit 1
        fi
        open_shell
        ;;
    report)
        check_docker
        if ! check_containers; then
            print_error "Containers are not running. Start them first with: $0 start"
            exit 1
        fi
        run_sample_report
        ;;
    help|--help|-h)
        cat << EOF
QueryHub Integration Test Runner

Usage: $0 <command> [options]

Commands:
  start          Start Docker containers and verify test data
  stop           Stop Docker containers
  cleanup        Stop containers and remove volumes
  restart        Restart Docker containers
  status         Show container status
  logs [opts]    Show container logs (pass options to docker-compose logs)
  verify         Verify test data in database
  test [opts]    Run integration tests (pass options to pytest)
  shell          Open PostgreSQL shell
  report         Run sample sales dashboard report
  help           Show this help message

Examples:
  $0 start                          # Start containers
  $0 test                           # Run all integration tests
  $0 test -v -s                     # Run tests with verbose output
  $0 test -k "test_postgres_sales"  # Run specific test
  $0 logs -f                        # Follow container logs
  $0 shell                          # Open PostgreSQL shell
  $0 cleanup                        # Clean up everything

For more information, see: tests/fixtures/docker_integration/README.md
EOF
        ;;
    *)
        print_error "Unknown command: ${1:-}"
        echo "Run '$0 help' for usage information"
        exit 1
        ;;
esac
