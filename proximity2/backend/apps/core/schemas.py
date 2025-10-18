"""
Core schemas - Pydantic models for API requests/responses
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


# Authentication Schemas

class LoginRequest(BaseModel):
    """Login request payload."""
    username: str = Field(..., min_length=3, max_length=150)
    password: str = Field(..., min_length=6)


class RegisterRequest(BaseModel):
    """User registration request payload."""
    username: str = Field(..., min_length=3, max_length=150)
    email: Optional[EmailStr] = None
    password: str = Field(..., min_length=6)
    first_name: Optional[str] = Field(None, max_length=150)
    last_name: Optional[str] = Field(None, max_length=150)


class UserResponse(BaseModel):
    """User information response."""
    id: int
    username: str
    email: Optional[str]
    preferred_theme: str


class LoginResponse(BaseModel):
    """Login response with JWT tokens."""
    access_token: str
    refresh_token: str
    user: UserResponse


# System Schemas

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    timestamp: str


class SystemInfoResponse(BaseModel):
    """System information response."""
    version: str
    default_theme: str
    enable_ai_agent: bool
    enable_community_chat: bool
    enable_multi_host: bool
