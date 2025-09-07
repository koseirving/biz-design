from app.core.database import engine, Base
from app.models.user import (
    User, BusinessFramework, UserOutput, CompanyProfile, UserProgress,
    UserLearningSession, NotificationPreferences, NotificationHistory,
    OutputVersions, UserBadge
)

def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    create_tables()