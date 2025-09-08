#!/bin/bash

# Biz Design - Production Readiness Checklist
# Comprehensive pre-production security and configuration check

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

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

log_critical() {
    echo -e "${RED}🚨 CRITICAL: $1${NC}"
}

log_section() {
    echo -e "${PURPLE}🔍 $1${NC}"
}

check_env_var() {
    local var_name=$1
    local file=$2
    local critical=${3:-false}
    
    if grep -q "^${var_name}=" "$file" 2>/dev/null; then
        value=$(grep "^${var_name}=" "$file" | cut -d'=' -f2- | sed 's/^"\(.*\)"$/\1/')
        if [ -z "$value" ] || [ "$value" = "your-key-here" ] || [ "$value" = "change-me" ]; then
            if [ "$critical" = true ]; then
                log_critical "$var_name is not set or has placeholder value"
                return 1
            else
                log_warning "$var_name is not set or has placeholder value"
                return 1
            fi
        else
            log_success "$var_name is configured"
            return 0
        fi
    else
        if [ "$critical" = true ]; then
            log_critical "$var_name is missing from $file"
            return 1
        else
            log_warning "$var_name is missing from $file"
            return 1
        fi
    fi
}

echo "🚀 Production Readiness Checklist"
echo "================================="
echo ""

critical_issues=0
warnings=0

# Environment Configuration
log_section "Environment Configuration"

# Backend environment
if [ -f "backend/.env" ]; then
    log_info "Checking backend environment variables..."
    
    # Critical variables
    check_env_var "DATABASE_URL" "backend/.env" true || ((critical_issues++))
    check_env_var "JWT_SECRET_KEY" "backend/.env" true || ((critical_issues++))
    check_env_var "ENCRYPTION_MASTER_KEY" "backend/.env" true || ((critical_issues++))
    
    # Important variables
    check_env_var "REDIS_URL" "backend/.env" false || ((warnings++))
    check_env_var "GEMINI_API_KEY" "backend/.env" false || ((warnings++))
    check_env_var "SENDGRID_API_KEY" "backend/.env" false || ((warnings++))
    
    # Check environment setting
    if grep -q "ENVIRONMENT=production" "backend/.env" 2>/dev/null; then
        log_success "Environment set to production"
    else
        log_warning "Environment not set to production"
        ((warnings++))
    fi
    
else
    log_critical "Backend .env file missing"
    ((critical_issues++))
fi

# Frontend environment
if [ -f "frontend/.env.local" ]; then
    log_info "Checking frontend environment variables..."
    check_env_var "NEXT_PUBLIC_API_URL" "frontend/.env.local" true || ((critical_issues++))
else
    log_critical "Frontend .env.local file missing"
    ((critical_issues++))
fi

echo ""

# Security Configuration
log_section "Security Configuration"

# Check for development secrets
log_info "Checking for development/test secrets..."

if grep -r "dev-.*key\|test-.*key\|change-me\|your-.*-here" backend/.env frontend/.env.local 2>/dev/null; then
    log_critical "Development/test secrets found in environment files"
    ((critical_issues++))
else
    log_success "No development secrets detected"
fi

# Check password/key strength
log_info "Checking secret strength..."

if [ -f "backend/.env" ]; then
    jwt_key=$(grep "JWT_SECRET_KEY=" backend/.env | cut -d'=' -f2- | sed 's/^"\(.*\)"$/\1/')
    if [ ${#jwt_key} -lt 32 ]; then
        log_critical "JWT secret key too short (< 32 characters)"
        ((critical_issues++))
    else
        log_success "JWT secret key length acceptable"
    fi
    
    enc_key=$(grep "ENCRYPTION_MASTER_KEY=" backend/.env | cut -d'=' -f2- | sed 's/^"\(.*\)"$/\1/')
    if [ ${#enc_key} -lt 32 ]; then
        log_critical "Encryption master key too short (< 32 characters)"
        ((critical_issues++))
    else
        log_success "Encryption master key length acceptable"
    fi
fi

echo ""

# Code Security
log_section "Code Security Analysis"

# Check for hardcoded secrets
log_info "Scanning for hardcoded secrets..."

secret_patterns=(
    "password.*=.*[\"'][^\"']{8,}[\"']"
    "api.*key.*=.*[\"'][^\"']{20,}[\"']"
    "secret.*=.*[\"'][^\"']{16,}[\"']"
    "token.*=.*[\"'][^\"']{20,}[\"']"
)

hardcoded_secrets=false
for pattern in "${secret_patterns[@]}"; do
    if grep -r -E "$pattern" backend/app/ frontend/src/ 2>/dev/null | grep -v "your-.*-here\|change-me\|example"; then
        hardcoded_secrets=true
    fi
done

if [ "$hardcoded_secrets" = true ]; then
    log_critical "Potential hardcoded secrets found in source code"
    ((critical_issues++))
else
    log_success "No hardcoded secrets detected"
fi

# Check for debug flags
log_info "Checking for debug configurations..."

if grep -r "debug.*=.*True\|DEBUG.*=.*True" backend/ frontend/ 2>/dev/null; then
    log_warning "Debug flags found - should be disabled in production"
    ((warnings++))
else
    log_success "No debug flags detected"
fi

echo ""

# Dependencies Security
log_section "Dependencies Security"

# Backend dependencies
log_info "Checking backend dependencies..."

if [ -f "backend/requirements.txt" ]; then
    # Check for known vulnerable packages (simplified check)
    if grep -E "requests==2\.(2[0-7]\.|1[0-9]\.|[0-9]\.)" backend/requirements.txt 2>/dev/null; then
        log_warning "Old requests version detected - may have vulnerabilities"
        ((warnings++))
    fi
    
    log_success "Requirements file exists"
else
    log_error "Backend requirements.txt missing"
    ((critical_issues++))
fi

# Frontend dependencies
log_info "Checking frontend dependencies..."

if [ -f "frontend/package.json" ]; then
    log_success "Package.json exists"
    
    # Check for audit
    if command -v npm &> /dev/null; then
        cd frontend
        if npm audit --audit-level high &> /dev/null; then
            log_success "No high-severity vulnerabilities in frontend dependencies"
        else
            log_warning "High-severity vulnerabilities found in frontend dependencies"
            ((warnings++))
        fi
        cd ..
    fi
else
    log_error "Frontend package.json missing"
    ((critical_issues++))
fi

echo ""

# HTTPS and Security Headers
log_section "Security Headers & HTTPS"

# Check CORS configuration
log_info "Checking CORS configuration..."

if grep -A 5 "CORSMiddleware" backend/main.py | grep -q "allow_origins.*\*"; then
    log_critical "CORS allows all origins (*) - security risk"
    ((critical_issues++))
else
    log_success "CORS configuration appears restricted"
fi

# Check for security headers middleware
if grep -q "security.*headers\|helmet" backend/main.py frontend/next.config.js 2>/dev/null; then
    log_success "Security headers middleware detected"
else
    log_warning "No security headers middleware detected"
    ((warnings++))
fi

echo ""

# Database & Storage
log_section "Database & Storage Security"

# Check database URL
if [ -f "backend/.env" ] && grep -q "sqlite://" backend/.env 2>/dev/null; then
    log_warning "SQLite detected - consider PostgreSQL for production"
    ((warnings++))
elif [ -f "backend/.env" ] && grep -q "postgresql://" backend/.env 2>/dev/null; then
    log_success "PostgreSQL database configured"
fi

# Check for database migrations
if [ -d "backend/alembic" ] && [ -f "backend/alembic.ini" ]; then
    log_success "Database migrations configured"
else
    log_warning "Database migrations not found"
    ((warnings++))
fi

echo ""

# Monitoring & Logging
log_section "Monitoring & Logging"

# Check for logging configuration
if grep -q "logging\|logger" backend/main.py backend/app/core/config.py 2>/dev/null; then
    log_success "Logging configuration detected"
else
    log_warning "No logging configuration detected"
    ((warnings++))
fi

# Check for health endpoints
if grep -q "/health" backend/main.py 2>/dev/null; then
    log_success "Health check endpoints configured"
else
    log_warning "No health check endpoints found"
    ((warnings++))
fi

echo ""

# Backup & Recovery
log_section "Backup & Recovery"

log_info "Checking backup procedures..."
if [ -f "scripts/backup.sh" ] || [ -f "docs/backup.md" ]; then
    log_success "Backup procedures documented"
else
    log_warning "No backup procedures found"
    ((warnings++))
fi

echo ""

# Final Assessment
log_section "Production Readiness Assessment"

echo ""
echo "📊 Summary:"
echo "==========="
echo ""

if [ "$critical_issues" -eq 0 ] && [ "$warnings" -eq 0 ]; then
    log_success "🎉 PRODUCTION READY! No issues detected."
    echo ""
    echo "✅ All critical security checks passed"
    echo "✅ No warnings detected"
    echo "✅ Configuration appears secure"
    echo ""
    echo "🚀 Ready for production deployment!"
    exit 0
elif [ "$critical_issues" -eq 0 ]; then
    log_success "✅ MOSTLY READY - Only warnings detected"
    echo ""
    echo "✅ All critical security checks passed"
    echo "⚠️  $warnings warning(s) detected"
    echo ""
    echo "🟡 Consider addressing warnings before production deployment"
    echo ""
    log_info "Recommended actions:"
    echo "1. Review and address all warnings above"
    echo "2. Run security audit: npm audit, pip-audit"
    echo "3. Test in staging environment"
    echo "4. Set up monitoring and alerting"
    exit 0
else
    log_error "❌ NOT PRODUCTION READY - Critical issues detected"
    echo ""
    echo "❌ $critical_issues critical issue(s) detected"
    echo "⚠️  $warnings warning(s) detected"
    echo ""
    echo "🛑 MUST fix critical issues before production deployment"
    echo ""
    log_critical "Required actions:"
    echo "1. Fix ALL critical issues listed above"
    echo "2. Address security warnings"
    echo "3. Re-run this check: make prod-check"
    echo "4. Test thoroughly in staging environment"
    exit 1
fi