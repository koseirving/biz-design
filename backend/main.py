from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Biz Design API", description="AI-powered business framework learning platform", version="1.0.0")

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    """Hello World endpoint for basic health check"""
    return {"message": "Hello World from Biz Design API"}

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "biz-design-backend"}