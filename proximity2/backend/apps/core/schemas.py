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


# Settings Schemas

class ResourceSettingsRequest(BaseModel):
    """Request payload for updating default resource settings."""
    default_cpu_cores: int = Field(..., ge=1, le=128, description="CPU cores (1-128)")
    default_memory_mb: int = Field(..., ge=256, le=524288, description="Memory in MB (256MB-512GB)")
    default_disk_gb: int = Field(..., ge=1, le=10240, description="Disk size in GB (1GB-10TB)")
    default_swap_mb: int = Field(..., ge=0, le=32768, description="Swap in MB (0-32GB)")


class ResourceSettingsResponse(BaseModel):
    """Response containing current default resource settings."""
    default_cpu_cores: int
    default_memory_mb: int
    default_disk_gb: int
    default_swap_mb: int
    updated_at: str


class NetworkSettingsRequest(BaseModel):
    """Request payload for updating default network settings."""
    default_subnet: str = Field(..., pattern=r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}/[0-9]{1,2}$',
                                description="Subnet in CIDR notation (e.g., 10.0.0.0/24)")
    default_gateway: str = Field(..., pattern=r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$',
                                 description="Gateway IPv4 address")
    default_dns_primary: str = Field(..., description="Primary DNS server")
    default_dns_secondary: Optional[str] = Field(None, description="Secondary DNS server (optional)")
    default_bridge: str = Field(..., min_length=1, max_length=50, description="Network bridge name (e.g., vmbr0)")


class NetworkSettingsResponse(BaseModel):
    """Response containing current default network settings."""
    default_subnet: str
    default_gateway: str
    default_dns_primary: str
    default_dns_secondary: Optional[str]
    default_bridge: str
    updated_at: str
