"""
Proxmox schemas - Pydantic models for API requests/responses
"""

from pydantic import BaseModel, Field
from typing import Optional


class ProxmoxHostCreate(BaseModel):
    """Create Proxmox host request."""

    name: str = Field(..., min_length=1, max_length=100)
    host: str = Field(..., min_length=1, max_length=255)
    port: int = Field(default=8006, ge=1, le=65535)
    user: str = Field(default="root@pam", max_length=100)
    password: str = Field(..., min_length=1)
    verify_ssl: bool = Field(default=False)
    is_default: bool = Field(default=False)


class ProxmoxHostUpdate(BaseModel):
    """Update Proxmox host request."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    host: Optional[str] = Field(None, min_length=1, max_length=255)
    port: Optional[int] = Field(None, ge=1, le=65535)
    user: Optional[str] = Field(None, max_length=100)
    password: Optional[str] = Field(None, min_length=1)
    verify_ssl: Optional[bool] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


class ProxmoxHostResponse(BaseModel):
    """Proxmox host response."""

    id: int
    name: str
    host: str
    port: int
    user: str
    is_active: bool
    is_default: bool
    last_seen: Optional[str]


class ProxmoxNodeResponse(BaseModel):
    """Proxmox node response."""

    id: int
    host_name: str
    name: str
    status: str
    cpu_count: Optional[int]
    cpu_usage: Optional[float]
    memory_total: Optional[int]
    memory_used: Optional[int]
    uptime: Optional[int]


class ConnectionTestResponse(BaseModel):
    """Connection test response."""

    success: bool
    message: str
