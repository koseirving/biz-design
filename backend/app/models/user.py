from sqlalchemy import Column, String, TIMESTAMP, Boolean, Integer, Text, JSON
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID
import uuid as uuid_module
from sqlalchemy.sql import func
from app.core.database import Base
import uuid

class GUID(TypeDecorator):
    """Platform-independent GUID type for SQLite and PostgreSQL"""
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(UUID())
        else:
            return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, uuid_module.UUID):
                return "%.32x" % uuid_module.UUID(value).int
            else:
                return "%.32x" % value.int

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid_module.UUID):
                return uuid_module.UUID(value)
            else:
                return value


class User(Base):
    __tablename__ = "users"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    subscription_tier = Column(String(50), default='free', nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)


class BusinessFramework(Base):
    __tablename__ = "business_frameworks"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False, default='strategy')
    difficulty_level = Column(String(20), nullable=False, default='beginner')
    estimated_duration = Column(Integer, nullable=False, default=30)
    is_premium = Column(Boolean, default=False, nullable=False)
    micro_content = Column(JSON, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)


class UserOutput(Base):
    __tablename__ = "user_outputs"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    user_id = Column(GUID(), nullable=False)
    framework_id = Column(GUID(), nullable=False)
    output_data = Column(JSON, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class CompanyProfile(Base):
    __tablename__ = "company_profiles"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    user_id = Column(GUID(), nullable=False)
    profile_name = Column(String(255), nullable=False)
    profile_data = Column(JSON, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class UserProgress(Base):
    __tablename__ = "user_progress"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    user_id = Column(GUID(), nullable=False)
    event_type = Column(String(50), nullable=False)
    entity_id = Column(GUID(), nullable=True)
    points_awarded = Column(Integer, nullable=True)
    event_metadata = Column(JSON, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)


class UserLearningSession(Base):
    __tablename__ = "user_learning_sessions"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    user_id = Column(GUID(), nullable=False)
    framework_id = Column(GUID(), nullable=False)
    started_at = Column(TIMESTAMP(timezone=True), nullable=False)
    completed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    learning_data = Column(JSON, nullable=True)
    status = Column(String(20), nullable=False, default='in_progress')


class NotificationPreferences(Base):
    __tablename__ = "notification_preferences"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    user_id = Column(GUID(), unique=True, nullable=False)
    email_enabled = Column(Boolean, default=True, nullable=False)
    push_enabled = Column(Boolean, default=True, nullable=False)
    reminder_settings = Column(JSON, nullable=True)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class NotificationHistory(Base):
    __tablename__ = "notification_history"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    user_id = Column(GUID(), nullable=False)
    notification_type = Column(String(50), nullable=False)
    delivery_channel = Column(String(20), nullable=False)
    content = Column(JSON, nullable=False)
    scheduled_at = Column(TIMESTAMP(timezone=True), nullable=False)
    sent_at = Column(TIMESTAMP(timezone=True), nullable=True)
    status = Column(String(20), nullable=False, default='pending')


class OutputVersions(Base):
    __tablename__ = "output_versions"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    output_id = Column(GUID(), nullable=False)
    version_number = Column(Integer, nullable=False)
    version_data = Column(JSON, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    is_current = Column(Boolean, default=False, nullable=False)


class UserBadge(Base):
    __tablename__ = "user_badges"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    user_id = Column(GUID(), nullable=False)
    badge_type = Column(String(50), nullable=False)
    badge_name = Column(String(100), nullable=False)
    badge_data = Column(JSON, nullable=True)
    earned_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)