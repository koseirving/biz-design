# Biz Design - Development & Testing Makefile
.PHONY: help setup dev test clean build deploy health

# Default target
help: ## Show this help message
	@echo "Biz Design - AI-powered Business Framework Learning Platform"
	@echo ""
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""

# Development Setup
setup: ## Install all dependencies (backend + frontend)
	@echo "🚀 Setting up Biz Design development environment..."
	@make setup-backend
	@make setup-frontend
	@echo "✅ Setup complete!"

setup-backend: ## Install backend dependencies
	@echo "📦 Installing backend dependencies..."
	@cd backend && python -m venv venv
	@cd backend && . venv/bin/activate && pip install --upgrade pip
	@cd backend && . venv/bin/activate && pip install -r requirements.txt
	@echo "✅ Backend dependencies installed"

setup-frontend: ## Install frontend dependencies
	@echo "📦 Installing frontend dependencies..."
	@cd frontend && npm install
	@echo "✅ Frontend dependencies installed"

# Development
dev: ## Start both backend and frontend in development mode
	@echo "🚀 Starting development servers..."
	@make dev-parallel

dev-parallel: ## Start backend and frontend in parallel
	@trap 'kill 0' INT; \
	make dev-backend & \
	make dev-frontend & \
	wait

dev-backend: ## Start backend development server
	@echo "🔧 Starting backend server on http://localhost:8000..."
	@cd backend && . venv/bin/activate && uvicorn main:app --reload --port 8000

dev-frontend: ## Start frontend development server  
	@echo "🎨 Starting frontend server on http://localhost:3000..."
	@cd frontend && npm run dev

# Testing
test: ## Run all tests (backend + frontend)
	@echo "🧪 Running all tests..."
	@make test-backend
	@make test-frontend
	@echo "✅ All tests completed"

test-backend: ## Run backend tests
	@echo "🧪 Running backend tests..."
	@cd backend && . venv/bin/activate && pytest tests/ -v --tb=short

test-frontend: ## Run frontend tests
	@echo "🧪 Running frontend unit tests..."
	@cd frontend && npm test -- --watchAll=false

test-e2e: ## Run E2E tests (requires dev servers running)
	@echo "🧪 Running E2E tests..."
	@cd frontend && npm run test:e2e

test-accessibility: ## Run accessibility tests
	@echo "♿ Running accessibility tests..."
	@cd frontend && npm test -- --testPathPattern=accessibility --watchAll=false

# Health Checks
health: ## Check system health and API endpoints
	@echo "🏥 Checking system health..."
	@./scripts/health-check.sh

health-backend: ## Check backend health
	@echo "🏥 Checking backend health..."
	@curl -f http://localhost:8000/health || echo "❌ Backend not responding"
	@curl -f http://localhost:8000/audit/health || echo "❌ Audit system not responding"
	@curl -f http://localhost:8000/admin/rate-limits/health || echo "❌ Rate limiting not responding"

health-frontend: ## Check frontend health
	@echo "🏥 Checking frontend health..."
	@curl -f http://localhost:3000 > /dev/null || echo "❌ Frontend not responding"

# Quick Verification
verify: ## Quick verification of all Module 9 features
	@echo "🔍 Verifying Module 9 implementation..."
	@./scripts/verify-module9.sh

demo: ## Start demo environment with sample data
	@echo "🎭 Starting demo environment..."
	@make setup-demo-data
	@make dev

# Database
db-reset: ## Reset database (development only)
	@echo "🗄️  Resetting database..."
	@cd backend && . venv/bin/activate && alembic downgrade base
	@cd backend && . venv/bin/activate && alembic upgrade head
	@echo "✅ Database reset complete"

db-migrate: ## Run database migrations
	@echo "🗄️  Running database migrations..."
	@cd backend && . venv/bin/activate && alembic upgrade head

# Linting and Formatting
lint: ## Run linters for both backend and frontend
	@make lint-backend
	@make lint-frontend

lint-backend: ## Run backend linting
	@echo "🧹 Linting backend code..."
	@cd backend && . venv/bin/activate && python -m flake8 app/
	@cd backend && . venv/bin/activate && python -m black --check app/

lint-frontend: ## Run frontend linting
	@echo "🧹 Linting frontend code..."
	@cd frontend && npm run lint

format: ## Format code (backend + frontend)
	@make format-backend
	@make format-frontend

format-backend: ## Format backend code
	@echo "🎨 Formatting backend code..."
	@cd backend && . venv/bin/activate && python -m black app/

format-frontend: ## Format frontend code
	@echo "🎨 Formatting frontend code..."
	@cd frontend && npm run lint -- --fix

# Build
build: ## Build production versions
	@echo "🏗️  Building production versions..."
	@make build-backend
	@make build-frontend

build-backend: ## Build backend for production
	@echo "🏗️  Building backend..."
	@cd backend && . venv/bin/activate && pip install --upgrade pip
	@echo "✅ Backend build ready"

build-frontend: ## Build frontend for production
	@echo "🏗️  Building frontend..."
	@cd frontend && npm run build
	@echo "✅ Frontend build complete"

# Clean
clean: ## Clean build artifacts and dependencies
	@echo "🧹 Cleaning up..."
	@rm -rf backend/venv
	@rm -rf backend/__pycache__
	@rm -rf backend/**/__pycache__
	@rm -rf backend/**/**/__pycache__
	@rm -rf frontend/node_modules
	@rm -rf frontend/.next
	@rm -rf frontend/out
	@echo "✅ Cleanup complete"

# Docker
docker-build: ## Build Docker images
	@echo "🐳 Building Docker images..."
	@cd backend && docker build -t biz-design-backend .
	@cd frontend && docker build -t biz-design-frontend .

docker-run: ## Run Docker containers
	@echo "🐳 Running Docker containers..."
	@docker-compose up -d

docker-stop: ## Stop Docker containers
	@docker-compose down

# Security
security-check: ## Run security checks
	@echo "🔒 Running security checks..."
	@cd backend && . venv/bin/activate && pip-audit
	@cd frontend && npm audit

# Git helpers
git-status: ## Show git status with summary
	@echo "📊 Git Status Summary:"
	@git status --porcelain | wc -l | xargs echo "Modified files:"
	@git log --oneline -5
	@echo ""
	@git status

# Quick commands for daily development
quick-start: setup dev ## Quick setup and start development

quick-test: ## Quick test run (essential tests only)
	@cd backend && . venv/bin/activate && pytest tests/test_basic_integration.py -v
	@cd frontend && npm test -- --testPathPattern=accessibility --watchAll=false

quick-check: health verify ## Quick health check and verification

# Documentation
docs: ## Open API documentation
	@echo "📚 Opening API documentation..."
	@open http://localhost:8000/docs || xdg-open http://localhost:8000/docs || echo "Visit http://localhost:8000/docs"

# Production helpers
prod-check: ## Pre-production checklist
	@echo "🚀 Production readiness check..."
	@./scripts/prod-check.sh

setup-demo-data: ## Setup demo data for testing
	@echo "🎭 Setting up demo data..."
	@cd backend && . venv/bin/activate && python -c "print('Demo data setup - implement as needed')"