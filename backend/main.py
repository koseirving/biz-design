from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, users, data_privacy, preferences, frameworks, outputs, learning, company_profiles, progress, notifications, reviews, email_templates, websocket, gdpr_compliance, audit_logs, rate_limits
from app.routers import ai
from app.core.database import engine
from app.core.middleware import APILimiter
from app.models import user
import redis
import os

# Create database tables
user.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Biz Design API", description="AI-powered business framework learning platform", version="2.0.0")

# Initialize Redis for rate limiting
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=0,
    decode_responses=True
)

# Initialize API Limiter
api_limiter = APILimiter(redis=redis_client)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(data_privacy.router, prefix="/users", tags=["Data Privacy"])
app.include_router(preferences.router, prefix="/users", tags=["Preferences"])
app.include_router(frameworks.router, prefix="/frameworks", tags=["Frameworks"])
app.include_router(outputs.router, prefix="/outputs", tags=["Outputs"])
app.include_router(learning.router, prefix="/learning", tags=["Learning"])
app.include_router(ai.router, prefix="/ai", tags=["AI Copilot"])
app.include_router(company_profiles.router, prefix="/company-profiles", tags=["Company Profiles"])
app.include_router(progress.router, prefix="/users", tags=["User Progress"])
app.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
app.include_router(reviews.router, prefix="/reviews", tags=["Reviews & Learning"])
app.include_router(email_templates.router, prefix="/email", tags=["Email Templates"])
app.include_router(websocket.router, prefix="/realtime", tags=["Real-time Notifications"])
app.include_router(gdpr_compliance.router, prefix="/gdpr", tags=["GDPR Compliance"])
app.include_router(audit_logs.router, prefix="/audit", tags=["Security Audit Logs"])
app.include_router(rate_limits.router, prefix="/admin/rate-limits", tags=["Rate Limiting Management"])

@app.get("/")
def read_root():
    """Hello World endpoint for basic health check"""
    return {"message": "Hello World from Biz Design API"}

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "biz-design-backend"}