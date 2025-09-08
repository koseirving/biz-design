#!/bin/bash

# Biz Design - Development Environment Setup Script
# This script sets up the complete development environment

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if we're in the right directory
if [ ! -f "Makefile" ] || [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    log_error "Please run this script from the project root directory"
    exit 1
fi

log_info "Starting Biz Design development environment setup..."

# Check prerequisites
log_info "Checking prerequisites..."

# Check Python
if ! command -v python3 &> /dev/null; then
    log_error "Python 3 is required but not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
log_success "Python $PYTHON_VERSION found"

# Check Node.js
if ! command -v node &> /dev/null; then
    log_error "Node.js is required but not installed"
    exit 1
fi

NODE_VERSION=$(node --version)
log_success "Node.js $NODE_VERSION found"

# Check npm
if ! command -v npm &> /dev/null; then
    log_error "npm is required but not installed"
    exit 1
fi

NPM_VERSION=$(npm --version)
log_success "npm $NPM_VERSION found"

# Setup backend
log_info "Setting up backend environment..."

cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    log_info "Creating Python virtual environment..."
    python3 -m venv venv
    log_success "Virtual environment created"
else
    log_success "Virtual environment already exists"
fi

# Activate virtual environment and install dependencies
log_info "Installing backend dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
log_success "Backend dependencies installed"

# Check if we can import the main app
log_info "Verifying backend installation..."
if python -c "import app; print('✅ Backend modules import successfully')" 2>/dev/null; then
    log_success "Backend verification passed"
else
    log_warning "Backend verification failed - some modules may have issues"
fi

cd ..

# Setup frontend
log_info "Setting up frontend environment..."

cd frontend

# Install dependencies
log_info "Installing frontend dependencies..."
npm install
log_success "Frontend dependencies installed"

# Check if build works
log_info "Verifying frontend installation..."
if npm run lint &> /dev/null; then
    log_success "Frontend verification passed"
else
    log_warning "Frontend linting has issues - may need attention"
fi

cd ..

# Create environment files if they don't exist
log_info "Setting up environment files..."

# Backend .env
if [ ! -f "backend/.env" ]; then
    log_info "Creating backend .env file..."
    cat > backend/.env << EOF
# Development Environment Configuration
DATABASE_URL=sqlite:///./dev.db
REDIS_URL=redis://localhost:6379
JWT_SECRET_KEY=dev-jwt-secret-key-change-in-production
ENCRYPTION_MASTER_KEY=dev-master-key-32-chars-long!!!
ENVIRONMENT=development

# API Keys (add your keys here)
GEMINI_API_KEY=your-gemini-api-key-here
SENDGRID_API_KEY=your-sendgrid-key-here

# Optional: GCP Settings
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
EOF
    log_success "Backend .env created"
else
    log_success "Backend .env already exists"
fi

# Frontend .env.local
if [ ! -f "frontend/.env.local" ]; then
    log_info "Creating frontend .env.local file..."
    cat > frontend/.env.local << EOF
# Development Environment Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_URL=http://localhost:3000
NEXT_PUBLIC_ENVIRONMENT=development
EOF
    log_success "Frontend .env.local created"
else
    log_success "Frontend .env.local already exists"
fi

# Create scripts directory if it doesn't exist
mkdir -p scripts

log_success "🎉 Development environment setup complete!"
echo ""
log_info "Next steps:"
echo "1. Start development servers: make dev"
echo "2. Run tests: make test"
echo "3. Check health: make health"
echo "4. View API docs: open http://localhost:8000/docs"
echo ""
log_warning "Note: Update API keys in .env files for full functionality"