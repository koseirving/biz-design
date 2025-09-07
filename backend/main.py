from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, users, data_privacy, preferences
from app.core.database import engine
from app.models import user

# Create database tables
user.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Biz Design API", description="AI-powered business framework learning platform", version="2.0.0")

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(data_privacy.router)
app.include_router(preferences.router)

@app.get("/")
def read_root():
    """Hello World endpoint for basic health check"""
    return {"message": "Hello World from Biz Design API"}

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "biz-design-backend"}