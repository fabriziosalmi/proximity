"""
Proxmox service - Connection and node management
Adapted from v1.0 ProxmoxService with async support via Celery
"""
import logging
from typing import List, Dict, Any, Optional
from proxmoxer import ProxmoxAPI
from proxmoxer.core import ResourceException
from django.utils import timezone
from django.core.cache import cache

from .models import ProxmoxHost, ProxmoxNode

logger = logging.getLogger(__name__)


class ProxmoxError(Exception):
    """Custom exception for Proxmox API errors."""
    pass


class ProxmoxService:
    """
    Service layer for Proxmox API interactions.
    Supports multiple hosts and connection caching.
    """
    
    def __init__(self, host_id: Optional[int] = None):
        """
        Initialize Proxmox service.
        
        Args:
            host_id: Optional Proxmox host ID. If None, uses default host.
        """
        self.host_id = host_id
        self._client = None
    
    def get_host(self) -> ProxmoxHost:
        """Get the ProxmoxHost instance."""
        if self.host_id:
            return ProxmoxHost.objects.get(pk=self.host_id, is_active=True)
        else:
            # Get default host
            host = ProxmoxHost.objects.filter(is_default=True, is_active=True).first()
            if not host:
                # Fallback to any active host
                host = ProxmoxHost.objects.filter(is_active=True).first()
            if not host:
                raise ProxmoxError("No active Proxmox host configured")
            return host
    
    def get_client(self) -> ProxmoxAPI:
        """
        Get or create Proxmox API client.
        Uses caching for connection pooling.
        """
        if self._client is not None:
            return self._client
        
        host = self.get_host()
        cache_key = f"proxmox_client_{host.id}"
        
        # Try to get from cache
        client = cache.get(cache_key)
        if client:
            self._client = client
            return client
        
        # Create new connection
        try:
            client = ProxmoxAPI(
                host.host,
                backend='https',
                user=host.user,
                password=host.password,  # TODO: Decrypt password
                verify_ssl=host.verify_ssl,
                port=host.port
            )
            
            # Test connection
            client.version.get()
            
            # Update last_seen
            host.last_seen = timezone.now()
            host.save(update_fields=['last_seen'])
            
            # Cache for 5 minutes
            cache.set(cache_key, client, 300)
            self._client = client
            
            logger.info(f"Connected to Proxmox host: {host.name}")
            return client
            
        except Exception as e:
            error_msg = str(e).lower()
            if "authentication" in error_msg or "auth" in error_msg:
                raise ProxmoxError(f"Authentication failed for {host.name}: {e}")
            elif "connection" in error_msg or "refused" in error_msg:
                raise ProxmoxError(
                    f"Cannot connect to {host.name} at {host.host}:{host.port}. "
                    f"Please check that Proxmox is running and accessible."
                )
            elif "ssl" in error_msg or "certificate" in error_msg:
                raise ProxmoxError(
                    f"SSL certificate error for {host.name}. "
                    f"Consider disabling SSL verification for self-signed certificates."
                )
            else:
                raise ProxmoxError(f"Failed to connect to {host.name}: {e}")
    
    def test_connection(self) -> bool:
        """Test connection to Proxmox API."""
        try:
            client = self.get_client()
            client.version.get()
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def get_nodes(self) -> List[Dict[str, Any]]:
        """
        Get list of all Proxmox nodes for this host.
        
        Returns:
            List of node information dictionaries
        """
        try:
            client = self.get_client()
            nodes_data = client.nodes.get()
            return nodes_data
        except Exception as e:
            raise ProxmoxError(f"Failed to get nodes: {e}")
    
    def sync_nodes(self) -> int:
        """
        Sync nodes from Proxmox API to database.
        
        Returns:
            Number of nodes synced
        """
        host = self.get_host()
        nodes_data = self.get_nodes()
        synced_count = 0
        
        for node_data in nodes_data:
            node, created = ProxmoxNode.objects.update_or_create(
                host=host,
                name=node_data.get('node'),
                defaults={
                    'status': node_data.get('status', 'unknown'),
                    'node_type': node_data.get('type', 'node'),
                    'cpu_count': node_data.get('maxcpu'),
                    'cpu_usage': node_data.get('cpu'),
                    'memory_total': node_data.get('maxmem'),
                    'memory_used': node_data.get('mem'),
                    'storage_total': node_data.get('maxdisk'),
                    'storage_used': node_data.get('disk'),
                    'uptime': node_data.get('uptime'),
                    'ip_address': node_data.get('ip'),
                    'pve_version': node_data.get('pveversion'),
                }
            )
            synced_count += 1
        
        logger.info(f"Synced {synced_count} nodes for host {host.name}")
        return synced_count
    
    def get_lxc_containers(self, node_name: str) -> List[Dict[str, Any]]:
        """
        Get all LXC containers on a specific node.
        
        Args:
            node_name: Name of the Proxmox node
            
        Returns:
            List of LXC container information
        """
        try:
            client = self.get_client()
            containers = client.nodes(node_name).lxc.get()
            return containers
        except Exception as e:
            raise ProxmoxError(f"Failed to get LXC containers for node {node_name}: {e}")
    
    def get_next_vmid(self) -> int:
        """
        Get the next available VMID from Proxmox.
        
        Returns:
            Next available VMID
        """
        try:
            client = self.get_client()
            return client.cluster.nextid.get()
        except Exception as e:
            raise ProxmoxError(f"Failed to get next VMID: {e}")
