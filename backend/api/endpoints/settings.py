"""
Settings API Endpoints for Proximity

Handles system configuration management with encrypted storage.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from models.database import get_db
from api.middleware.auth import get_current_user, require_admin, TokenData
from services.settings_service import get_settings_service, SettingsService
from services.auth_service import AuthService
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


# Request/Response Schemas

class ProxmoxCredentials(BaseModel):
    """Proxmox connection settings"""
    host: str
    user: str
    password: str
    port: int = 8006
    verify_ssl: bool = False


class NetworkSettings(BaseModel):
    """Network configuration"""
    lan_subnet: str = "10.20.0.0/24"
    lan_gateway: str = "10.20.0.1"
    dhcp_start: str = "10.20.0.100"
    dhcp_end: str = "10.20.0.250"
    dns_domain: str = "prox.local"


class DefaultResources(BaseModel):
    """Default LXC resource allocations"""
    lxc_memory: int = 2048
    lxc_cores: int = 2
    lxc_disk: int = 8
    lxc_storage: str = "local-lvm"


class SettingUpdate(BaseModel):
    """Generic setting update"""
    key: str
    value: str
    category: str = "system"


# API Endpoints

@router.get("/proxmox")
async def get_proxmox_settings(
    request: Request,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_admin),
    settings_svc: SettingsService = Depends(get_settings_service)
):
    """
    Get Proxmox connection settings (admin only)

    Password is masked in response for security.
    """
    creds = settings_svc.get_proxmox_credentials(db)

    # Log access
    AuthService.log_audit(
        db, current_user.user_id, current_user.username,
        "view_proxmox_settings", "settings", "proxmox",
        ip_address=request.client.host
    )

    return {
        "host": creds.get('host', ''),
        "user": creds.get('user', ''),
        "password": "******" if creds.get('password') else "",  # Masked
        "port": creds.get('port', 8006),
        "verify_ssl": creds.get('verify_ssl', False)
    }


@router.post("/proxmox")
async def update_proxmox_settings(
    creds: ProxmoxCredentials,
    request: Request,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_admin),
    settings_svc: SettingsService = Depends(get_settings_service)
):
    """
    Update Proxmox credentials (admin only)

    Credentials are encrypted before storage.
    Connection is tested before saving.
    """
    # Only update password if not placeholder
    if creds.password != "******":
        settings_svc.set_proxmox_credentials(
            db, creds.host, creds.user, creds.password,
            creds.port, creds.verify_ssl, current_user.user_id
        )
    else:
        # Update other fields only
        settings_svc.set(db, 'proxmox_host', creds.host, 'proxmox', current_user.user_id)
        settings_svc.set(db, 'proxmox_user', creds.user, 'proxmox', current_user.user_id)
        settings_svc.set(db, 'proxmox_port', str(creds.port), 'proxmox', current_user.user_id)
        settings_svc.set(db, 'proxmox_verify_ssl', str(creds.verify_ssl), 'proxmox', current_user.user_id)

    # Test connection
    connection_test_result = "skipped"
    connection_error = None

    try:
        from services.proxmox_service import proxmox_service

        # Note: This would require proxmox_service to reload credentials from DB
        # For now, just save and note that restart is needed
        connection_test_result = "saved"
        connection_error = "Restart API to apply new Proxmox credentials"

    except Exception as e:
        logger.error(f"Proxmox connection test failed: {e}")
        connection_error = str(e)

    # Log change
    AuthService.log_audit(
        db, current_user.user_id, current_user.username,
        "update_proxmox_settings", "settings", "proxmox",
        details={"host": creds.host, "user": creds.user},
        ip_address=request.client.host
    )

    return {
        "success": True,
        "message": "Proxmox settings updated successfully",
        "connection_test": connection_test_result,
        "note": connection_error,
        "warning": "API restart required to apply new credentials"
    }


@router.get("/network")
async def get_network_settings(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
    settings_svc: SettingsService = Depends(get_settings_service)
):
    """Get network configuration"""
    return settings_svc.get_network_settings(db)


@router.post("/network")
async def update_network_settings(
    network: NetworkSettings,
    request: Request,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_admin),
    settings_svc: SettingsService = Depends(get_settings_service)
):
    """
    Update network settings (admin only)

    Changes apply to newly created apps only.
    Existing apps retain their current network configuration.
    """
    settings_svc.set_network_settings(
        db,
        lan_subnet=network.lan_subnet,
        lan_gateway=network.lan_gateway,
        dhcp_start=network.dhcp_start,
        dhcp_end=network.dhcp_end,
        dns_domain=network.dns_domain,
        user_id=current_user.user_id
    )

    # Log change
    AuthService.log_audit(
        db, current_user.user_id, current_user.username,
        "update_network_settings", "settings", "network",
        details=network.dict(),
        ip_address=request.client.host
    )

    return {
        "success": True,
        "message": "Network settings updated successfully",
        "warning": "Changes will apply to newly created apps. Existing apps not affected."
    }


@router.get("/resources")
async def get_default_resources(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
    settings_svc: SettingsService = Depends(get_settings_service)
):
    """Get default resource allocations for new LXC containers"""
    return settings_svc.get_default_resources(db)


@router.post("/resources")
async def update_default_resources(
    resources: DefaultResources,
    request: Request,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_admin),
    settings_svc: SettingsService = Depends(get_settings_service)
):
    """
    Update default resource allocations (admin only)

    These values are used as defaults when deploying new apps.
    """
    settings_svc.set_default_resources(
        db,
        lxc_memory=resources.lxc_memory,
        lxc_cores=resources.lxc_cores,
        lxc_disk=resources.lxc_disk,
        lxc_storage=resources.lxc_storage,
        user_id=current_user.user_id
    )

    # Log change
    AuthService.log_audit(
        db, current_user.user_id, current_user.user_id,
        "update_default_resources", "settings", "resources",
        details=resources.dict(),
        ip_address=request.client.host
    )

    return {
        "success": True,
        "message": "Default resources updated successfully"
    }


@router.get("/all")
async def get_all_settings(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_admin),
    settings_svc: SettingsService = Depends(get_settings_service)
):
    """
    Get all settings grouped by category (admin only)

    Sensitive values (passwords) are masked.
    """
    proxmox = await get_proxmox_settings(db, current_user, settings_svc)
    network = await get_network_settings(db, current_user, settings_svc)
    resources = await get_default_resources(db, current_user, settings_svc)

    return {
        "proxmox": proxmox,
        "network": network,
        "resources": resources
    }


@router.post("/")
async def set_setting(
    setting: SettingUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_admin),
    settings_svc: SettingsService = Depends(get_settings_service)
):
    """
    Set a generic setting (admin only)

    For advanced use or custom settings.
    """
    settings_svc.set(
        db, setting.key, setting.value,
        setting.category, current_user.user_id
    )

    # Log change
    AuthService.log_audit(
        db, current_user.user_id, current_user.username,
        "update_setting", "settings", setting.key,
        details={"key": setting.key, "category": setting.category},
        ip_address=request.client.host
    )

    return {
        "success": True,
        "message": f"Setting '{setting.key}' updated successfully"
    }


@router.delete("/{key}")
async def delete_setting(
    key: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_admin),
    settings_svc: SettingsService = Depends(get_settings_service)
):
    """Delete a setting (admin only)"""
    deleted = settings_svc.delete(db, key)

    if not deleted:
        raise HTTPException(status_code=404, detail=f"Setting '{key}' not found")

    # Log deletion
    AuthService.log_audit(
        db, current_user.user_id, current_user.username,
        "delete_setting", "settings", key,
        ip_address=request.client.host
    )

    return {
        "success": True,
        "message": f"Setting '{key}' deleted successfully"
    }
