from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.auth import UserRegister, UserLogin, UserResponse, Token
from app.services.auth_service import AuthService
from app.services.login_service import LoginTrackingService
from app.services.badge_service import BadgeService
from app.core.security import decode_token

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user"""
    user = AuthService.register_user(db, user_data)
    return UserResponse(
        id=str(user.id),
        email=user.email,
        subscription_tier=user.subscription_tier,
        created_at=user.created_at,
        is_active=user.is_active
    )

@router.post("/login", response_model=dict)
async def login(user_data: UserLogin, response: Response, db: Session = Depends(get_db)):
    """Login user and set HttpOnly cookies"""
    user = AuthService.authenticate_user(db, user_data)
    tokens = AuthService.create_user_tokens(user)
    
    # Track login and award points/badges
    login_result = LoginTrackingService.record_login(db, user)
    
    # Check and award any eligible badges
    newly_awarded_badges = BadgeService.check_and_award_badges(db, user)
    all_badges = login_result.get('badges_earned', []) + newly_awarded_badges
    
    # Set HttpOnly cookies
    response.set_cookie(
        key="access_token",
        value=tokens["access_token"],
        max_age=1800,  # 30 minutes
        httponly=True,
        secure=True,
        samesite="lax"
    )
    response.set_cookie(
        key="refresh_token", 
        value=tokens["refresh_token"],
        max_age=604800,  # 7 days
        httponly=True,
        secure=True,
        samesite="lax"
    )
    
    return {
        "message": "Login successful",
        "user": UserResponse(
            id=str(user.id),
            email=user.email,
            subscription_tier=user.subscription_tier,
            created_at=user.created_at,
            is_active=user.is_active
        ),
        "gamification": {
            "points_awarded": login_result.get('points_awarded', 0),
            "streak_days": login_result.get('streak_days', 0),
            "is_first_login": login_result.get('is_first_login', False),
            "badges_earned": [
                {
                    "type": badge.badge_type,
                    "name": badge.badge_name,
                    "data": badge.badge_data
                } for badge in all_badges
            ]
        }
    }

@router.post("/logout")
async def logout(response: Response):
    """Logout user by clearing cookies"""
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message": "Logout successful"}

@router.post("/refresh", response_model=dict)
async def refresh_token(request: Request, response: Response, db: Session = Depends(get_db)):
    """Refresh access token using refresh token"""
    refresh_token = request.cookies.get("refresh_token")
    
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found"
        )
    
    email = decode_token(refresh_token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user = AuthService.get_user_by_email(db, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # Create new tokens
    tokens = AuthService.create_user_tokens(user)
    
    # Set new cookies
    response.set_cookie(
        key="access_token",
        value=tokens["access_token"],
        max_age=1800,
        httponly=True,
        secure=True,
        samesite="lax"
    )
    
    return {"message": "Token refreshed successfully"}