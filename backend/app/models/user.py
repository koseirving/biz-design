from sqlalchemy import Column, String, TIMESTAMP, Boolean, Integer, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    subscription_tier = Column(String(50), default='free', nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)


class BusinessFramework(Base):
    __tablename__ = "business_frameworks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    micro_content = Column(JSON, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)


class UserOutput(Base):
    __tablename__ = "user_outputs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    framework_id = Column(UUID(as_uuid=True), nullable=False)
    output_data = Column(JSON, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class CompanyProfile(Base):
    __tablename__ = "company_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    profile_name = Column(String(255), nullable=False)
    profile_data = Column(JSON, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class UserProgress(Base):
    __tablename__ = "user_progress"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    event_type = Column(String(50), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=True)
    points_awarded = Column(Integer, nullable=True)
    metadata = Column(JSON, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)


class UserLearningSession(Base):
    __tablename__ = "user_learning_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    framework_id = Column(UUID(as_uuid=True), nullable=False)
    started_at = Column(TIMESTAMP(timezone=True), nullable=False)
    completed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    learning_data = Column(JSON, nullable=True)
    status = Column(String(20), nullable=False, default='in_progress')


class NotificationPreferences(Base):
    __tablename__ = "notification_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), unique=True, nullable=False)
    email_enabled = Column(Boolean, default=True, nullable=False)
    push_enabled = Column(Boolean, default=True, nullable=False)
    reminder_settings = Column(JSON, nullable=True)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class NotificationHistory(Base):
    __tablename__ = "notification_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    notification_type = Column(String(50), nullable=False)
    delivery_channel = Column(String(20), nullable=False)
    content = Column(JSON, nullable=False)
    scheduled_at = Column(TIMESTAMP(timezone=True), nullable=False)
    sent_at = Column(TIMESTAMP(timezone=True), nullable=True)
    status = Column(String(20), nullable=False, default='pending')


class OutputVersions(Base):
    __tablename__ = "output_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    output_id = Column(UUID(as_uuid=True), nullable=False)
    version_number = Column(Integer, nullable=False)
    version_data = Column(JSON, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    is_current = Column(Boolean, default=False, nullable=False)


class UserBadge(Base):
    __tablename__ = "user_badges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    badge_type = Column(String(50), nullable=False)
    badge_name = Column(String(100), nullable=False)
    badge_metadata = Column(JSON, nullable=True)
    earned_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)