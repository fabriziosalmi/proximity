"""
Application schemas - Pydantic models for API requests/responses
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime


class ApplicationCreate(BaseModel):
    """Create application request."""
    catalog_id: str = Field(..., description="Catalog item ID")
    hostname: str = Field(..., min_length=3, max_length=63, description="Unique hostname")
    config: Dict[str, Any] = Field(default_factory=dict, description="Application configuration")
    environment: Dict[str, str] = Field(default_factory=dict, description="Environment variables")
    node: Optional[str] = Field(None, description="Target node (auto-select if not specified)")


class ApplicationResponse(BaseModel):
    """Application detail response."""
    id: str
    catalog_id: str
    name: str
    hostname: str
    status: str
    url: Optional[str]
    iframe_url: Optional[str]
    public_port: Optional[int]
    internal_port: Optional[int]
    lxc_id: Optional[int]
    node: str
    host_id: int
    created_at: str
    updated_at: str
    config: Dict[str, Any]
    environment: Dict[str, str]


class ApplicationListResponse(BaseModel):
    """Paginated application list."""
    apps: List[ApplicationResponse]
    total: int
    page: int
    per_page: int


class ApplicationAction(BaseModel):
    """Application action request."""
    action: str = Field(..., description="Action: start, stop, restart, or delete")


class ApplicationClone(BaseModel):
    """Clone application request."""
    new_hostname: str = Field(..., min_length=3, max_length=63, description="Hostname for the cloned application")


class DeploymentLogResponse(BaseModel):
    """Deployment log entry."""
    id: int
    timestamp: str
    level: str
    message: str
    step: Optional[str]


class ApplicationLogsResponse(BaseModel):
    """Application deployment logs."""
    app_id: str
    logs: List[DeploymentLogResponse]
    total: int
