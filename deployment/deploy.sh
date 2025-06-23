#!/bin/bash
# Calgary Analytica Deployment Script
# Production deployment automation

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="calgary-analytica"
DOCKER_IMAGE="${PROJECT_NAME}:latest"
BACKUP_DIR="./backups"
LOG_FILE="deployment.log"

# Functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    echo "[ERROR] $1" >> "$LOG_FILE"
    exit 1
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
    echo "[SUCCESS] $1" >> "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
    echo "[WARNING] $1" >> "$LOG_FILE"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed or not in PATH"
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed or not in PATH"
    fi
    
    # Check if running as root (not recommended)
    if [[ $EUID -eq 0 ]]; then
        warning "Running as root is not recommended for security reasons"
    fi
    
    success "Prerequisites check passed"
}

# Create necessary directories
setup_directories() {
    log "Setting up directories..."
    
    mkdir -p "$BACKUP_DIR"
    mkdir -p data-lake
    mkdir -p data-engine/data/{raw,processed,staging}
    mkdir -p data-engine/validation/{pending,approved,rejected,logs}
    mkdir -p monitoring/logs
    
    success "Directories created"
}

# Backup existing data
backup_data() {
    log "Creating backup of existing data..."
    
    if [[ -f "data-lake/calgary_data.db" ]]; then
        BACKUP_FILE="$BACKUP_DIR/calgary_data_$(date +%Y%m%d_%H%M%S).db"
        cp "data-lake/calgary_data.db" "$BACKUP_FILE"
        success "Database backed up to $BACKUP_FILE"
    else
        log "No existing database found, skipping backup"
    fi
}

# Build Docker image
build_image() {
    log "Building Docker image..."
    
    docker build -t "$DOCKER_IMAGE" .
    
    if [[ $? -eq 0 ]]; then
        success "Docker image built successfully"
    else
        error "Failed to build Docker image"
    fi
}

# Deploy services
deploy_services() {
    log "Deploying services..."
    
    # Stop existing services
    docker-compose down 2>/dev/null || true
    
    # Start services
    docker-compose up -d
    
    if [[ $? -eq 0 ]]; then
        success "Services deployed successfully"
    else
        error "Failed to deploy services"
    fi
}

# Verify deployment
verify_deployment() {
    log "Verifying deployment..."
    
    # Wait for services to start
    sleep 10
    
    # Check service health
    if docker-compose ps | grep -q "Up"; then
        success "Services are running"
    else
        error "Services failed to start properly"
    fi
    
    # Test monitoring endpoint
    if curl -f http://localhost:8081 >/dev/null 2>&1; then
        success "Monitoring dashboard is accessible"
    else
        warning "Monitoring dashboard may not be accessible"
    fi
    
    # Run health check
    log "Running application health check..."
    if docker-compose exec -T calgary-analytica python3 monitoring/simple_monitor.py >/dev/null 2>&1; then
        success "Application health check passed"
    else
        warning "Application health check failed"
    fi
}

# Show deployment status
show_status() {
    log "Deployment Status:"
    echo ""
    echo "🏠 Calgary Analytica - Deployment Complete"
    echo "=========================================="
    echo ""
    echo "📊 Services:"
    docker-compose ps
    echo ""
    echo "🌐 Access Points:"
    echo "  • Main Application: http://localhost:8080"
    echo "  • Monitoring Dashboard: http://localhost:8081"
    echo ""
    echo "📁 Data Directories:"
    echo "  • Database: ./data-lake/calgary_data.db"
    echo "  • Raw Data: ./data-engine/data/raw/"
    echo "  • Logs: ./monitoring/logs/"
    echo ""
    echo "🛠  Management Commands:"
    echo "  • View logs: docker-compose logs -f"
    echo "  • Stop services: docker-compose down"
    echo "  • Restart: docker-compose restart"
    echo "  • Shell access: docker-compose exec calgary-analytica bash"
    echo ""
}

# Cleanup on failure
cleanup() {
    if [[ $? -ne 0 ]]; then
        error "Deployment failed. Cleaning up..."
        docker-compose down 2>/dev/null || true
    fi
}

# Main deployment flow
main() {
    echo "🏠 Calgary Analytica - Production Deployment"
    echo "==========================================="
    echo ""
    
    # Set trap for cleanup
    trap cleanup EXIT
    
    # Deployment steps
    check_prerequisites
    setup_directories
    backup_data
    build_image
    deploy_services
    verify_deployment
    show_status
    
    success "Deployment completed successfully!"
}

# Command line options
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "backup")
        log "Creating manual backup..."
        backup_data
        ;;
    "logs")
        docker-compose logs -f
        ;;
    "status")
        docker-compose ps
        ;;
    "stop")
        log "Stopping services..."
        docker-compose down
        success "Services stopped"
        ;;
    "restart")
        log "Restarting services..."
        docker-compose restart
        success "Services restarted"
        ;;
    "health")
        log "Running health check..."
        docker-compose exec calgary-analytica python3 monitoring/simple_monitor.py
        ;;
    "shell")
        log "Opening shell in container..."
        docker-compose exec calgary-analytica bash
        ;;
    "clean")
        log "Cleaning up Docker resources..."
        docker-compose down -v --rmi local
        docker system prune -f
        success "Cleanup completed"
        ;;
    *)
        echo "Calgary Analytica Deployment Script"
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  deploy    - Full deployment (default)"
        echo "  backup    - Create database backup"
        echo "  logs      - View service logs"
        echo "  status    - Show service status"
        echo "  stop      - Stop all services"
        echo "  restart   - Restart all services"
        echo "  health    - Run health check"
        echo "  shell     - Open shell in container"
        echo "  clean     - Clean up Docker resources"
        echo ""
        ;;
esac