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
    
    # Resource metrics (populated for running containers)
    cpu_usage: Optional[float] = None
    memory_used: Optional[int] = None
    memory_total: Optional[int] = None
    disk_used: Optional[int] = None
    disk_total: Optional[int] = None


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


class ApplicationAdopt(BaseModel):
    """Adopt existing LXC container request."""
    vmid: int = Field(..., description="VMID of the existing container to adopt")
    node_name: str = Field(..., description="Node name where the container is running")
    catalog_id: str = Field(..., description="Catalog app ID that matches this container")
    hostname: Optional[str] = Field(None, min_length=3, max_length=63, description="Custom hostname (defaults to container name)")
    container_port_to_expose: int = Field(..., description="Internal port the container is listening on (e.g., 80 for nginx)")


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
