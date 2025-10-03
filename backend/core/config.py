from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os


class Settings(BaseSettings):
    # Proxmox Connection Settings
    PROXMOX_HOST: str
    PROXMOX_USER: str
    PROXMOX_PASSWORD: str
    PROXMOX_VERIFY_SSL: bool = False
    PROXMOX_PORT: int = 8006
    
    # SSH Settings (for executing commands in containers via pct exec)
    PROXMOX_SSH_HOST: Optional[str] = None  # Defaults to PROXMOX_HOST if not set
    PROXMOX_SSH_PORT: int = 22
    PROXMOX_SSH_USER: str = "root"
    PROXMOX_SSH_PASSWORD: Optional[str] = None  # Defaults to PROXMOX_PASSWORD if not set
    
    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8765
    API_VERSION: str = "v1"
    
    # Application Settings
    APP_NAME: str = "Proximity"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    
    # LXC Template Settings
    DEFAULT_LXC_TEMPLATE: str = "local:vztmpl/proximity-docker-template.tar.zst"
    LXC_STORAGE: str = "local-lvm"
    LXC_MEMORY: int = 2048  # MB
    LXC_CORES: int = 2
    LXC_DISK_SIZE: str = "8G"
    
    # Network Settings
    LXC_BRIDGE: str = "vmbr0"
    LXC_NET_CONFIG: str = "name=eth0,bridge=vmbr0,ip=dhcp"
    
    # Application Catalog
    APP_CATALOG_PATH: Optional[str] = None  # Will default to ./catalog in development
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        case_sensitive=True
    )

    def get_proxmox_url(self) -> str:
        """Get the full Proxmox API URL"""
        protocol = "https" if self.PROXMOX_VERIFY_SSL else "https"
        return f"{protocol}://{self.PROXMOX_HOST}:{self.PROXMOX_PORT}"


# Global settings instance
settings = Settings()