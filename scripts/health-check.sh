#!/bin/bash

# Biz Design - Health Check Script
# Comprehensive health check for all services and Module 9 features

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
BACKEND_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:3000"
TIMEOUT=5

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

# Test HTTP endpoint
test_endpoint() {
    local url=$1
    local name=$2
    local expected_code=${3:-200}
    
    log_info "Testing $name..."
    
    if response=$(curl -s -w "HTTPSTATUS:%{http_code}" --connect-timeout $TIMEOUT "$url" 2>/dev/null); then
        http_code=$(echo $response | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
        body=$(echo $response | sed -e 's/HTTPSTATUS:.*//g')
        
        if [ "$http_code" -eq "$expected_code" ]; then
            log_success "$name (HTTP $http_code)"
            return 0
        else
            log_warning "$name (HTTP $http_code, expected $expected_code)"
            return 1
        fi
    else
        log_error "$name (Connection failed)"
        return 1
    fi
}

# Check if service is running
check_service() {
    local url=$1
    local name=$2
    
    if curl -s --connect-timeout $TIMEOUT "$url" > /dev/null 2>&1; then
        log_success "$name is running"
        return 0
    else
        log_error "$name is not responding"
        return 1
    fi
}

echo "🏥 Biz Design Health Check"
echo "=========================="
echo ""

# Basic service checks
log_info "Checking core services..."

BACKEND_RUNNING=false
FRONTEND_RUNNING=false

if check_service "$BACKEND_URL/health" "Backend Service"; then
    BACKEND_RUNNING=true
fi

if check_service "$FRONTEND_URL" "Frontend Service"; then
    FRONTEND_RUNNING=true
fi

echo ""

# Backend API endpoints
if [ "$BACKEND_RUNNING" = true ]; then
    log_info "Testing backend API endpoints..."
    
    # Core endpoints
    test_endpoint "$BACKEND_URL/" "Root endpoint"
    test_endpoint "$BACKEND_URL/health" "Health endpoint"
    
    # Module 9 Security endpoints
    log_info "Testing Module 9 security endpoints..."
    test_endpoint "$BACKEND_URL/gdpr/privacy-notice" "GDPR Privacy Notice"
    test_endpoint "$BACKEND_URL/audit/health" "Audit System Health"
    test_endpoint "$BACKEND_URL/admin/rate-limits/health" "Rate Limiting Health"
    
    # API Documentation
    test_endpoint "$BACKEND_URL/docs" "OpenAPI Documentation"
    test_endpoint "$BACKEND_URL/redoc" "ReDoc Documentation"
    
    echo ""
    
    # Test backend functionality
    log_info "Testing backend functionality..."
    
    # Test JSON response format
    if health_response=$(curl -s "$BACKEND_URL/health" 2>/dev/null); then
        if echo "$health_response" | jq . > /dev/null 2>&1; then
            log_success "JSON responses working"
            
            # Check health response content
            status=$(echo "$health_response" | jq -r '.status' 2>/dev/null || echo "unknown")
            service=$(echo "$health_response" | jq -r '.service' 2>/dev/null || echo "unknown")
            
            if [ "$status" = "healthy" ] && [ "$service" = "biz-design-backend" ]; then
                log_success "Health response format correct"
            else
                log_warning "Health response format unexpected (status: $status, service: $service)"
            fi
        else
            log_error "Invalid JSON response from health endpoint"
        fi
    fi
    
else
    log_error "Skipping backend tests - service not running"
fi

echo ""

# Frontend checks
if [ "$FRONTEND_RUNNING" = true ]; then
    log_info "Testing frontend functionality..."
    
    # Check if it's a Next.js app
    if response=$(curl -s "$FRONTEND_URL" 2>/dev/null); then
        if echo "$response" | grep -q "Next.js" || echo "$response" | grep -q "_next"; then
            log_success "Next.js application detected"
        else
            log_info "Frontend responding (Next.js detection inconclusive)"
        fi
    fi
    
    # Check for accessibility features (look for specific class names or elements)
    if echo "$response" | grep -q "accessibility" || echo "$response" | grep -q "sr-only"; then
        log_success "Accessibility features detected in HTML"
    else
        log_info "Accessibility features not detected in initial HTML (may load dynamically)"
    fi
    
else
    log_error "Skipping frontend tests - service not running"
fi

echo ""

# System resource checks
log_info "Checking system resources..."

# Check disk space
disk_usage=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$disk_usage" -lt 90 ]; then
    log_success "Disk usage: $disk_usage%"
else
    log_warning "Disk usage high: $disk_usage%"
fi

# Check if Python processes are running
python_processes=$(ps aux | grep -c "python.*uvicorn\|python.*main" | grep -v grep || echo 0)
if [ "$python_processes" -gt 0 ]; then
    log_success "$python_processes Python backend process(es) running"
else
    log_warning "No Python backend processes detected"
fi

# Check if Node.js processes are running  
node_processes=$(ps aux | grep -c "node.*next" | grep -v grep || echo 0)
if [ "$node_processes" -gt 0 ]; then
    log_success "$node_processes Node.js frontend process(es) running"
else
    log_warning "No Node.js frontend processes detected"
fi

echo ""

# Summary
log_info "Health check summary:"
if [ "$BACKEND_RUNNING" = true ] && [ "$FRONTEND_RUNNING" = true ]; then
    log_success "All core services are running"
    
    echo ""
    echo "🌐 Access URLs:"
    echo "   Frontend:  $FRONTEND_URL"
    echo "   Backend:   $BACKEND_URL"
    echo "   API Docs:  $BACKEND_URL/docs"
    
    echo ""
    echo "🔐 Module 9 Security Features Available:"
    echo "   GDPR Compliance:  $BACKEND_URL/gdpr/"
    echo "   Audit Logs:       $BACKEND_URL/audit/"
    echo "   Rate Limiting:    $BACKEND_URL/admin/rate-limits/"
    
    exit 0
elif [ "$BACKEND_RUNNING" = true ]; then
    log_warning "Backend running but frontend not responding"
    echo "Try: cd frontend && npm run dev"
    exit 1
elif [ "$FRONTEND_RUNNING" = true ]; then
    log_warning "Frontend running but backend not responding" 
    echo "Try: cd backend && uvicorn main:app --reload"
    exit 1
else
    log_error "Neither service is responding"
    echo "Try: make dev"
    exit 1
fi