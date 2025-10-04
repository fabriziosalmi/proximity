"""
Authentication Endpoints for Proximity

Handles user registration, login, logout, and password management.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import timedelta
from models.database import get_db, User
from models.schemas import (
    UserCreate, UserLogin, UserResponse, Token,
    PasswordChange, APIResponse
)
from services.auth_service import AuthService
from api.middleware.auth import get_current_user, get_current_user_db, TokenData
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Register a new user.

    **Note**: In production, this endpoint should be admin-only or disabled.
    For initial setup, it's open to create the first admin user.
    """
    # Create user
    user = AuthService.create_user(
        db=db,
        username=user_data.username,
        email=user_data.email,
        password=user_data.password,
        role=user_data.role
    )

    # Generate token
    access_token = AuthService.create_access_token(
        data={
            "sub": user.username,
            "role": user.role,
            "user_id": user.id
        }
    )

    # Log audit
    AuthService.log_audit(
        db=db,
        user_id=user.id,
        username=user.username,
        action="user_registered",
        resource_type="user",
        resource_id=str(user.id),
        ip_address=request.client.host
    )

    # Return token with user info
    user_response = UserResponse.model_validate(user)

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=3600,
        user=user_response
    )


@router.post("/login", response_model=Token)
async def login(
    login_data: UserLogin,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Login with username and password.

    Returns JWT access token.
    """
    # Authenticate user
    user = AuthService.authenticate_user(
        db=db,
        username=login_data.username,
        password=login_data.password
    )

    # Generate token
    access_token = AuthService.create_access_token(
        data={
            "sub": user.username,
            "role": user.role,
            "user_id": user.id
        }
    )

    # Log audit
    AuthService.log_audit(
        db=db,
        user_id=user.id,
        username=user.username,
        action="user_login",
        resource_type="auth",
        ip_address=request.client.host
    )

    # Return token with user info
    user_response = UserResponse.model_validate(user)

    logger.info(f"User '{user.username}' logged in from {request.client.host}")

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=3600,
        user=user_response
    )


@router.post("/logout")
async def logout(
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Logout current user.

    **Note**: With JWT, logout is handled client-side by discarding the token.
    This endpoint exists for audit logging purposes.

    For token blacklisting, you would need Redis or a database table.
    """
    # Log audit
    AuthService.log_audit(
        db=db,
        user_id=current_user.user_id,
        username=current_user.username,
        action="user_logout",
        resource_type="auth",
        ip_address=request.client.host
    )

    logger.info(f"User '{current_user.username}' logged out")

    return APIResponse(
        success=True,
        message="Logged out successfully. Please discard your token."
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user_db)
):
    """
    Get current authenticated user information.
    """
    return UserResponse.model_validate(current_user)


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    request: Request,
    current_user: User = Depends(get_current_user_db),
    db: Session = Depends(get_db)
):
    """
    Change password for current user.
    """
    # Change password
    AuthService.change_password(
        db=db,
        user=current_user,
        old_password=password_data.old_password,
        new_password=password_data.new_password
    )

    # Log audit
    AuthService.log_audit(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        action="password_changed",
        resource_type="user",
        resource_id=str(current_user.id),
        ip_address=request.client.host
    )

    return APIResponse(
        success=True,
        message="Password changed successfully"
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Refresh access token.

    Issues a new token with extended expiration.
    """
    # Get fresh user data
    user = db.query(User).filter(User.id == current_user.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    # Generate new token
    access_token = AuthService.create_access_token(
        data={
            "sub": user.username,
            "role": user.role,
            "user_id": user.id
        }
    )

    user_response = UserResponse.model_validate(user)

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=3600,
        user=user_response
    )
