"""Proxmox app initialization with mock support."""
import os

# Check environment variable FIRST before any heavy imports
USE_MOCK = os.getenv('USE_MOCK_PROXMOX') == '1'

if USE_MOCK:
    # Import mock FIRST (no Django model dependencies)
    print("🎭 INITIALIZING MOCK: USE_MOCK_PROXMOX=1, loading MockProxmoxService...")
    from .mock_service import MockProxmoxService as ProxmoxService, ProxmoxError
    print("✅ Mock service loaded successfully")
else:
    # Import real service (has Django model dependencies, safe after apps are loaded)
    print("📦 INITIALIZING REAL: Loading real ProxmoxService...")
    from .services import ProxmoxService, ProxmoxError
    print("✅ Real service loaded successfully")

__all__ = ['ProxmoxService', 'ProxmoxError']
