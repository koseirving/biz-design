import pytest
import asyncio
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from httpx import AsyncClient

from app.core.database import get_db, Base
from app.models.user import User
from app.services.auth_service import create_access_token
from main import app
import redis
import fakeredis

# Test database URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create test database tables
Base.metadata.create_all(bind=engine)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def db_session():
    """Create a fresh database session for each test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def override_get_db(db_session):
    """Override the get_db dependency."""
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides = {}


@pytest.fixture
def fake_redis():
    """Create a fake Redis instance for testing."""
    return fakeredis.FakeRedis(decode_responses=True)


@pytest.fixture
def test_client(override_get_db, fake_redis) -> TestClient:
    """Create a test client for the FastAPI app."""
    # Override Redis dependency if needed
    # Note: You may need to modify this based on how Redis is injected in your app
    return TestClient(app)


@pytest.fixture
async def async_client(override_get_db) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def test_user_data():
    """Test user data fixture."""
    return {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User",
        "subscription_tier": "free"
    }


@pytest.fixture
def test_user(db_session, test_user_data):
    """Create a test user in the database."""
    from app.services.auth_service import get_password_hash
    
    user = User(
        email=test_user_data["email"],
        hashed_password=get_password_hash(test_user_data["password"]),
        full_name=test_user_data["full_name"],
        subscription_tier=test_user_data["subscription_tier"],
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_premium_user(db_session):
    """Create a test premium user in the database."""
    from app.services.auth_service import get_password_hash
    
    user = User(
        email="premium@example.com",
        hashed_password=get_password_hash("premiumpassword123"),
        full_name="Premium User",
        subscription_tier="premium",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    """Create authorization headers for test user."""
    token = create_access_token(data={"sub": test_user.email})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def premium_auth_headers(test_premium_user):
    """Create authorization headers for premium test user."""
    token = create_access_token(data={"sub": test_premium_user.email})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def mock_redis():
    """Mock Redis for tests that need it."""
    import unittest.mock
    with unittest.mock.patch('redis.Redis') as mock:
        fake_redis = fakeredis.FakeRedis(decode_responses=True)
        mock.return_value = fake_redis
        yield fake_redis


@pytest.fixture
def sample_gdpr_consent():
    """Sample GDPR consent data."""
    return {
        "consent_types": ["marketing", "analytics"],
        "legal_basis": "consent",
        "purpose": "Marketing communications and analytics",
        "data_categories": ["email", "usage_data"]
    }


@pytest.fixture
def sample_export_request():
    """Sample data export request."""
    return {
        "formats": ["json", "csv"]
    }


@pytest.fixture
def sample_deletion_request():
    """Sample account deletion request."""
    return {
        "reason": "user_request",
        "confirm_deletion": True,
        "understand_consequences": True
    }