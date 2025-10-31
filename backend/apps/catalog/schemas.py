"""
Pydantic schemas for catalog application definitions.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class DockerComposeServiceSchema(BaseModel):
    """Schema for a single Docker Compose service definition."""

    image: str
    environment: Optional[Dict[str, str]] = Field(default_factory=dict)
    restart: Optional[str] = "unless-stopped"
    network_mode: Optional[str] = None
    ports: Optional[List[str]] = Field(default_factory=list)
    volumes: Optional[List[str]] = Field(default_factory=list)
    command: Optional[str] = None


class DockerComposeSchema(BaseModel):
    """Schema for Docker Compose configuration."""

    version: str
    services: Dict[str, DockerComposeServiceSchema]


class CatalogAppSchema(BaseModel):
    """
    Schema for a catalog application definition.

    This schema maps directly to the JSON structure used in catalog files.
    Example: adminer.json, nginx.json, etc.
    """

    # Core identification
    id: str = Field(..., description="Unique identifier for the application")
    name: str = Field(..., description="Display name of the application")
    version: str = Field(..., description="Application version")
    description: str = Field(..., description="Short description of what the application does")

    # Visual and categorization
    icon: Optional[str] = Field(None, description="URL to application icon")
    category: str = Field(..., description="Category for grouping (e.g., Database, Web Server)")

    # Docker configuration
    docker_compose: Dict[str, Any] = Field(
        ..., description="Docker Compose configuration as a dictionary"
    )

    # Resource requirements
    ports: List[int] = Field(default_factory=list, description="List of ports the application uses")
    volumes: List[Any] = Field(
        default_factory=list, description="List of volume definitions (can be strings or dicts)"
    )
    environment: Dict[str, str] = Field(
        default_factory=dict, description="Default environment variables"
    )

    # System requirements
    min_memory: int = Field(..., description="Minimum memory in MB", ge=0)
    min_cpu: int = Field(..., description="Minimum CPU cores", ge=1)

    # Metadata
    tags: List[str] = Field(default_factory=list, description="Tags for search and filtering")
    author: Optional[str] = Field(None, description="Application author")
    website: Optional[str] = Field(None, description="Official website URL")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "adminer",
                "name": "Adminer",
                "version": "latest",
                "description": "Full-featured database management tool",
                "icon": "https://cdn.simpleicons.org/adminer/34567C",
                "category": "Database",
                "docker_compose": {
                    "version": "3.8",
                    "services": {
                        "adminer": {
                            "image": "adminer:latest",
                            "environment": {"ADMINER_DEFAULT_SERVER": "db"},
                            "restart": "always",
                            "network_mode": "host",
                        }
                    },
                },
                "ports": [8080],
                "volumes": [],
                "environment": {},
                "min_memory": 128,
                "min_cpu": 1,
                "tags": ["database", "management", "mysql", "postgresql"],
                "author": "Adminer",
                "website": "https://www.adminer.org",
            }
        }


class CatalogListResponse(BaseModel):
    """Response schema for listing catalog applications."""

    total: int = Field(..., description="Total number of applications")
    applications: List[CatalogAppSchema] = Field(..., description="List of applications")


class CatalogCategoriesResponse(BaseModel):
    """Response schema for listing categories."""

    categories: List[str] = Field(..., description="List of unique category names")
