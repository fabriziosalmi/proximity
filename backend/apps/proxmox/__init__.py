"""Proxmox app initialization."""
import os

# Lazy import to avoid circular dependencies during Django initialization
ProxmoxService = None
ProxmoxError = None

def __getattr__(name):
    """Lazy loading of ProxmoxService and ProxmoxError."""
    global ProxmoxService, ProxmoxError
    
    if name == 'ProxmoxService':
        if ProxmoxService is None:
            if os.getenv('USE_MOCK_PROXMOX') == '1':
                print("🎭 MOCK: Using MockProxmoxService (USE_MOCK_PROXMOX=1)")
                from .mock_service import MockProxmoxService
                ProxmoxService = MockProxmoxService
            else:
                from .services import ProxmoxService as RealService
                ProxmoxService = RealService
        return ProxmoxService
    elif name == 'ProxmoxError':
        if ProxmoxError is None:
            if os.getenv('USE_MOCK_PROXMOX') == '1':
                from .mock_service import ProxmoxError as MockError
                ProxmoxError = MockError
            else:
                from .services import ProxmoxError as RealError
                ProxmoxError = RealError
        return ProxmoxError
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = ['ProxmoxService', 'ProxmoxError']
