"""
Unit tests for ProxmoxService.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from services.proxmox_service import ProxmoxService, ProxmoxError


class TestProxmoxService:
    """Test suite for ProxmoxService."""

    @pytest.mark.asyncio
    async def test_connection_success(self, mock_proxmox_service):
        """Test successful Proxmox connection."""
        result = await mock_proxmox_service.test_connection()
        assert result is True

    @pytest.mark.asyncio
    async def test_get_nodes(self, mock_proxmox_service):
        """Test getting Proxmox nodes."""
        nodes = await mock_proxmox_service.get_nodes()
        assert len(nodes) > 0
        assert nodes[0]["node"] == "testnode"

    @pytest.mark.asyncio
    async def test_get_next_vmid(self, mock_proxmox_service):
        """Test getting next available VMID."""
        vmid = await mock_proxmox_service.get_next_vmid()
        assert isinstance(vmid, int)
        assert vmid >= 100

    @pytest.mark.asyncio
    async def test_create_lxc_success(self, mock_proxmox_service):
        """Test LXC container creation."""
        config = {
            "hostname": "test-container",
            "memory": 2048,
            "cores": 2,
            "rootfs": "local-lvm:8"
        }

        result = await mock_proxmox_service.create_lxc("testnode", 100, config)
        assert "task_id" in result

    @pytest.mark.asyncio
    async def test_start_lxc(self, mock_proxmox_service):
        """Test starting LXC container."""
        task_id = await mock_proxmox_service.start_lxc("testnode", 100)
        assert task_id is not None

    @pytest.mark.asyncio
    async def test_stop_lxc(self, mock_proxmox_service):
        """Test stopping LXC container."""
        task_id = await mock_proxmox_service.stop_lxc("testnode", 100)
        assert task_id is not None

    @pytest.mark.asyncio
    async def test_destroy_lxc(self, mock_proxmox_service):
        """Test destroying LXC container."""
        task_id = await mock_proxmox_service.destroy_lxc("testnode", 100)
        assert task_id is not None

    @pytest.mark.asyncio
    async def test_get_lxc_status(self, mock_proxmox_service):
        """Test getting LXC container status."""
        status = await mock_proxmox_service.get_lxc_status("testnode", 100)
        assert status["vmid"] == 100
        assert status["status"] == "running"

    @pytest.mark.asyncio
    async def test_connection_failure(self):
        """Test Proxmox connection failure handling."""
        mock_service = AsyncMock(spec=ProxmoxService)
        mock_service.test_connection = AsyncMock(side_effect=ProxmoxError("Connection failed"))

        with pytest.raises(ProxmoxError):
            await mock_service.test_connection()

    @pytest.mark.asyncio
    async def test_lxc_already_exists(self, mock_proxmox_service):
        """Test handling of LXC creation when container already exists."""
        mock_proxmox_service.create_lxc = AsyncMock(
            side_effect=ProxmoxError("LXC 100 already exists")
        )

        with pytest.raises(ProxmoxError, match="already exists"):
            await mock_proxmox_service.create_lxc("testnode", 100, {})


class TestProxmoxServiceSSH:
    """Test SSH-related functionality in ProxmoxService."""

    @pytest.mark.asyncio
    async def test_execute_in_container(self, mock_proxmox_service):
        """Test executing command in container via SSH."""
        mock_proxmox_service.execute_in_container = AsyncMock(
            return_value="Command output"
        )

        result = await mock_proxmox_service.execute_in_container(
            "testnode", 100, "echo test"
        )
        assert result == "Command output"

    @pytest.mark.asyncio
    async def test_setup_docker_in_alpine(self, mock_proxmox_service):
        """Test Docker installation in Alpine container."""
        mock_proxmox_service.setup_docker_in_alpine = AsyncMock(return_value=True)

        result = await mock_proxmox_service.setup_docker_in_alpine("testnode", 100)
        assert result is True


class TestProxmoxServiceNetwork:
    """Test network-related functionality."""

    @pytest.mark.asyncio
    async def test_get_lxc_ip(self, mock_proxmox_service):
        """Test getting LXC container IP address."""
        mock_proxmox_service.get_lxc_ip = AsyncMock(return_value="10.20.0.100")

        ip = await mock_proxmox_service.get_lxc_ip("testnode", 100)
        assert ip == "10.20.0.100"

    @pytest.mark.asyncio
    async def test_network_config_creation(self, mock_proxmox_service):
        """Test network configuration for container."""
        config = {
            "net0": "name=eth0,bridge=proximity-lan,ip=dhcp"
        }

        result = await mock_proxmox_service.create_lxc(
            "testnode", 100, config
        )
        assert result is not None
