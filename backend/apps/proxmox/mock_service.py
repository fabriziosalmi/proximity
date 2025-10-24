"""
Mock Proxmox Service for Backend Testing

This is a simplified version for use in the Django backend during E2E testing.
It's activated via environment variable: USE_MOCK_PROXMOX=1
"""
import logging
import time
import random
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

# Print immediately when this module is imported
print("🎭 MOCK MODULE IMPORTED: MockProxmoxService is loading...")


class ProxmoxError(Exception):
    """Mock exception matching the real ProxmoxError."""
    pass


class MockProxmoxService:
    """
    Mock implementation of ProxmoxService for E2E testing.
    
    This is a backend-compatible version that simulates Proxmox without Django imports.
    """
    
    # Class-level state
    _containers: Dict[int, Dict[str, Any]] = {}
    _next_vmid = 1000
    _mock_node = "mock-pve-node"
    
    def __init__(self, host_id: Optional[int] = None):
        self.host_id = host_id
        self._client = "MOCK_CLIENT"
        logger.info(f"🎭 MOCK: Initialized MockProxmoxService (host_id={host_id})")
    
    def get_host(self):
        """Mock get_host - returns a mock host object."""
        class MockHost:
            id = 1
            name = "mock-proxmox-host"
            host = "mock-proxmox.local"
            port = 8006
            user = "root@pam"
            is_active = True
            is_default = True
        return MockHost()
    
    def get_client(self):
        return self._client
    
    def test_connection(self) -> bool:
        logger.info("🎭 MOCK: test_connection() - returning True")
        return True
    
    def get_nodes(self) -> List[Dict[str, Any]]:
        return [{
            'node': self._mock_node,
            'status': 'online',
            'maxcpu': 8,
            'cpu': 0.15,
            'maxmem': 32 * 1024**3,
            'mem': 8 * 1024**3,
        }]
    
    def get_next_vmid(self) -> int:
        vmid = self._next_vmid
        self._next_vmid += 1
        logger.info(f"🎭 MOCK: get_next_vmid() - returning {vmid}")
        return vmid
    
    def create_lxc(self, node_name: str, vmid: int, hostname: str, ostemplate: str,
                   password: str, memory: int = 2048, cores: int = 2, disk_size: str = "8",
                   storage: str = "local-lvm", network_bridge: str = "vmbr0", **kwargs) -> Dict[str, Any]:
        print(f"🎭🎭🎭 MOCK CREATE_LXC CALLED: vmid={vmid}, hostname={hostname} 🎭🎭🎭")
        logger.info(f"🎭 MOCK: create_lxc(vmid={vmid}, hostname={hostname}) - STARTING")
        time.sleep(5)  # Simulate deployment delay
        
        self._containers[vmid] = {
            'vmid': vmid,
            'hostname': hostname,
            'status': 'stopped',
            'memory': memory,
            'cores': cores,
            'node': node_name,
            'created_at': time.time(),
        }
        
        logger.info(f"🎭 MOCK: create_lxc(vmid={vmid}) - COMPLETED ✓")
        return {'task': f'UPID:mock::{vmid}:createct:', 'status': 'success'}
    
    def configure_lxc_for_docker(self, node_name: str, vmid: int) -> None:
        logger.info(f"🎭 MOCK: configure_lxc_for_docker(vmid={vmid})")
        time.sleep(1)
    
    def start_lxc(self, node_name: str, vmid: int) -> Dict[str, Any]:
        logger.info(f"🎭 MOCK: start_lxc(vmid={vmid})")
        if vmid not in self._containers:
            raise ProxmoxError(f"Container {vmid} not found")
        time.sleep(2)
        self._containers[vmid]['status'] = 'running'
        logger.info(f"🎭 MOCK: start_lxc(vmid={vmid}) - status=running")
        return {'task': f'UPID:mock::{vmid}:vzstart:', 'status': 'success'}
    
    def stop_lxc(self, node_name: str, vmid: int, force: bool = False) -> Dict[str, Any]:
        logger.info(f"🎭 MOCK: stop_lxc(vmid={vmid})")
        if vmid in self._containers:
            time.sleep(1)
            self._containers[vmid]['status'] = 'stopped'
        return {'task': f'UPID:mock::{vmid}:vzstop:', 'status': 'success'}
    
    def delete_lxc(self, node_name: str, vmid: int, force: bool = False) -> Dict[str, Any]:
        logger.info(f"🎭 MOCK: delete_lxc(vmid={vmid})")
        if vmid in self._containers:
            time.sleep(2)
            del self._containers[vmid]
        return {'task': f'UPID:mock::{vmid}:vzdestroy:', 'status': 'success'}
    
    def clone_lxc(self, node_name: str, source_vmid: int, new_vmid: int,
                  new_hostname: str, full: bool = True, timeout: int = 600) -> str:
        logger.info(f"🎭 MOCK: clone_lxc({source_vmid} → {new_vmid})")
        if source_vmid not in self._containers:
            raise ProxmoxError(f"Source container {source_vmid} not found")
        
        time.sleep(8 if full else 3)
        
        source = self._containers[source_vmid]
        self._containers[new_vmid] = {
            'vmid': new_vmid,
            'hostname': new_hostname,
            'status': 'stopped',
            'memory': source['memory'],
            'cores': source['cores'],
            'node': node_name,
            'cloned_from': source_vmid,
        }
        
        return f"Container {source_vmid} successfully cloned to {new_vmid}"
    
    def get_lxc_status(self, node_name: str, vmid: int) -> Dict[str, Any]:
        if vmid not in self._containers:
            raise ProxmoxError(f"Container {vmid} not found")
        
        container = self._containers[vmid]
        status = {
            'status': container['status'],
            'vmid': vmid,
            'name': container['hostname'],
            'maxmem': container['memory'] * 1024**2,
            'cpu': 0.15 if container['status'] == 'running' else 0,
        }
        
        logger.info(f"🎭 MOCK: get_lxc_status(vmid={vmid}) - {status['status']}")
        return status
    
    def wait_for_task(self, node_name: str, task_upid: str, timeout: int = 300, poll_interval: int = 2) -> bool:
        logger.info(f"🎭 MOCK: wait_for_task(task={task_upid})")
        time.sleep(0.5)
        return True
    
    def execute_command(self, node_name: str, vmid: int, command: str, timeout: int = 30) -> Dict[str, Any]:
        logger.info(f"🎭 MOCK: execute_command(vmid={vmid}, command='{command}')")
        time.sleep(1)
        return {'stdout': f"MOCK: {command}", 'stderr': '', 'exit_code': 0}
