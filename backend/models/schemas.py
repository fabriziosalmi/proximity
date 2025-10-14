from pydantic import BaseModel, Field, field_validator, EmailStr, ConfigDict
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


class SafeCommand(str, Enum):
    """Safe command enumeration for secure container command execution"""
    LOGS = "logs"
    STATUS = "status"
    DISK = "disk"
    PROCESSES = "processes"
    MEMORY = "memory"
    NETWORK = "network"
    IMAGES = "images"
    VOLUMES = "volumes"
    CONFIG = "config"
    SYSTEM = "system"


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
    ip: Optional[str] = None  # Node IP address
    pveversion: Optional[str] = None  # Proxmox VE version
    lxc_count: Optional[int] = None  # Number of LXC containers on this node
    netout: Optional[int] = None  # Network bytes transmitted
    netin: Optional[int] = None  # Network bytes received


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
    hostname: str = Field(..., description="Hostname for the app")
    status: AppStatus = Field(..., description="Current status")
    url: Optional[str] = Field(None, description="App access URL")
    iframe_url: Optional[str] = Field(None, description="In-app canvas iframe URL")
    public_port: Optional[int] = Field(None, description="Unique port for public access")
    internal_port: Optional[int] = Field(None, description="Unique port for iframe access")
    lxc_id: int = Field(..., description="Associated LXC container ID")
    node: str = Field(..., description="Proxmox node")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    config: Dict[str, Any] = Field(default_factory=dict, description="App configuration")
    ports: Union[Dict[int, int], Dict[str, int]] = Field(default_factory=dict, description="Port mappings (container:host)")
    volumes: Union[List[str], List[Dict[str, str]]] = Field(default_factory=list, description="Mounted volumes")
    environment: Dict[str, str] = Field(default_factory=dict, description="Environment variables")



class AppCreate(BaseModel):
    """Application creation request"""
    catalog_id: str = Field(..., description="Application catalog ID")
    hostname: str = Field(..., description="Hostname for the app", min_length=3, max_length=63)
    config: Dict[str, Any] = Field(default_factory=dict, description="App-specific configuration")
    environment: Dict[str, str] = Field(default_factory=dict, description="Custom environment variables")
    node: Optional[str] = Field(None, description="Target Proxmox node (auto-select if not specified)")
    
    @field_validator('hostname')
    @classmethod
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
    
    @field_validator('action')
    @classmethod
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


# Authentication Schemas

class UserCreate(BaseModel):
    """User creation/registration request"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr | None = None
    password: str = Field(..., min_length=8)
    role: str = Field(default="user")

    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Username must contain only alphanumeric characters, hyphens, and underscores')
        return v.lower()

    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        if v not in ['user', 'admin']:
            raise ValueError('Role must be either "user" or "admin"')
        return v


class UserLogin(BaseModel):
    """User login request"""
    username: str
    password: str


class UserResponse(BaseModel):
    """User response model (excludes password)"""
    id: int
    username: str
    email: EmailStr | None = None
    role: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600
    user: Optional[UserResponse] = None


class TokenData(BaseModel):
    """Token payload data"""
    username: str
    role: str
    user_id: int


class PasswordChange(BaseModel):
    """Password change request"""
    old_password: str
    new_password: str = Field(..., min_length=8)


class BackupStatus(str, Enum):
    """Backup status enumeration"""
    CREATING = "creating"
    AVAILABLE = "available"
    FAILED = "failed"
    RESTORING = "restoring"
    DELETING = "deleting"


class Backup(BaseModel):
    """Backup instance"""
    id: int = Field(..., description="Backup ID")
    app_id: str = Field(..., description="Associated app ID")
    filename: str = Field(..., description="Backup filename")
    storage_name: str = Field(..., description="Proxmox storage name")
    size_bytes: Optional[int] = Field(None, description="Backup size in bytes")
    backup_type: str = Field(default="vzdump", description="Backup type")
    status: BackupStatus = Field(..., description="Current backup status")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    created_at: datetime = Field(..., description="Backup creation time")
    completed_at: Optional[datetime] = Field(None, description="Backup completion time")

    model_config = ConfigDict(from_attributes=True)


class BackupCreate(BaseModel):
    """Backup creation request"""
    backup_type: str = Field(default="vzdump", description="Type of backup to create")
    storage: Optional[str] = Field(None, description="Storage name (defaults to local)")
    compress: Optional[str] = Field("zstd", description="Compression type: zstd, gzip, or none")
    mode: Optional[str] = Field("snapshot", description="Backup mode: snapshot or stop")
    
    @field_validator('compress')
    @classmethod
    def validate_compress(cls, v):
        """Validate compression type"""
        if v is not None and v not in ['zstd', 'gzip', 'none']:
            raise ValueError(f"compress must be one of: zstd, gzip, none (got: {v})")
        return v
    
    @field_validator('mode')
    @classmethod
    def validate_mode(cls, v):
        """Validate backup mode"""
        if v is not None and v not in ['snapshot', 'stop']:
            raise ValueError(f"mode must be one of: snapshot, stop (got: {v})")
        return v


class BackupList(BaseModel):
    """List of backups"""
    backups: List[Backup]
    total: int