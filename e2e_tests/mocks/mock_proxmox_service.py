"""
Mock Proxmox Service for E2E Testing

This mock service simulates the behavior of a real Proxmox host without
requiring actual infrastructure. It allows E2E tests to run fast, reliably,
and independently in any environment (local, CI/CD, etc.).

The mock maintains internal state to simulate container lifecycle:
- Tracks created containers with their status
- Simulates deployment delays
- Supports all critical operations (create, clone, start, stop, delete)
"""

import logging
import time
import random
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class ProxmoxError(Exception):
    """Mock exception matching the real ProxmoxError."""

    pass


class MockProxmoxService:
    """
    Mock implementation of ProxmoxService for E2E testing.

    This class simulates all Proxmox operations without making real API calls.
    It maintains internal state to provide realistic behavior for tests.
    """

    # Class-level state shared across all instances (simulates Proxmox state)
    _containers: Dict[int, Dict[str, Any]] = {}
    _next_vmid = 1000
    _mock_node = "mock-pve-node"

    def __init__(self, host_id: Optional[int] = None):
        """
        Initialize mock Proxmox service.

        Args:
            host_id: Optional Proxmox host ID (ignored in mock)
        """
        self.host_id = host_id
        self._client = "MOCK_CLIENT"
        logger.info(f"🎭 MOCK: Initialized MockProxmoxService (host_id={host_id})")

    def get_host(self):
        """
        Mock get_host - returns a mock host object.
        """
        logger.info("🎭 MOCK: get_host() called")

        # Create a mock host object with required attributes
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
        """Mock get_client - returns a mock client."""
        logger.info("🎭 MOCK: get_client() called")
        return self._client

    def test_connection(self) -> bool:
        """Mock test_connection - always succeeds."""
        logger.info("🎭 MOCK: test_connection() called - returning True")
        return True

    def get_nodes(self) -> List[Dict[str, Any]]:
        """Mock get_nodes - returns a mock node."""
        logger.info("🎭 MOCK: get_nodes() called")
        return [
            {
                "node": self._mock_node,
                "status": "online",
                "type": "node",
                "maxcpu": 8,
                "cpu": 0.15,
                "maxmem": 32 * 1024**3,  # 32GB
                "mem": 8 * 1024**3,  # 8GB used
                "maxdisk": 500 * 1024**3,  # 500GB
                "disk": 100 * 1024**3,  # 100GB used
                "uptime": 86400 * 30,  # 30 days
            }
        ]

    def sync_nodes(self) -> int:
        """Mock sync_nodes - returns 1."""
        logger.info("🎭 MOCK: sync_nodes() called - synced 1 node")
        return 1

    def get_lxc_containers(self, node_name: str) -> List[Dict[str, Any]]:
        """Mock get_lxc_containers - returns mock containers."""
        logger.info(f"🎭 MOCK: get_lxc_containers(node={node_name}) called")
        return [
            {
                "vmid": vmid,
                "status": container["status"],
                "name": container["hostname"],
                "maxmem": container.get("memory", 2048) * 1024**2,
                "maxdisk": 8 * 1024**3,
            }
            for vmid, container in self._containers.items()
        ]

    def get_next_vmid(self) -> int:
        """Mock get_next_vmid - returns next available VMID."""
        vmid = self._next_vmid
        self._next_vmid += 1
        logger.info(f"🎭 MOCK: get_next_vmid() called - returning {vmid}")
        return vmid

    def create_lxc(
        self,
        node_name: str,
        vmid: int,
        hostname: str,
        ostemplate: str,
        password: str,
        memory: int = 2048,
        cores: int = 2,
        disk_size: str = "8",
        storage: str = "local-lvm",
        network_bridge: str = "vmbr0",
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Mock create_lxc - simulates container creation with delay.

        This method simulates the time it takes to create a container
        and adds it to the internal state with 'deploying' status.
        """
        logger.info(f"🎭 MOCK: create_lxc(vmid={vmid}, hostname={hostname}) - STARTING")
        logger.info(f"         Template: {ostemplate}, Memory: {memory}MB, Cores: {cores}")

        # Simulate deployment time (5 seconds)
        logger.info("         ⏳ Simulating container creation delay (5s)...")
        time.sleep(5)

        # Add container to internal state
        self._containers[vmid] = {
            "vmid": vmid,
            "hostname": hostname,
            "status": "stopped",  # Created but not started
            "ostemplate": ostemplate,
            "memory": memory,
            "cores": cores,
            "disk_size": disk_size,
            "node": node_name,
            "created_at": time.time(),
        }

        logger.info(f"🎭 MOCK: create_lxc(vmid={vmid}) - COMPLETED ✓")

        # Return mock task info
        return {"task": f"UPID:mock::{vmid}:createct:", "status": "success"}

    def configure_lxc_for_docker(self, node_name: str, vmid: int) -> None:
        """Mock configure_lxc_for_docker - simulates Docker configuration."""
        logger.info(f"🎭 MOCK: configure_lxc_for_docker(vmid={vmid}) - configuring...")
        time.sleep(1)  # Brief delay
        logger.info(f"🎭 MOCK: configure_lxc_for_docker(vmid={vmid}) - COMPLETED ✓")

    def start_lxc(self, node_name: str, vmid: int) -> Dict[str, Any]:
        """Mock start_lxc - simulates starting a container."""
        logger.info(f"🎭 MOCK: start_lxc(vmid={vmid}) - STARTING")

        if vmid not in self._containers:
            raise ProxmoxError(f"Container {vmid} not found")

        # Simulate startup time
        time.sleep(2)

        self._containers[vmid]["status"] = "running"
        logger.info(f"🎭 MOCK: start_lxc(vmid={vmid}) - COMPLETED ✓ (status=running)")

        return {"task": f"UPID:mock::{vmid}:vzstart:", "status": "success"}

    def stop_lxc(self, node_name: str, vmid: int, force: bool = False) -> Dict[str, Any]:
        """Mock stop_lxc - simulates stopping a container."""
        logger.info(f"🎭 MOCK: stop_lxc(vmid={vmid}, force={force}) - STOPPING")

        if vmid not in self._containers:
            raise ProxmoxError(f"Container {vmid} not found")

        # Simulate shutdown time
        time.sleep(1)

        self._containers[vmid]["status"] = "stopped"
        logger.info(f"🎭 MOCK: stop_lxc(vmid={vmid}) - COMPLETED ✓ (status=stopped)")

        return {"task": f"UPID:mock::{vmid}:vzstop:", "status": "success"}

    def delete_lxc(self, node_name: str, vmid: int, force: bool = False) -> Dict[str, Any]:
        """Mock delete_lxc - simulates deleting a container."""
        logger.info(f"🎭 MOCK: delete_lxc(vmid={vmid}, force={force}) - DELETING")

        if vmid not in self._containers:
            logger.warning(f"🎭 MOCK: Container {vmid} not found (already deleted?)")
            return {"task": f"UPID:mock::{vmid}:vzdestroy:", "status": "success"}

        # Simulate deletion time
        time.sleep(2)

        del self._containers[vmid]
        logger.info(f"🎭 MOCK: delete_lxc(vmid={vmid}) - COMPLETED ✓ (deleted)")

        return {"task": f"UPID:mock::{vmid}:vzdestroy:", "status": "success"}

    def create_snapshot(
        self, node_name: str, vmid: int, snapname: str, description: str = ""
    ) -> str:
        """Mock create_snapshot - simulates snapshot creation."""
        logger.info(f"🎭 MOCK: create_snapshot(vmid={vmid}, snapname={snapname})")
        time.sleep(1)
        return f"UPID:mock::{vmid}:vzsnapshot:"

    def delete_snapshot(self, node_name: str, vmid: int, snapname: str) -> str:
        """Mock delete_snapshot - simulates snapshot deletion."""
        logger.info(f"🎭 MOCK: delete_snapshot(vmid={vmid}, snapname={snapname})")
        time.sleep(0.5)
        return f"UPID:mock::{vmid}:vzdelsnapshot:"

    def clone_lxc(
        self,
        node_name: str,
        source_vmid: int,
        new_vmid: int,
        new_hostname: str,
        full: bool = True,
        timeout: int = 600,
    ) -> str:
        """
        Mock clone_lxc - simulates cloning a container.

        This creates a new container based on an existing one,
        copying all the configuration.
        """
        logger.info(
            f"🎭 MOCK: clone_lxc(source={source_vmid} → new={new_vmid}, hostname={new_hostname})"
        )

        if source_vmid not in self._containers:
            raise ProxmoxError(f"Source container {source_vmid} not found")

        # Simulate clone time (full clone takes longer)
        clone_time = 8 if full else 3
        logger.info(f"         ⏳ Simulating clone operation ({clone_time}s)...")
        time.sleep(clone_time)

        # Copy source container configuration
        source = self._containers[source_vmid]
        self._containers[new_vmid] = {
            "vmid": new_vmid,
            "hostname": new_hostname,
            "status": "stopped",
            "ostemplate": source["ostemplate"],
            "memory": source["memory"],
            "cores": source["cores"],
            "disk_size": source["disk_size"],
            "node": node_name,
            "cloned_from": source_vmid,
            "created_at": time.time(),
        }

        logger.info(f"🎭 MOCK: clone_lxc - COMPLETED ✓ (cloned {source_vmid} → {new_vmid})")
        return f"Container {source_vmid} successfully cloned to {new_vmid}"

    def get_lxc_status(self, node_name: str, vmid: int) -> Dict[str, Any]:
        """
        Mock get_lxc_status - returns current container status.

        This is critical for tests that poll for status changes.
        """
        if vmid not in self._containers:
            logger.warning(f"🎭 MOCK: get_lxc_status(vmid={vmid}) - NOT FOUND")
            raise ProxmoxError(f"Container {vmid} not found")

        container = self._containers[vmid]
        status_info = {
            "status": container["status"],
            "vmid": vmid,
            "name": container["hostname"],
            "uptime": 3600 if container["status"] == "running" else 0,
            "maxmem": container["memory"] * 1024**2,
            "mem": container["memory"] * 1024**2 * 0.3 if container["status"] == "running" else 0,
            "maxdisk": int(container["disk_size"]) * 1024**3,
            "disk": int(container["disk_size"]) * 1024**3 * 0.2,
            "cpus": container["cores"],
            "cpu": 0.15 if container["status"] == "running" else 0,
        }

        logger.info(f"🎭 MOCK: get_lxc_status(vmid={vmid}) - status={status_info['status']}")
        return status_info

    def get_lxc_metrics(self, node_name: str, vmid: int) -> Dict[str, Any]:
        """Mock get_lxc_metrics - returns mock metrics."""
        logger.info(f"🎭 MOCK: get_lxc_metrics(vmid={vmid})")

        if vmid not in self._containers:
            raise ProxmoxError(f"Container {vmid} not found")

        container = self._containers[vmid]
        is_running = container["status"] == "running"

        return {
            "cpu": random.uniform(0.1, 0.5) if is_running else 0,
            "mem": container["memory"] * 1024**2 * 0.3 if is_running else 0,
            "maxmem": container["memory"] * 1024**2,
            "disk": int(container["disk_size"]) * 1024**3 * 0.2,
            "maxdisk": int(container["disk_size"]) * 1024**3,
            "netin": random.randint(1000000, 10000000) if is_running else 0,
            "netout": random.randint(1000000, 10000000) if is_running else 0,
        }

    def get_lxc_config(self, node_name: str, vmid: int) -> Dict[str, Any]:
        """Mock get_lxc_config - returns mock configuration."""
        logger.info(f"🎭 MOCK: get_lxc_config(vmid={vmid})")

        if vmid not in self._containers:
            raise ProxmoxError(f"Container {vmid} not found")

        container = self._containers[vmid]
        return {
            "hostname": container["hostname"],
            "memory": container["memory"],
            "cores": container["cores"],
            "rootfs": f"local-lvm:{container['disk_size']}",
            "net0": "name=eth0,bridge=vmbr0,ip=dhcp",
            "ostype": "ubuntu",
        }

    def update_lxc_config(
        self, node_name: str, vmid: int, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Mock update_lxc_config - simulates config update."""
        logger.info(f"🎭 MOCK: update_lxc_config(vmid={vmid}, config={config})")

        if vmid not in self._containers:
            raise ProxmoxError(f"Container {vmid} not found")

        # Update internal state
        if "memory" in config:
            self._containers[vmid]["memory"] = config["memory"]
        if "cores" in config:
            self._containers[vmid]["cores"] = config["cores"]
        if "hostname" in config:
            self._containers[vmid]["hostname"] = config["hostname"]

        time.sleep(0.5)
        logger.info(f"🎭 MOCK: update_lxc_config(vmid={vmid}) - COMPLETED ✓")
        return {"status": "success"}

    def wait_for_task(
        self, node_name: str, task_upid: str, timeout: int = 300, poll_interval: int = 2
    ) -> bool:
        """
        Mock wait_for_task - simulates waiting for task completion.

        Since all our mock operations complete instantly or with sleep(),
        we can return immediately.
        """
        logger.info(f"🎭 MOCK: wait_for_task(task={task_upid}, timeout={timeout}s)")
        time.sleep(0.5)  # Brief delay to simulate polling
        logger.info("🎭 MOCK: wait_for_task - COMPLETED ✓")
        return True

    def execute_command(
        self, node_name: str, vmid: int, command: str, timeout: int = 30
    ) -> Dict[str, Any]:
        """Mock execute_command - simulates command execution."""
        logger.info(f"🎭 MOCK: execute_command(vmid={vmid}, command='{command}')")
        time.sleep(1)

        return {
            "stdout": f"MOCK: Command executed: {command}",
            "stderr": "",
            "exit_code": 0,
        }

    @classmethod
    def reset_mock_state(cls):
        """
        Reset all mock state (useful for test isolation).

        Call this in test teardown if needed.
        """
        logger.info("🎭 MOCK: Resetting all mock state")
        cls._containers.clear()
        cls._next_vmid = 1000
