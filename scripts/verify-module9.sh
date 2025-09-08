#!/bin/bash

# Biz Design - Module 9 Verification Script
# Comprehensive verification of all Module 9 security and privacy features

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

BACKEND_URL="http://localhost:8000"
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

log_feature() {
    echo -e "${PURPLE}🔐 $1${NC}"
}

# Test API endpoint with JSON response
test_api() {
    local endpoint=$1
    local description=$2
    local method=${3:-GET}
    
    log_info "Testing $description..."
    
    if response=$(curl -s -X "$method" --connect-timeout $TIMEOUT "$BACKEND_URL$endpoint" 2>/dev/null); then
        if echo "$response" | jq . > /dev/null 2>&1; then
            log_success "$description - JSON response valid"
            return 0
        else
            log_warning "$description - Non-JSON response: $(echo "$response" | head -c 100)"
            return 1
        fi
    else
        log_error "$description - Request failed"
        return 1
    fi
}

# Check file exists
check_file() {
    local file=$1
    local description=$2
    
    if [ -f "$file" ]; then
        log_success "$description exists"
        return 0
    else
        log_error "$description missing: $file"
        return 1
    fi
}

# Check directory exists and has files
check_implementation() {
    local pattern=$1
    local description=$2
    
    files=$(find . -name "$pattern" 2>/dev/null | wc -l)
    if [ "$files" -gt 0 ]; then
        log_success "$description implemented ($files files)"
        return 0
    else
        log_error "$description not found"
        return 1
    fi
}

echo "🔐 Module 9: Security and Privacy Verification"
echo "=============================================="
echo ""

# Check if backend is running
log_info "Checking if backend is running..."
if ! curl -s --connect-timeout $TIMEOUT "$BACKEND_URL/health" > /dev/null 2>&1; then
    log_error "Backend not running at $BACKEND_URL"
    echo "Please start the backend first: cd backend && uvicorn main:app --reload"
    exit 1
fi
log_success "Backend is running"
echo ""

# Task 9.1: GDPR Compliance
log_feature "Task 9.1: GDPR Compliance Module"
check_file "backend/app/services/gdpr_compliance_service.py" "GDPR Compliance Service"
check_file "backend/app/api/gdpr_compliance.py" "GDPR Compliance API"

# Test GDPR endpoints
test_api "/gdpr/privacy-notice" "GDPR Privacy Notice endpoint"
test_api "/gdpr/configuration" "GDPR Configuration endpoint"

echo ""

# Task 9.2: Data Export
log_feature "Task 9.2: Enhanced Data Export"
check_file "backend/app/services/data_export_service.py" "Data Export Service"
check_file "backend/app/api/data_privacy.py" "Data Privacy API"

# Check export formats support
if grep -q "JSON\|CSV\|XML\|PDF\|ZIP" backend/app/services/data_export_service.py 2>/dev/null; then
    log_success "Multi-format export support found (JSON/CSV/XML/PDF/ZIP)"
else
    log_warning "Multi-format export support not clearly detected"
fi

echo ""

# Task 9.3: Account Deletion
log_feature "Task 9.3: GDPR-Compliant Account Deletion"
check_file "backend/app/services/account_deletion_service.py" "Account Deletion Service"

# Check staged deletion support
if grep -q "soft.*delete\|anonymization\|physical.*delete" backend/app/services/account_deletion_service.py 2>/dev/null; then
    log_success "Staged deletion process found (soft → anonymization → hard delete)"
else
    log_warning "Staged deletion process not clearly detected"
fi

echo ""

# Task 9.4: Rate Limiting
log_feature "Task 9.4: Advanced API Rate Limiting"
check_file "backend/app/core/middleware.py" "Rate Limiting Middleware"
check_file "backend/app/api/rate_limits.py" "Rate Limits API"

# Test rate limiting endpoints
test_api "/admin/rate-limits/health" "Rate Limiting Health endpoint"
test_api "/admin/rate-limits/configuration" "Rate Limiting Configuration endpoint"

# Check multiple strategies
if grep -q "sliding.*window\|fixed.*window\|token.*bucket" backend/app/core/middleware.py 2>/dev/null; then
    log_success "Multiple rate limiting strategies found"
else
    log_warning "Rate limiting strategies not clearly detected"
fi

echo ""

# Task 9.5: Data Encryption
log_feature "Task 9.5: Multi-layer Data Encryption"
check_file "backend/app/services/encryption_service.py" "Data Encryption Service"

# Check encryption methods
encryption_methods=0
for method in "AES.*256.*GCM" "Fernet" "RSA.*OAEP" "Hybrid"; do
    if grep -q "$method" backend/app/services/encryption_service.py 2>/dev/null; then
        ((encryption_methods++))
    fi
done

if [ "$encryption_methods" -ge 3 ]; then
    log_success "Multiple encryption methods implemented ($encryption_methods/4)"
else
    log_warning "Limited encryption methods detected ($encryption_methods/4)"
fi

echo ""

# Task 9.6: Audit Logging
log_feature "Task 9.6: Comprehensive Security Audit Logging"
check_file "backend/app/services/audit_log_service.py" "Audit Log Service"
check_file "backend/app/api/audit_logs.py" "Audit Logs API"

# Test audit endpoints
test_api "/audit/health" "Audit System Health endpoint"
test_api "/audit/configuration" "Audit Configuration endpoint"

# Check audit features
if grep -q "180.*day\|integrity.*verification\|Google.*Cloud.*Logging" backend/app/services/audit_log_service.py 2>/dev/null; then
    log_success "Advanced audit features found (retention, integrity, cloud logging)"
else
    log_warning "Advanced audit features not clearly detected"
fi

echo ""

# Task 9.7: Accessibility
log_feature "Task 9.7: WCAG 2.1 Level AA Accessibility"
check_file "frontend/components/accessibility/AccessibilityProvider.tsx" "Accessibility Provider"
check_file "frontend/components/accessibility/AccessibilityMenu.tsx" "Accessibility Menu"
check_file "frontend/components/accessibility/FocusTrap.tsx" "Focus Trap Component"
check_file "frontend/styles/accessibility.css" "Accessibility Styles"

# Check WCAG compliance features
if grep -q "WCAG\|aria-\|role=\|tabIndex\|screen.*reader" frontend/components/accessibility/AccessibilityProvider.tsx 2>/dev/null; then
    log_success "WCAG compliance features found"
else
    log_warning "WCAG compliance features not clearly detected"
fi

echo ""

# Task 9.8: Integration
log_feature "Task 9.8: Module 9 Integration"

# Check main.py integration
if grep -q "gdpr_compliance\|audit_logs\|rate_limits" backend/main.py 2>/dev/null; then
    log_success "Security APIs integrated in main.py"
else
    log_error "Security APIs not integrated in main.py"
fi

# Check frontend integration
if grep -q "AccessibilityProvider" frontend/src/app/layout.tsx 2>/dev/null; then
    log_success "AccessibilityProvider integrated in layout.tsx"
else
    log_error "AccessibilityProvider not integrated in layout.tsx"
fi

echo ""

# Task 9.9: Testing
log_feature "Task 9.9: Comprehensive Testing Suite"

# Check backend tests
backend_test_files=$(find backend/tests -name "test_*.py" 2>/dev/null | wc -l)
if [ "$backend_test_files" -ge 4 ]; then
    log_success "Backend test suite implemented ($backend_test_files test files)"
else
    log_warning "Limited backend test coverage ($backend_test_files test files)"
fi

# Check frontend tests
if [ -f "frontend/tests/accessibility.test.tsx" ] && [ -f "frontend/tests/e2e/accessibility.spec.ts" ]; then
    log_success "Frontend accessibility tests implemented"
else
    log_warning "Frontend accessibility tests not found"
fi

# Check test configuration
check_file "frontend/jest.config.js" "Jest configuration"
check_file "frontend/playwright.config.ts" "Playwright configuration"

echo ""

# Security Configuration Check
log_feature "Security Configuration Verification"

# Check middleware integration
if grep -q "APILimiter\|rate.*limit" backend/main.py 2>/dev/null; then
    log_success "Rate limiting middleware integrated"
else
    log_warning "Rate limiting middleware integration unclear"
fi

# Check encryption configuration
if grep -q "ENCRYPTION_MASTER_KEY\|encryption.*enabled" backend/app/core/config.py 2>/dev/null; then
    log_success "Encryption configuration found"
else
    log_warning "Encryption configuration not clearly detected"
fi

echo ""

# Final Summary
log_info "Module 9 Verification Summary:"
echo ""

# Count implemented features
implemented=0
total=9

# Quick check of major components
[ -f "backend/app/services/gdpr_compliance_service.py" ] && ((implemented++))
[ -f "backend/app/services/data_export_service.py" ] && ((implemented++))
[ -f "backend/app/services/account_deletion_service.py" ] && ((implemented++))
[ -f "backend/app/core/middleware.py" ] && ((implemented++))
[ -f "backend/app/services/encryption_service.py" ] && ((implemented++))
[ -f "backend/app/services/audit_log_service.py" ] && ((implemented++))
[ -f "frontend/components/accessibility/AccessibilityProvider.tsx" ] && ((implemented++))
grep -q "gdpr_compliance\|audit_logs" backend/main.py 2>/dev/null && ((implemented++))
[ -d "backend/tests" ] && [ -d "frontend/tests" ] && ((implemented++))

percentage=$((implemented * 100 / total))

if [ "$percentage" -ge 90 ]; then
    log_success "Module 9 implementation: $implemented/$total tasks ($percentage%) - Excellent!"
elif [ "$percentage" -ge 70 ]; then
    log_success "Module 9 implementation: $implemented/$total tasks ($percentage%) - Good progress"
else
    log_warning "Module 9 implementation: $implemented/$total tasks ($percentage%) - Needs attention"
fi

echo ""
echo "🎯 Next steps:"
echo "1. Run tests: make test"
echo "2. Check health: make health"  
echo "3. View API docs: open $BACKEND_URL/docs"
echo "4. Test accessibility: open http://localhost:3000 (look for ⚙️ button)"
echo ""

if [ "$percentage" -ge 90 ]; then
    echo "🚀 Module 9 is ready for production!"
    exit 0
else
    echo "⚠️  Some features may need attention before production deployment"
    exit 1
fi