# Biz Design

AI-powered Business Framework Learning Platform

## Overview

Biz Design is an AI-driven educational platform that transforms traditional business framework learning through interactive, AI-guided experiences. Users learn by doing - not just consuming content, but creating real business outputs with AI assistance.

## Architecture

- **Frontend**: Next.js 15 with TypeScript and Tailwind CSS
- **Backend**: FastAPI with Python 3.11
- **Database**: PostgreSQL on Cloud SQL
- **Cache**: Redis on Cloud Memorystore
- **AI**: Google Gemini API for intelligent interactions
- **Infrastructure**: Google Cloud Platform with Cloud Run

## Services

### Frontend (Port 3000)
- Next.js application with modern React features
- Server-side rendering and API routes
- Responsive design with Tailwind CSS

### Backend (Port 8000)
- FastAPI REST API
- JWT authentication with HttpOnly cookies
- PostgreSQL database integration
- AI-powered business framework analysis

## Quick Start

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/koseirving/biz-design.git
cd biz-design
```

2. Start the backend:
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

3. Start the frontend:
```bash
cd frontend
npm install
npm run dev
```

### Production Deployment

The project uses Google Cloud Build for CI/CD:

1. Push to the main branch
2. Cloud Build automatically builds and deploys both services to Cloud Run
3. Services are accessible via their Cloud Run URLs

## Environment Variables

See `spec/initial/design.md` for complete environment variable documentation.

## Project Status

🚧 **Currently in Development** - Module 1 (Basic Setup) Complete

- [x] GCP Project Setup
- [x] Basic Project Structure  
- [x] Hello World Applications
- [x] Docker Containerization
- [x] CI/CD Pipeline Setup

Next: Database setup and user authentication (Module 2)

## Documentation

Detailed specifications are available in the `spec/initial/` directory:
- `overview.md` - Project overview and goals
- `requirement.md` - Functional and non-functional requirements  
- `design.md` - Technical architecture and API specifications
- `task.md` - Development roadmap and tasks

## License

This project is private and proprietary.