from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
from enum import Enum
from datetime import datetime


class AppStatus(str, Enum):
    """Application status enumeration"""
    DEPLOYING = "deploying"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    UPDATING = "updating"
    REMOVING = "removing"


class LXCStatus(str, Enum):
    """LXC container status enumeration"""
    RUNNING = "running"
    STOPPED = "stopped"
    STARTING = "starting"
    STOPPING = "stopping"


class NodeInfo(BaseModel):
    """Proxmox node information"""
    node: str
    status: str
    type: str
    uptime: Optional[int] = None
    maxcpu: Optional[int] = None
    maxmem: Optional[int] = None
    cpu: Optional[float] = None
    mem: Optional[int] = None
    disk: Optional[int] = None
    maxdisk: Optional[int] = None


class LXCInfo(BaseModel):
    """LXC container information"""
    vmid: int
    node: str
    status: LXCStatus
    name: Optional[str] = None
    maxmem: Optional[int] = None
    maxcpu: Optional[int] = None
    uptime: Optional[int] = None
    cpu: Optional[float] = None
    mem: Optional[int] = None
    disk: Optional[int] = None
    maxdisk: Optional[int] = None
    netout: Optional[int] = None
    netin: Optional[int] = None


class AppCatalogItem(BaseModel):
    """Application catalog item definition"""
    id: str = Field(..., description="Unique identifier for the app")
    name: str = Field(..., description="Display name of the application")
    description: str = Field(..., description="App description")
    version: str = Field(..., description="App version")
    icon: Optional[str] = Field(None, description="URL to app icon")
    category: str = Field(..., description="App category")
    docker_compose: Dict[str, Any] = Field(..., description="Docker Compose configuration")
    config_schema: Optional[Dict[str, Any]] = Field(None, description="Configuration schema")
    ports: List[int] = Field(default_factory=list, description="Exposed ports")
    volumes: List[str] = Field(default_factory=list, description="Required volumes")
    environment: Dict[str, str] = Field(default_factory=dict, description="Default environment variables")
    min_memory: int = Field(default=1024, description="Minimum memory in MB")
    min_cpu: int = Field(default=1, description="Minimum CPU cores")


class App(BaseModel):
    """Deployed application instance"""
    id: str = Field(..., description="Unique app instance ID")
    catalog_id: str = Field(..., description="Reference to catalog item")
    name: str = Field(..., description="App display name")
    hostname: str = Field(..., description="App hostname")
    status: AppStatus = Field(..., description="Current status")
    url: Optional[str] = Field(None, description="App access URL")
    lxc_id: int = Field(..., description="Associated LXC container ID")
    node: str = Field(..., description="Proxmox node")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    config: Dict[str, Any] = Field(default_factory=dict, description="App configuration")
    ports: Dict[int, int] = Field(default_factory=dict, description="Port mappings (container:host)")
    volumes: List[str] = Field(default_factory=list, description="Mounted volumes")
    environment: Dict[str, str] = Field(default_factory=dict, description="Environment variables")


class AppCreate(BaseModel):
    """Application creation request"""
    catalog_id: str = Field(..., description="Application catalog ID")
    hostname: str = Field(..., description="Hostname for the app", min_length=3, max_length=63)
    config: Dict[str, Any] = Field(default_factory=dict, description="App-specific configuration")
    environment: Dict[str, str] = Field(default_factory=dict, description="Custom environment variables")
    node: Optional[str] = Field(None, description="Target Proxmox node (auto-select if not specified)")
    
    @validator('hostname')
    def validate_hostname(cls, v):
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Hostname must contain only alphanumeric characters, hyphens, and underscores')
        if v.startswith('-') or v.endswith('-'):
            raise ValueError('Hostname cannot start or end with a hyphen')
        return v.lower()


class AppUpdate(BaseModel):
    """Application update request"""
    config: Optional[Dict[str, Any]] = None
    environment: Optional[Dict[str, str]] = None
    status: Optional[AppStatus] = None


class AppAction(BaseModel):
    """Application action request"""
    action: str = Field(..., description="Action to perform: start, stop, restart, rebuild")
    
    @validator('action')
    def validate_action(cls, v):
        allowed_actions = ['start', 'stop', 'restart', 'rebuild']
        if v not in allowed_actions:
            raise ValueError(f'Action must be one of: {", ".join(allowed_actions)}')
        return v


class DeploymentLog(BaseModel):
    """Deployment log entry"""
    timestamp: datetime
    level: str = Field(..., description="Log level: info, warning, error")
    message: str
    step: Optional[str] = None


class DeploymentStatus(BaseModel):
    """Deployment status and logs"""
    app_id: str
    status: AppStatus
    progress: int = Field(default=0, ge=0, le=100)
    current_step: Optional[str] = None
    logs: List[DeploymentLog] = Field(default_factory=list)
    error: Optional[str] = None


class SystemInfo(BaseModel):
    """System information"""
    nodes: List[NodeInfo]
    total_apps: int
    running_apps: int
    total_lxc: int
    version: str
    uptime: Optional[int] = None


class AppList(BaseModel):
    """Paginated app list response"""
    apps: List[App]
    total: int
    page: int
    per_page: int
    pages: int


class CatalogResponse(BaseModel):
    """Application catalog response"""
    items: List[AppCatalogItem]
    categories: List[str]
    total: int


class APIResponse(BaseModel):
    """Generic API response wrapper"""
    success: bool = True
    message: Optional[str] = None
    data: Optional[Any] = None
    error: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = False
    error: str
    details: Optional[Dict[str, Any]] = None