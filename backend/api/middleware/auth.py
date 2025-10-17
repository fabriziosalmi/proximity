"""
Authentication Middleware for Proximity

Provides dependency injection for authentication and authorization.
"""

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from models.database import get_db, User
from models.schemas import TokenData
from services.auth_service import AuthService
from core.config import settings
from typing import Optional
import logging
import sentry_sdk

logger = logging.getLogger(__name__)

# HTTP Bearer token security scheme
security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> TokenData:
    """
    Dependency to get current authenticated user from JWT token.

    Args:
        request: FastAPI request object (for IP logging)
        credentials: Bearer token credentials
        db: Database session

    Returns:
        TokenData with user information

    Raises:
        HTTPException: If token is missing or invalid
    """
    # Allow OPTIONS requests for CORS preflight
    if request.method == "OPTIONS":
        return None

    if credentials is None:
        logger.warning(f"Authentication required: No token provided from {request.client.host}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # Verify token and extract user data
    token_data = AuthService.verify_token(token)

    # Verify user still exists and is active
    user = db.query(User).filter(User.id == token_data.user_id).first()
    if not user or not user.is_active:
        logger.warning(f"User {token_data.username} not found or inactive")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Store user info in request state for logging
    request.state.user = token_data
    request.state.user_ip = request.client.host

    # Set Sentry user context for error tracking
    # This ensures all backend errors include user information
    sentry_sdk.set_user({
        "id": str(token_data.user_id),
        "username": token_data.username,
        "email": getattr(user, "email", None),  # Include email if available
        "role": token_data.role,
        "ip_address": request.client.host if request.client else None,
    })
    
    # Add additional Sentry tags for better filtering
    sentry_sdk.set_tag("user_role", token_data.role)
    sentry_sdk.set_tag("authenticated", "true")

    return token_data


async def get_current_active_user(
    current_user: TokenData = Depends(get_current_user)
) -> TokenData:
    """
    Dependency to get current active user (alias for get_current_user).

    This is kept for compatibility with common FastAPI patterns.
    """
    return current_user


async def require_admin(
    current_user: TokenData = Depends(get_current_user)
) -> TokenData:
    """
    Dependency to require admin privileges.

    Args:
        current_user: Current authenticated user

    Returns:
        TokenData if user is admin

    Raises:
        HTTPException: If user is not admin
    """
    if current_user.role != "admin":
        logger.warning(f"Admin access denied for user: {current_user.username}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )

    return current_user


async def get_current_user_db(
    token_data: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get current user database object.

    Useful when you need the full User model, not just TokenData.

    Args:
        token_data: Current user token data
        db: Database session

    Returns:
        User database object
    """
    user = db.query(User).filter(User.id == token_data.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    return user


# Optional: Allow certain endpoints to work without auth
async def optional_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[TokenData]:
    """
    Dependency for optional authentication.

    Returns user data if token is present and valid, None otherwise.
    Useful for endpoints that change behavior based on authentication.

    Args:
        credentials: Bearer token credentials (optional)
        db: Database session

    Returns:
        TokenData if authenticated, None otherwise
    """
    if credentials is None:
        return None

    try:
        token = credentials.credentials
        token_data = AuthService.verify_token(token)

        # Verify user exists
        user = db.query(User).filter(User.id == token_data.user_id).first()
        if not user or not user.is_active:
            return None

        return token_data

    except HTTPException:
        return None
