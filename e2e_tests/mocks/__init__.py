"""
Mocks Package for E2E Testing

This package contains mock implementations of external services
to enable fast, reliable, and environment-independent E2E testing.
"""
from .mock_proxmox_service import MockProxmoxService

__all__ = ['MockProxmoxService']
