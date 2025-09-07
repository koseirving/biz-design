from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, users, data_privacy, preferences, frameworks, outputs, learning
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
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(data_privacy.router, prefix="/users", tags=["Data Privacy"])
app.include_router(preferences.router, prefix="/users", tags=["Preferences"])
app.include_router(frameworks.router, prefix="/frameworks", tags=["Frameworks"])
app.include_router(outputs.router, prefix="/outputs", tags=["Outputs"])
app.include_router(learning.router, prefix="/learning", tags=["Learning"])

@app.get("/")
def read_root():
    """Hello World endpoint for basic health check"""
    return {"message": "Hello World from Biz Design API"}

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "biz-design-backend"}