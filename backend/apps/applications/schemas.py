"""
Application schemas - Pydantic models for API requests/responses
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, List, Any
import re
from ipaddress import ip_network, AddressValueError


# Hostname pattern: RFC 1123 compliant
# Lowercase letters, numbers, and hyphens only
# Must start and end with alphanumeric character
# No underscores or special characters
HOSTNAME_PATTERN = re.compile(r"^[a-z0-9]([a-z0-9\-]{1,61}[a-z0-9])?$")


def validate_cidr(cidr_str: str) -> str:
    """
    Validate CIDR notation (e.g., 10.0.0.0/24).

    Args:
        cidr_str: CIDR string to validate

    Returns:
        The validated CIDR string

    Raises:
        ValueError: If CIDR is invalid
    """
    try:
        ip_network(cidr_str, strict=False)
        return cidr_str
    except (AddressValueError, ValueError) as e:
        raise ValueError(f"Invalid CIDR format: {cidr_str} - {str(e)}")


class ApplicationCreate(BaseModel):
    """Create application request."""

    catalog_id: str = Field(..., description="Catalog item ID")
    hostname: str = Field(
        ..., min_length=3, max_length=63, description="Unique hostname (RFC 1123 format)"
    )
    config: Dict[str, Any] = Field(default_factory=dict, description="Application configuration")
    environment: Dict[str, str] = Field(default_factory=dict, description="Environment variables")
    node: Optional[str] = Field(None, description="Target node (auto-select if not specified)")
    network_cidr: Optional[str] = Field(
        None, description="Network CIDR for container (e.g., 10.0.0.0/24)"
    )

    @field_validator("hostname")
    @classmethod
    def validate_hostname(cls, v):
        """🔐 Validate hostname format (RFC 1123)."""
        if not HOSTNAME_PATTERN.match(v):
            raise ValueError(
                "Hostname must contain only lowercase letters, numbers, and hyphens, "
                "and must start and end with an alphanumeric character"
            )
        return v

    @field_validator("network_cidr")
    @classmethod
    def validate_network_cidr(cls, v):
        """🔐 Validate CIDR notation for network configuration."""
        if v:
            return validate_cidr(v)
        return v


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

    new_hostname: str = Field(
        ...,
        min_length=3,
        max_length=63,
        description="Hostname for the cloned application (RFC 1123 format)",
    )

    @field_validator("new_hostname")
    @classmethod
    def validate_new_hostname(cls, v):
        """🔐 Validate hostname format (RFC 1123)."""
        if not HOSTNAME_PATTERN.match(v):
            raise ValueError(
                "Hostname must contain only lowercase letters, numbers, and hyphens, "
                "and must start and end with an alphanumeric character"
            )
        return v


class ApplicationAdopt(BaseModel):
    """Adopt existing LXC container request."""

    vmid: int = Field(..., ge=1, description="VMID of the existing container to adopt")
    node_name: str = Field(..., description="Node name where the container is running")
    # Optional: User can suggest what type of app this is (for icon/category), but defaults to "custom"
    suggested_type: Optional[str] = Field(
        "custom",
        description="Optional suggested app type for categorization (nginx, postgres, custom, etc.)",
    )
    # Optional: User can specify a port to expose, otherwise we auto-detect listening ports
    port_to_expose: Optional[int] = Field(
        None, ge=1, le=65535, description="Optional: specific port to expose (1-65535)"
    )

    @field_validator("vmid")
    @classmethod
    def validate_vmid(cls, v):
        """🔐 Validate VMID is a positive integer."""
        if v < 1:
            raise ValueError("VMID must be a positive integer (>= 1)")
        return v

    @field_validator("port_to_expose")
    @classmethod
    def validate_port(cls, v):
        """🔐 Validate port is in valid range."""
        if v is not None and (v < 1 or v > 65535):
            raise ValueError("Port must be between 1 and 65535")
        return v


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
