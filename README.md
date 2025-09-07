# Biz Design - AI-powered Business Framework Learning Platform

## Overview

Biz Design is a comprehensive platform that combines AI-powered learning with business framework education. The platform provides interactive learning experiences through SWOT analysis, user journey mapping, and other business methodologies enhanced by Gemini AI.

## Architecture

- **Frontend**: Next.js 15 with TypeScript, TailwindCSS
- **Backend**: FastAPI with Python 3.11
- **Database**: PostgreSQL with SQLAlchemy
- **Cache/Queue**: Redis
- **AI**: Google Gemini API
- **Infrastructure**: Google Cloud Platform (Cloud Run, Cloud SQL, Memorystore)

## Project Structure

```
biz-design-repo/
├── frontend/          # Next.js application
├── backend/           # FastAPI application
├── spec/              # Project specifications
└── README.md
```

## Features Implemented

### ✅ Module 1: Project Setup and Foundation
- GCP project initialization
- Git repository setup
- Hello World applications
- Basic CI/CD pipeline

### ✅ Module 2: Database and User Authentication
- PostgreSQL database setup
- User registration/login with JWT
- Redis caching
- Data privacy features (GDPR compliance)

### ✅ Module 3: Core Content and Version Management
- Business framework content management
- Version control for outputs
- Auto-save functionality
- Learning session tracking

### ✅ Module 4: AI Copilot (Gemini Integration)
- Gemini API integration
- Function calling for analysis
- Interactive AI chat interface
- Output visualization

### ✅ Module 5: Premium Features and Gamification
- Company profile management
- Points and badge system
- Progress tracking
- AI-powered evaluation

### ✅ Module 7: Notification System and Ebbinghaus Review
- Redis-based notification queues
- Email notifications with SendGrid
- Spaced repetition learning system
- WebSocket real-time notifications

### ✅ Module 8: Frontend New Components
- Version history management
- Badge collection display
- Notification center
- Export functionality

### ✅ Module 9: Security and Privacy
- **GDPR Compliance**: Full consent management, data minimization
- **Data Export**: Multi-format export (JSON/CSV/XML/PDF/ZIP)
- **Account Deletion**: Staged deletion process (soft → anonymization → hard delete)
- **Rate Limiting**: Advanced multi-strategy rate limiting
- **Encryption**: AES-256-GCM, Fernet, RSA-OAEP, hybrid encryption
- **Audit Logging**: Comprehensive security event tracking
- **Accessibility**: WCAG 2.1 Level AA compliance

## Security Features

### Data Protection
- **Encryption at Rest**: AES-256-GCM encryption for sensitive data
- **Encryption in Transit**: TLS 1.3 for all communications
- **Field-level Encryption**: Selective encryption of sensitive fields
- **Key Management**: Integration with GCP Secret Manager

### Access Control
- **Rate Limiting**: Sliding window, fixed window, and token bucket strategies
- **Subscription-based Limits**: Different limits for free/premium users
- **API Security**: Comprehensive input validation and sanitization

### Audit & Compliance
- **Security Audit Logs**: 180-day retention with integrity verification
- **GDPR Compliance**: Full data subject rights implementation
- **Incident Reporting**: Automated security incident tracking
- **Real-time Monitoring**: Proactive security alerting

### Accessibility
- **WCAG 2.1 AA**: Full compliance with web accessibility standards
- **Keyboard Navigation**: Complete keyboard accessibility
- **Screen Reader Support**: Comprehensive assistive technology support
- **Focus Management**: Proper focus trapping and indicators

## Getting Started

### Prerequisites
- Node.js 18+
- Python 3.11+
- PostgreSQL 14+
- Redis 6+
- Google Cloud SDK (for deployment)

### Development Setup

#### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
alembic upgrade head

# Start the server
uvicorn main:app --reload
```

#### Frontend Setup
```bash
cd frontend
npm install

# Set up environment variables
cp .env.example .env.local
# Edit .env.local with your configuration

# Start the development server
npm run dev
```

### Testing

#### Backend Testing
```bash
cd backend
pytest tests/ -v
```

#### Frontend Testing
```bash
cd frontend
# Unit tests
npm test

# E2E tests
npm run test:e2e
```

### Environment Variables

#### Backend (.env)
```
DATABASE_URL=postgresql://user:pass@localhost/bizdesign
REDIS_URL=redis://localhost:6379
GEMINI_API_KEY=your_gemini_key
JWT_SECRET_KEY=your_jwt_secret
ENCRYPTION_MASTER_KEY=your_encryption_key
SENDGRID_API_KEY=your_sendgrid_key
```

#### Frontend (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

## API Documentation

When running the backend server, visit:
- **OpenAPI Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key API Endpoints

#### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `POST /auth/refresh` - Token refresh

#### AI Copilot
- `POST /ai/interact` - AI interaction for analysis
- `GET /frameworks` - Available business frameworks

#### Security & Privacy
- `POST /gdpr/consent/record` - Record GDPR consent
- `POST /users/data-export` - Export user data
- `POST /users/request-deletion` - Request account deletion
- `GET /audit/logs` - Query security audit logs

## Deployment

### Google Cloud Platform

#### Backend (Cloud Run)
```bash
# Build and deploy
gcloud run deploy biz-design-backend \
  --source . \
  --platform managed \
  --region us-central1
```

#### Frontend (Cloud Run)
```bash
# Build and deploy
gcloud run deploy biz-design-frontend \
  --source . \
  --platform managed \
  --region us-central1
```

### Database Migration
```bash
# Run migrations in production
alembic upgrade head
```

## Monitoring & Observability

- **Logs**: Google Cloud Logging with structured JSON
- **Metrics**: Custom metrics for business and security events
- **Alerts**: Automated alerting for security incidents
- **Health Checks**: Comprehensive health monitoring

## Security Considerations

### Production Checklist
- [ ] Enable HTTPS only
- [ ] Configure proper CORS origins
- [ ] Set up rate limiting
- [ ] Enable audit logging
- [ ] Configure encryption keys
- [ ] Set up monitoring alerts
- [ ] Review access controls
- [ ] Test backup/recovery procedures

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For questions or support, please contact the development team or create an issue in the repository.

---

**Status**: ✅ Modules 1-9 Complete | 🚧 Module 10 (Deployment) In Progress