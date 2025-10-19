"""
Core API endpoints - Authentication, health checks, system info
"""
from typing import Dict
from ninja import Router
from django.contrib.auth import authenticate
from django.conf import settings
import jwt
from datetime import datetime, timedelta

from .schemas import (
    LoginRequest, LoginResponse, RegisterRequest, 
    UserResponse, HealthResponse, SystemInfoResponse
)
from .models import User, SystemSettings

router = Router()


@router.post("/auth/login", response=LoginResponse)
def login(request, payload: LoginRequest):
    """
    Authenticate user and return JWT tokens.
    """
    user = authenticate(username=payload.username, password=payload.password)
    
    if user is None:
        return 401, {"error": "Invalid credentials"}
    
    # Generate JWT tokens
    access_token = generate_jwt_token(user, 'access')
    refresh_token = generate_jwt_token(user, 'refresh')
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "preferred_theme": user.preferred_theme,
        }
    }


@router.post("/auth/register", response=UserResponse)
def register(request, payload: RegisterRequest):
    """
    Register a new user.
    """
    # Check if username exists
    if User.objects.filter(username=payload.username).exists():
        return 400, {"error": "Username already exists"}
    
    # Check if email exists (if provided)
    if payload.email and User.objects.filter(email=payload.email).exists():
        return 400, {"error": "Email already exists"}
    
    # Create user
    user = User.objects.create_user(
        username=payload.username,
        email=payload.email,
        password=payload.password,
        first_name=payload.first_name or '',
        last_name=payload.last_name or '',
    )
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "preferred_theme": user.preferred_theme,
    }


@router.get("/health", response=HealthResponse)
def health_check(request):
    """
    Health check endpoint for monitoring.
    """
    return {
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/system/info", response=SystemInfoResponse)
def system_info(request):
    """
    Get system information and configuration.
    """
    settings_obj = SystemSettings.load()
    
    return {
        "version": "2.0.0",
        "default_theme": settings_obj.default_theme,
        "enable_ai_agent": settings_obj.enable_ai_agent,
        "enable_community_chat": settings_obj.enable_community_chat,
        "enable_multi_host": settings_obj.enable_multi_host,
    }


@router.get("/sentry-debug/")
def sentry_debug(request):
    """
    Intentionally raise an exception to test Sentry integration.
    This endpoint should only be used for verification purposes.
    """
    raise ZeroDivisionError("Sentry test error from backend.")


# Utility functions

def generate_jwt_token(user: User, token_type: str) -> str:
    """
    Generate JWT token for user.
    
    Args:
        user: User instance
        token_type: 'access' or 'refresh'
    
    Returns:
        JWT token string
    """
    if token_type == 'access':
        lifetime = settings.JWT_ACCESS_TOKEN_LIFETIME
    else:
        lifetime = settings.JWT_REFRESH_TOKEN_LIFETIME
    
    payload = {
        'user_id': user.id,
        'username': user.username,
        'token_type': token_type,
        'exp': datetime.utcnow() + lifetime,
        'iat': datetime.utcnow(),
    }
    
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
