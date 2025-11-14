#!/usr/bin/env bash
# QueryHub Docker Build Script
# Builds a standalone executable distribution using Docker
#
# Usage:
#   ./scripts/build_docker.sh [OUTPUT_DIR]
#
# OUTPUT_DIR: Optional directory to place the distribution (default: ./dist)

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
OUTPUT_DIR="${1:-$PROJECT_ROOT/dist}"
BUILD_TAG="queryhub-builder:latest"
DIST_TAG="queryhub-dist:latest"

# Functions
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

print_header() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║        QueryHub Docker Build System                        ║"
    echo "║        Building Standalone Executable                       ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        exit 1
    fi
    
    log_success "Docker is available"
}

build_executable() {
    log_info "Building Docker image with PyInstaller..."
    
    cd "$PROJECT_ROOT"
    
    # Build the multi-stage Docker image
    docker build \
        --target packager-dist \
        --tag "$DIST_TAG" \
        --file Dockerfile \
        . || {
            log_error "Docker build failed"
            exit 1
        }
    
    log_success "Docker image built successfully"
}

extract_distribution() {
    log_info "Extracting distribution files..."
    
    # Create output directory
    mkdir -p "$OUTPUT_DIR"
    
    # Create temporary container
    local container_id
    container_id=$(docker create "$DIST_TAG")
    
    # Extract all files from the container
    docker cp "$container_id:/." "$OUTPUT_DIR/" || {
        log_error "Failed to extract distribution files"
        docker rm "$container_id" &> /dev/null
        exit 1
    }
    
    # Clean up container
    docker rm "$container_id" &> /dev/null
    
    log_success "Distribution extracted to: $OUTPUT_DIR"
}

make_executable() {
    log_info "Setting executable permissions..."
    
    # Make the binary executable (Unix systems)
    if [[ -f "$OUTPUT_DIR/queryhub" ]]; then
        chmod +x "$OUTPUT_DIR/queryhub"
        log_success "Made queryhub executable"
    fi
    
    # Make wrapper scripts executable
    if [[ -f "$OUTPUT_DIR/queryhub.sh" ]]; then
        chmod +x "$OUTPUT_DIR/queryhub.sh"
        log_success "Made queryhub.sh executable"
    fi
}

create_archive() {
    log_info "Creating distribution archive..."
    
    cd "$(dirname "$OUTPUT_DIR")"
    local archive_name="queryhub-$(date +%Y%m%d-%H%M%S).tar.gz"
    
    tar -czf "$archive_name" -C "$OUTPUT_DIR" . || {
        log_warning "Failed to create archive"
        return
    }
    
    log_success "Archive created: $archive_name"
}

print_summary() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║                   Build Complete!                          ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    log_info "Distribution location: $OUTPUT_DIR"
    echo ""
    echo "Contents:"
    echo "  • queryhub          - Main executable (Linux/macOS)"
    echo "  • queryhub.sh       - Unix wrapper script"
    echo "  • queryhub.bat      - Windows wrapper script"
    echo "  • templates/        - HTML templates"
    echo "  • config/           - Configuration examples"
    echo "  • examples/         - Additional samples"
    echo "  • README.md         - Full documentation"
    echo "  • DISTRIBUTION.md   - Distribution guide"
    echo "  • VERSION.txt       - Build information"
    echo ""
    echo "Quick Start:"
    echo "  cd $OUTPUT_DIR"
    echo "  ./queryhub --help"
    echo ""
    echo "To test:"
    echo "  cd $OUTPUT_DIR"
    echo "  ./queryhub list-reports --config-dir config --templates-dir templates"
    echo ""
}

# Main execution
main() {
    print_header
    
    log_info "Project root: $PROJECT_ROOT"
    log_info "Output directory: $OUTPUT_DIR"
    echo ""
    
    check_docker
    build_executable
    extract_distribution
    make_executable
    create_archive
    print_summary
}

# Run main function
main "$@"
