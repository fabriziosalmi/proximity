"""
SafeCommandService - Secure command execution for LXC containers.

This service provides a secure, auditable interface for executing 
predefined commands inside LXC containers. It replaces the dangerous
generic command execution endpoint with safe, read-only operations.

All commands are hardcoded and do not accept user input as part of
the command string, eliminating command injection vulnerabilities.

Author: Proximity Security Team
Date: October 2025
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

from services.proxmox_service import ProxmoxService, ProxmoxError

logger = logging.getLogger(__name__)


class SafeCommandError(Exception):
    """Custom exception for SafeCommand errors"""
    pass


class SafeCommandService:
    """
    Secure command execution service for LXC containers.
    
    This service exposes a limited set of safe, read-only commands
    that can be executed inside containers. All commands are predefined
    and parameterized to prevent command injection attacks.
    """
    
    def __init__(self, proxmox_service: ProxmoxService):
        self.proxmox_service = proxmox_service
    
    async def get_docker_logs(
        self, 
        node: str, 
        vmid: int, 
        tail: int = 100,
        service: Optional[str] = None
    ) -> str:
        """
        Get Docker Compose logs from a container.
        
        Args:
            node: Proxmox node name
            vmid: Container VMID
            tail: Number of log lines to retrieve (default: 100, max: 1000)
            service: Optional specific service name to get logs from
            
        Returns:
            Docker logs as string
            
        Raises:
            SafeCommandError: If command execution fails
        """
        # Validate and sanitize tail parameter
        tail = max(1, min(tail, 1000))  # Clamp between 1 and 1000
        
        try:
            if service:
                # Sanitize service name - only allow alphanumeric, dash, underscore
                if not service.replace('-', '').replace('_', '').isalnum():
                    raise SafeCommandError("Invalid service name format")
                command = f"cd /root && docker compose logs --tail={tail} {service}"
            else:
                command = f"cd /root && docker compose logs --tail={tail}"
            
            output = await self.proxmox_service.execute_in_container(
                node, vmid, command, timeout=30
            )
            return output
        except ProxmoxError as e:
            logger.error(f"Failed to get Docker logs for VMID {vmid}: {e}")
            raise SafeCommandError(f"Failed to retrieve Docker logs: {e}")
        except Exception as e:
            logger.error(f"Unexpected error getting Docker logs: {e}")
            raise SafeCommandError(f"Unexpected error: {e}")
    
    async def get_container_status(self, node: str, vmid: int) -> str:
        """
        Get Docker Compose container status.
        
        Args:
            node: Proxmox node name
            vmid: Container VMID
            
        Returns:
            Container status information
            
        Raises:
            SafeCommandError: If command execution fails
        """
        try:
            command = "cd /root && docker compose ps"
            output = await self.proxmox_service.execute_in_container(
                node, vmid, command, timeout=30
            )
            return output
        except ProxmoxError as e:
            logger.error(f"Failed to get container status for VMID {vmid}: {e}")
            raise SafeCommandError(f"Failed to retrieve container status: {e}")
        except Exception as e:
            logger.error(f"Unexpected error getting container status: {e}")
            raise SafeCommandError(f"Unexpected error: {e}")
    
    async def get_disk_usage(self, node: str, vmid: int) -> str:
        """
        Get disk usage information from container.
        
        Args:
            node: Proxmox node name
            vmid: Container VMID
            
        Returns:
            Disk usage information in human-readable format
            
        Raises:
            SafeCommandError: If command execution fails
        """
        try:
            command = "df -h"
            output = await self.proxmox_service.execute_in_container(
                node, vmid, command, timeout=30
            )
            return output
        except ProxmoxError as e:
            logger.error(f"Failed to get disk usage for VMID {vmid}: {e}")
            raise SafeCommandError(f"Failed to retrieve disk usage: {e}")
        except Exception as e:
            logger.error(f"Unexpected error getting disk usage: {e}")
            raise SafeCommandError(f"Unexpected error: {e}")
    
    async def get_running_processes(self, node: str, vmid: int) -> str:
        """
        Get list of running processes in container.
        
        Args:
            node: Proxmox node name
            vmid: Container VMID
            
        Returns:
            Process list output
            
        Raises:
            SafeCommandError: If command execution fails
        """
        try:
            command = "ps aux"
            output = await self.proxmox_service.execute_in_container(
                node, vmid, command, timeout=30
            )
            return output
        except ProxmoxError as e:
            logger.error(f"Failed to get running processes for VMID {vmid}: {e}")
            raise SafeCommandError(f"Failed to retrieve process list: {e}")
        except Exception as e:
            logger.error(f"Unexpected error getting running processes: {e}")
            raise SafeCommandError(f"Unexpected error: {e}")
    
    async def get_memory_usage(self, node: str, vmid: int) -> str:
        """
        Get memory usage information from container.
        
        Args:
            node: Proxmox node name
            vmid: Container VMID
            
        Returns:
            Memory usage information
            
        Raises:
            SafeCommandError: If command execution fails
        """
        try:
            command = "free -h"
            output = await self.proxmox_service.execute_in_container(
                node, vmid, command, timeout=30
            )
            return output
        except ProxmoxError as e:
            logger.error(f"Failed to get memory usage for VMID {vmid}: {e}")
            raise SafeCommandError(f"Failed to retrieve memory usage: {e}")
        except Exception as e:
            logger.error(f"Unexpected error getting memory usage: {e}")
            raise SafeCommandError(f"Unexpected error: {e}")
    
    async def get_network_info(self, node: str, vmid: int) -> str:
        """
        Get network interface information from container.
        
        Args:
            node: Proxmox node name
            vmid: Container VMID
            
        Returns:
            Network interface information
            
        Raises:
            SafeCommandError: If command execution fails
        """
        try:
            command = "ip addr show"
            output = await self.proxmox_service.execute_in_container(
                node, vmid, command, timeout=30
            )
            return output
        except ProxmoxError as e:
            logger.error(f"Failed to get network info for VMID {vmid}: {e}")
            raise SafeCommandError(f"Failed to retrieve network information: {e}")
        except Exception as e:
            logger.error(f"Unexpected error getting network info: {e}")
            raise SafeCommandError(f"Unexpected error: {e}")
    
    async def get_docker_images(self, node: str, vmid: int) -> str:
        """
        Get list of Docker images in container.
        
        Args:
            node: Proxmox node name
            vmid: Container VMID
            
        Returns:
            Docker images list
            
        Raises:
            SafeCommandError: If command execution fails
        """
        try:
            command = "docker images"
            output = await self.proxmox_service.execute_in_container(
                node, vmid, command, timeout=30
            )
            return output
        except ProxmoxError as e:
            logger.error(f"Failed to get Docker images for VMID {vmid}: {e}")
            raise SafeCommandError(f"Failed to retrieve Docker images: {e}")
        except Exception as e:
            logger.error(f"Unexpected error getting Docker images: {e}")
            raise SafeCommandError(f"Unexpected error: {e}")
    
    async def get_docker_volumes(self, node: str, vmid: int) -> str:
        """
        Get list of Docker volumes in container.
        
        Args:
            node: Proxmox node name
            vmid: Container VMID
            
        Returns:
            Docker volumes list
            
        Raises:
            SafeCommandError: If command execution fails
        """
        try:
            command = "docker volume ls"
            output = await self.proxmox_service.execute_in_container(
                node, vmid, command, timeout=30
            )
            return output
        except ProxmoxError as e:
            logger.error(f"Failed to get Docker volumes for VMID {vmid}: {e}")
            raise SafeCommandError(f"Failed to retrieve Docker volumes: {e}")
        except Exception as e:
            logger.error(f"Unexpected error getting Docker volumes: {e}")
            raise SafeCommandError(f"Unexpected error: {e}")
    
    async def get_compose_config(self, node: str, vmid: int) -> str:
        """
        Get Docker Compose configuration.
        
        Args:
            node: Proxmox node name
            vmid: Container VMID
            
        Returns:
            Docker Compose configuration
            
        Raises:
            SafeCommandError: If command execution fails
        """
        try:
            command = "cd /root && docker compose config"
            output = await self.proxmox_service.execute_in_container(
                node, vmid, command, timeout=30
            )
            return output
        except ProxmoxError as e:
            logger.error(f"Failed to get Docker Compose config for VMID {vmid}: {e}")
            raise SafeCommandError(f"Failed to retrieve Compose configuration: {e}")
        except Exception as e:
            logger.error(f"Unexpected error getting Compose config: {e}")
            raise SafeCommandError(f"Unexpected error: {e}")
    
    async def get_system_info(self, node: str, vmid: int) -> str:
        """
        Get basic system information from container.
        
        Args:
            node: Proxmox node name
            vmid: Container VMID
            
        Returns:
            System information (hostname, uptime, OS version)
            
        Raises:
            SafeCommandError: If command execution fails
        """
        try:
            command = "uname -a && uptime && cat /etc/os-release"
            output = await self.proxmox_service.execute_in_container(
                node, vmid, command, timeout=30
            )
            return output
        except ProxmoxError as e:
            logger.error(f"Failed to get system info for VMID {vmid}: {e}")
            raise SafeCommandError(f"Failed to retrieve system information: {e}")
        except Exception as e:
            logger.error(f"Unexpected error getting system info: {e}")
            raise SafeCommandError(f"Unexpected error: {e}")
    
    def get_available_commands(self) -> Dict[str, str]:
        """
        Get list of all available safe commands.
        
        Returns:
            Dictionary mapping command names to descriptions
        """
        return {
            "logs": "Get Docker Compose logs (supports 'tail' and 'service' parameters)",
            "status": "Get Docker Compose container status",
            "disk": "Get disk usage information",
            "processes": "Get list of running processes",
            "memory": "Get memory usage information",
            "network": "Get network interface information",
            "images": "Get list of Docker images",
            "volumes": "Get list of Docker volumes",
            "config": "Get Docker Compose configuration",
            "system": "Get system information (OS, uptime, kernel)"
        }


# Singleton instance
_command_service: Optional[SafeCommandService] = None


def get_command_service() -> SafeCommandService:
    """Dependency injection for SafeCommandService"""
    global _command_service
    if _command_service is None:
        from services.proxmox_service import proxmox_service
        _command_service = SafeCommandService(proxmox_service)
    return _command_service
