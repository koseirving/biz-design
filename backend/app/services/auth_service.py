from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token
from app.schemas.auth import UserRegister, UserLogin
from datetime import datetime

class AuthService:
    
    @staticmethod
    def register_user(db: Session, user_data: UserRegister) -> User:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        hashed_password = get_password_hash(user_data.password)
        db_user = User(
            email=user_data.email,
            password_hash=hashed_password,
            subscription_tier="free"
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        return db_user
    
    @staticmethod
    def authenticate_user(db: Session, user_data: UserLogin) -> User:
        user = db.query(User).filter(
            User.email == user_data.email,
            User.is_active == True,
            User.is_deleted == False
        ).first()
        
        if not user or not verify_password(user_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        return user
    
    @staticmethod
    def create_user_tokens(user: User) -> dict:
        access_token = create_access_token(subject=user.email)
        refresh_token = create_refresh_token(subject=user.email)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> User:
        return db.query(User).filter(
            User.email == email,
            User.is_active == True,
            User.is_deleted == False
        ).first()