"""
Core API endpoints - Health checks, system info, and settings
"""

from typing import Dict
from ninja import Router
from datetime import datetime

from .schemas import (
    HealthResponse,
    SystemInfoResponse,
    ResourceSettingsRequest,
    ResourceSettingsResponse,
    NetworkSettingsRequest,
    NetworkSettingsResponse,
)
from .models import SystemSettings

router = Router()


@router.get("/health", response=HealthResponse)
def health_check(request):
    """
    Health check endpoint for monitoring.
    """
    return {
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/system/info", response=SystemInfoResponse)
def system_info(request):
    """
    Get system information and configuration.
    """
    settings_obj = SystemSettings.load()

    return {
        "version": "2.0.0",
        "default_theme": settings_obj.default_theme,
        "enable_ai_agent": settings_obj.enable_ai_agent,
        "enable_community_chat": settings_obj.enable_community_chat,
        "enable_multi_host": settings_obj.enable_multi_host,
    }


@router.get("/sentry-debug/")
def sentry_debug(request):
    """
    Intentionally raise an exception to test Sentry integration.
    This endpoint should only be used for verification purposes.
    """
    raise ZeroDivisionError("Sentry test error from backend.")


# Settings Management Endpoints


@router.get("/settings/resources", response=ResourceSettingsResponse)
def get_resource_settings(request):
    """
    Get current default resource settings for new deployments.
    """
    settings_obj = SystemSettings.load()

    return {
        "default_cpu_cores": settings_obj.default_cpu_cores,
        "default_memory_mb": settings_obj.default_memory_mb,
        "default_disk_gb": settings_obj.default_disk_gb,
        "default_swap_mb": settings_obj.default_swap_mb,
        "updated_at": settings_obj.updated_at.isoformat(),
    }


@router.post("/settings/resources", response={200: ResourceSettingsResponse, 403: Dict})
def update_resource_settings(request, payload: ResourceSettingsRequest):
    """
    Update default resource settings.
    Requires admin privileges.
    """
    # The global JWTCookieAuthenticator populates request.auth if the user is authenticated.
    if not request.auth or not request.auth.is_staff:
        return 403, {"error": "Admin privileges required"}

    settings_obj = SystemSettings.load()

    # Update resource settings
    settings_obj.default_cpu_cores = payload.default_cpu_cores
    settings_obj.default_memory_mb = payload.default_memory_mb
    settings_obj.default_disk_gb = payload.default_disk_gb
    settings_obj.default_swap_mb = payload.default_swap_mb
    settings_obj.updated_by = request.auth
    settings_obj.save()

    return {
        "default_cpu_cores": settings_obj.default_cpu_cores,
        "default_memory_mb": settings_obj.default_memory_mb,
        "default_disk_gb": settings_obj.default_disk_gb,
        "default_swap_mb": settings_obj.default_swap_mb,
        "updated_at": settings_obj.updated_at.isoformat(),
    }


@router.get("/settings/network", response=NetworkSettingsResponse)
def get_network_settings(request):
    """
    Get current default network settings for new deployments.
    """
    settings_obj = SystemSettings.load()

    return {
        "default_subnet": settings_obj.default_subnet,
        "default_gateway": settings_obj.default_gateway,
        "default_dns_primary": settings_obj.default_dns_primary,
        "default_dns_secondary": settings_obj.default_dns_secondary,
        "default_bridge": settings_obj.default_bridge,
        "updated_at": settings_obj.updated_at.isoformat(),
    }


@router.post("/settings/network", response={200: NetworkSettingsResponse, 400: Dict, 403: Dict})
def update_network_settings(request, payload: NetworkSettingsRequest):
    """
    Update default network settings.
    Requires admin privileges.
    """
    # The global JWTCookieAuthenticator populates request.auth if the user is authenticated.
    if not request.auth or not request.auth.is_staff:
        return 403, {"error": "Admin privileges required"}

    # Additional CIDR validation
    import ipaddress

    try:
        # Validate subnet CIDR
        ipaddress.IPv4Network(payload.default_subnet, strict=False)

        # Validate gateway IP
        ipaddress.IPv4Address(payload.default_gateway)

        # Validate DNS servers
        ipaddress.ip_address(payload.default_dns_primary)
        if payload.default_dns_secondary:
            ipaddress.ip_address(payload.default_dns_secondary)

    except ValueError as e:
        return 400, {"error": f"Invalid IP address or CIDR notation: {str(e)}"}

    settings_obj = SystemSettings.load()

    # Update network settings
    settings_obj.default_subnet = payload.default_subnet
    settings_obj.default_gateway = payload.default_gateway
    settings_obj.default_dns_primary = payload.default_dns_primary
    settings_obj.default_dns_secondary = payload.default_dns_secondary
    settings_obj.default_bridge = payload.default_bridge
    settings_obj.updated_by = request.auth
    settings_obj.save()

    return {
        "default_subnet": settings_obj.default_subnet,
        "default_gateway": settings_obj.default_gateway,
        "default_dns_primary": settings_obj.default_dns_primary,
        "default_dns_secondary": settings_obj.default_dns_secondary,
        "default_bridge": settings_obj.default_bridge,
        "updated_at": settings_obj.updated_at.isoformat(),
    }
