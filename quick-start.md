# 🚀 Biz Design - Quick Start Guide

## 🎯 One-Command Setup

```bash
# Complete setup and start development
make quick-start
```

## 📋 Step-by-Step Setup

### 1. Initial Setup
```bash
# Setup development environment
make setup

# Or run the setup script directly
./scripts/dev-setup.sh
```

### 2. Start Development
```bash
# Start both backend and frontend
make dev

# Or start individually:
make dev-backend    # Backend only (port 8000)
make dev-frontend   # Frontend only (port 3000)
```

### 3. Verify Everything Works
```bash
# Quick health check
make health

# Comprehensive verification
make verify

# Or run scripts directly:
./scripts/health-check.sh       # Basic health check
./scripts/verify-module9.sh     # Module 9 features verification
```

## 🧪 Testing

```bash
# Run all tests
make test

# Backend tests only
make test-backend

# Frontend tests only  
make test-frontend

# E2E tests (requires dev servers running)
make test-e2e
```

## 🌐 Access URLs

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔐 Module 9 Security Features

Once running, you can access:

### Frontend Features
- **Accessibility Menu**: Click the ⚙️ button in the top-right corner
- **WCAG 2.1 AA Compliance**: Full keyboard navigation, screen reader support
- **Responsive Design**: Works on all devices

### Backend API Endpoints
- **GDPR Compliance**: `/gdpr/*`
- **Audit Logs**: `/audit/*`  
- **Rate Limiting**: `/admin/rate-limits/*`
- **Data Privacy**: `/users/data-export`, `/users/request-deletion`

## 🛠️ Available Make Commands

```bash
make help           # Show all available commands
make setup          # Install dependencies
make dev            # Start development servers
make test           # Run all tests
make health         # Check system health
make verify         # Verify Module 9 features
make clean          # Clean build artifacts
make build          # Build for production
make prod-check     # Production readiness check
```

## 🚨 Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   # Kill processes using ports 3000 and 8000
   lsof -ti:3000,8000 | xargs kill -9
   ```

2. **Dependencies issues**
   ```bash
   make clean
   make setup
   ```

3. **Permission errors**
   ```bash
   chmod +x scripts/*.sh
   ```

4. **Python/Node version issues**
   - Ensure Python 3.11+ and Node.js 18+ are installed
   - Use pyenv/nvm for version management

### Getting Help

1. **Check logs**: Look at terminal output for error messages
2. **Health check**: Run `make health` to identify issues
3. **Verification**: Run `make verify` to check Module 9 features
4. **Reset**: Run `make clean && make setup` for fresh start

## ⚡ Quick Commands for Daily Development

```bash
# Start development (most common)
make dev

# Quick test run
make quick-test

# Quick health check
make quick-check

# Open API docs
make docs
```

## 📁 Project Structure

```
biz-design-repo/
├── Makefile              # Development commands
├── scripts/              # Utility scripts
│   ├── dev-setup.sh      # Setup script
│   ├── health-check.sh   # Health verification
│   ├── verify-module9.sh # Module 9 verification
│   └── prod-check.sh     # Production readiness
├── backend/              # FastAPI backend
└── frontend/             # Next.js frontend
```

## 🎉 You're Ready!

Once setup is complete, you'll have:
- ✅ Full-stack development environment
- ✅ All Module 9 security features
- ✅ Comprehensive test suites
- ✅ WCAG 2.1 AA accessibility
- ✅ Production-ready architecture

Happy coding! 🚀