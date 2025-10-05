"""
Unit tests for App Clone and Config Edit features.

Tests:
- Clone App functionality
- Config Edit (CPU/RAM/Disk updates)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from models.database import App as DBApp, get_db
from models.schemas import App, AppStatus, AppCatalogItem
from services.app_service import AppService
from services.proxmox_service import ProxmoxService
from core.exceptions import (
    AppNotFoundError,
    AppAlreadyExistsError,
    AppOperationError
)


@pytest.fixture
def mock_proxmox_for_clone():
    """Mock ProxmoxService for clone/config tests."""
    mock = AsyncMock(spec=ProxmoxService)
    mock.get_next_vmid = AsyncMock(return_value=100)
    mock.clone_lxc = AsyncMock(return_value={"task_id": "task123", "newid": 100})
    mock.wait_for_task = AsyncMock()
    mock.start_lxc = AsyncMock(return_value="start_task")
    mock.get_lxc_ip = AsyncMock(return_value="10.20.0.100")
    mock.update_lxc_config = AsyncMock(return_value="update_task")
    mock.resize_lxc_disk = AsyncMock(return_value="resize_task")
    mock.network_manager = None
    return mock


@pytest.fixture
def app_service(db_session, mock_proxmox_for_clone):
    """Create AppService instance for testing."""
    service = AppService(mock_proxmox_for_clone, db_session)

    # Mock catalog
    service._catalog_cache = MagicMock()
    service._catalog_cache.items = [
        AppCatalogItem(
            id="nginx",
            name="NGINX",
            version="1.0.0",
            category="Web Servers",
            description="NGINX web server",
            icon="",
            docker_compose={},
            ports=[80],
            min_cpu=1,
            min_memory=512,
            environment={}
        )
    ]
    service._catalog_loaded = True

    return service


class TestCloneApp:
    """Test suite for clone_app functionality."""

    @pytest.fixture
    def source_app(self, db_session, test_user):
        """Create a source app for cloning tests."""
        app = DBApp(
            id="nginx-source",
            catalog_id="nginx",
            name="NGINX",
            hostname="nginx-source",
            status="running",
            url="http://192.168.1.100:30001",
            iframe_url="http://192.168.1.100:40001",
            lxc_id=100,
            node="pve",
            public_port=30001,
            internal_port=40001,
            config={"cpu_cores": 2, "memory_mb": 2048},
            environment={"ENV_VAR": "value"},
            ports={80: 80},
            volumes=[{"host_path": "/data/nginx", "container_path": "/usr/share/nginx/html"}],
            owner_id=test_user.id
        )
        db_session.add(app)
        db_session.commit()
        db_session.refresh(app)
        return app

    @pytest.mark.asyncio
    async def test_clone_app_success(self, app_service, source_app, db_session):
        """Test successful app cloning."""
        new_hostname = "nginx-clone"

        # Mock Proxmox operations
        app_service.proxmox_service.get_next_vmid = AsyncMock(return_value=101)
        app_service.proxmox_service.clone_lxc = AsyncMock(return_value={"task_id": "UPID:task123", "newid": 101})
        app_service.proxmox_service.wait_for_task = AsyncMock()
        app_service.proxmox_service.start_lxc = AsyncMock(return_value="UPID:start123")
        app_service.proxmox_service.get_lxc_ip = AsyncMock(return_value="10.20.0.101")

        # Mock port manager
        app_service.port_manager.assign_next_available_ports = AsyncMock(return_value=(30002, 40002))

        # Mock proxy manager
        mock_proxy = AsyncMock()
        mock_proxy.create_vhost = AsyncMock(return_value=True)
        app_service._proxy_manager = mock_proxy

        # Mock network manager for WAN IP
        app_service.proxmox_service.network_manager = MagicMock()
        app_service.proxmox_service.network_manager.appliance_info = MagicMock()
        app_service.proxmox_service.network_manager.appliance_info.wan_ip = "192.168.1.100"

        # Execute clone
        cloned_app = await app_service.clone_app(source_app.id, new_hostname)

        # Verify clone was called correctly
        app_service.proxmox_service.clone_lxc.assert_called_once()
        clone_call = app_service.proxmox_service.clone_lxc.call_args
        assert clone_call.kwargs['vmid'] == 100
        assert clone_call.kwargs['newid'] == 101
        assert clone_call.kwargs['name'] == new_hostname
        assert clone_call.kwargs['full'] is True

        # Verify cloned app properties
        assert cloned_app.hostname == new_hostname
        assert cloned_app.id == f"nginx-{new_hostname}"
        assert cloned_app.lxc_id == 101
        assert cloned_app.public_port == 30002
        assert cloned_app.internal_port == 40002
        assert cloned_app.config == source_app.config  # Config copied
        assert cloned_app.environment == source_app.environment  # Env copied
        assert cloned_app.volumes == source_app.volumes  # Volumes copied

        # Verify reverse proxy was configured
        mock_proxy.create_vhost.assert_called_once()

        # Verify ports were allocated
        app_service.port_manager.assign_next_available_ports.assert_called_once()

        # Verify database entry
        db_cloned = db_session.query(DBApp).filter(DBApp.id == cloned_app.id).first()
        assert db_cloned is not None
        assert db_cloned.hostname == new_hostname

    @pytest.mark.asyncio
    async def test_clone_app_source_not_found(self, app_service):
        """Test cloning non-existent app raises AppNotFoundError."""
        with pytest.raises(AppNotFoundError):
            await app_service.clone_app("nonexistent-app", "new-hostname")

    @pytest.mark.asyncio
    async def test_clone_app_duplicate_hostname(self, app_service, source_app, db_session):
        """Test cloning with existing hostname raises AppAlreadyExistsError."""
        # Create app with target hostname
        existing = DBApp(
            id="nginx-existing",
            catalog_id="nginx",
            name="NGINX",
            hostname="nginx-existing",
            status="running",
            lxc_id=200,
            node="pve"
        )
        db_session.add(existing)
        db_session.commit()

        # Try to clone with same hostname
        with pytest.raises(AppAlreadyExistsError):
            await app_service.clone_app(source_app.id, "nginx-existing")

    @pytest.mark.asyncio
    async def test_clone_app_proxmox_failure_cleanup(self, app_service, source_app, db_session):
        """Test cleanup on Proxmox clone failure."""
        new_hostname = "nginx-fail"

        # Mock successful setup
        app_service.proxmox_service.get_next_vmid = AsyncMock(return_value=101)
        app_service.port_manager.assign_next_available_ports = AsyncMock(return_value=(30002, 40002))

        # Mock clone failure
        app_service.proxmox_service.clone_lxc = AsyncMock(
            side_effect=Exception("Clone failed")
        )

        # Mock cleanup methods
        app_service.proxmox_service.destroy_lxc = AsyncMock()
        app_service.port_manager.release_ports_for_app = AsyncMock()

        # Execute clone (should fail)
        with pytest.raises(AppOperationError, match="Failed to clone application"):
            await app_service.clone_app(source_app.id, new_hostname)

        # Verify database was rolled back (no new app)
        new_app_id = f"nginx-{new_hostname}"
        db_app = db_session.query(DBApp).filter(DBApp.id == new_app_id).first()
        assert db_app is None

    @pytest.mark.asyncio
    async def test_clone_app_copies_all_properties(self, app_service, source_app, db_session):
        """Test that clone copies all relevant properties from source."""
        new_hostname = "nginx-full-clone"

        # Setup mocks
        app_service.proxmox_service.get_next_vmid = AsyncMock(return_value=101)
        app_service.proxmox_service.clone_lxc = AsyncMock(return_value={"task_id": "task123", "newid": 101})
        app_service.proxmox_service.wait_for_task = AsyncMock()
        app_service.proxmox_service.start_lxc = AsyncMock(return_value="start123")
        app_service.proxmox_service.get_lxc_ip = AsyncMock(return_value="10.20.0.101")
        app_service.port_manager.assign_next_available_ports = AsyncMock(return_value=(30002, 40002))
        app_service._proxy_manager = AsyncMock()
        app_service._proxy_manager.create_vhost = AsyncMock(return_value=True)
        app_service.proxmox_service.network_manager = MagicMock()
        app_service.proxmox_service.network_manager.appliance_info = MagicMock()
        app_service.proxmox_service.network_manager.appliance_info.wan_ip = "192.168.1.100"

        # Execute
        cloned = await app_service.clone_app(source_app.id, new_hostname)

        # Verify all properties copied
        assert cloned.catalog_id == source_app.catalog_id
        assert cloned.name == source_app.name
        assert cloned.config == source_app.config
        assert cloned.environment == source_app.environment
        assert cloned.ports == source_app.ports
        assert cloned.volumes == source_app.volumes


class TestUpdateAppConfig:
    """Test suite for update_app_config functionality."""

    @pytest.fixture
    def running_app(self, db_session, test_user):
        """Create a running app for config tests."""
        app = DBApp(
            id="nginx-config",
            catalog_id="nginx",
            name="NGINX",
            hostname="nginx-config",
            status="running",
            lxc_id=100,
            node="pve",
            config={"cpu_cores": 1, "memory_mb": 1024, "disk_gb": 10},
            owner_id=test_user.id
        )
        db_session.add(app)
        db_session.commit()
        db_session.refresh(app)
        return app

    @pytest.mark.asyncio
    async def test_update_cpu_cores(self, app_service, running_app, db_session):
        """Test updating CPU cores."""
        # Mock Proxmox operations
        app_service.proxmox_service.update_lxc_config = AsyncMock(return_value="task123")

        # Mock stop/start (app is running)
        with patch.object(app_service, 'stop_app', new_callable=AsyncMock) as mock_stop, \
             patch.object(app_service, 'start_app', new_callable=AsyncMock) as mock_start:

            # Execute update
            updated_app = await app_service.update_app_config(running_app.id, cpu_cores=4)

            # Verify stop was called
            mock_stop.assert_called_once_with(running_app.id)

            # Verify config update was called
            app_service.proxmox_service.update_lxc_config.assert_called_once()
            call_args = app_service.proxmox_service.update_lxc_config.call_args
            assert call_args.kwargs['config']['cores'] == 4

            # Verify start was called
            mock_start.assert_called_once_with(running_app.id)

            # Verify database updated
            db_app = db_session.query(DBApp).filter(DBApp.id == running_app.id).first()
            assert db_app.config['cpu_cores'] == 4

    @pytest.mark.asyncio
    async def test_update_memory(self, app_service, running_app, db_session):
        """Test updating memory allocation."""
        app_service.proxmox_service.update_lxc_config = AsyncMock(return_value="task123")

        with patch.object(app_service, 'stop_app', new_callable=AsyncMock), \
             patch.object(app_service, 'start_app', new_callable=AsyncMock):

            updated_app = await app_service.update_app_config(running_app.id, memory_mb=4096)

            # Verify memory was updated
            call_args = app_service.proxmox_service.update_lxc_config.call_args
            assert call_args.kwargs['config']['memory'] == 4096

            # Verify database
            db_app = db_session.query(DBApp).filter(DBApp.id == running_app.id).first()
            assert db_app.config['memory_mb'] == 4096

    @pytest.mark.asyncio
    async def test_update_disk_size(self, app_service, running_app, db_session):
        """Test updating disk size."""
        app_service.proxmox_service.resize_lxc_disk = AsyncMock(return_value="task123")

        with patch.object(app_service, 'stop_app', new_callable=AsyncMock), \
             patch.object(app_service, 'start_app', new_callable=AsyncMock):

            updated_app = await app_service.update_app_config(running_app.id, disk_gb=20)

            # Verify disk resize was called
            app_service.proxmox_service.resize_lxc_disk.assert_called_once()
            call_args = app_service.proxmox_service.resize_lxc_disk.call_args
            assert call_args.args[2] == 20  # disk_gb argument

            # Verify database
            db_app = db_session.query(DBApp).filter(DBApp.id == running_app.id).first()
            assert db_app.config['disk_gb'] == 20

    @pytest.mark.asyncio
    async def test_update_multiple_resources(self, app_service, running_app, db_session):
        """Test updating CPU, memory, and disk together."""
        app_service.proxmox_service.update_lxc_config = AsyncMock(return_value="task123")
        app_service.proxmox_service.resize_lxc_disk = AsyncMock(return_value="task456")

        with patch.object(app_service, 'stop_app', new_callable=AsyncMock), \
             patch.object(app_service, 'start_app', new_callable=AsyncMock):

            updated_app = await app_service.update_app_config(
                running_app.id,
                cpu_cores=4,
                memory_mb=8192,
                disk_gb=50
            )

            # Verify both methods called
            app_service.proxmox_service.update_lxc_config.assert_called_once()
            app_service.proxmox_service.resize_lxc_disk.assert_called_once()

            # Verify database has all updates
            db_app = db_session.query(DBApp).filter(DBApp.id == running_app.id).first()
            assert db_app.config['cpu_cores'] == 4
            assert db_app.config['memory_mb'] == 8192
            assert db_app.config['disk_gb'] == 50

    @pytest.mark.asyncio
    async def test_update_no_parameters_raises_error(self, app_service, running_app):
        """Test that calling with no parameters raises AppOperationError."""
        with pytest.raises(AppOperationError, match="At least one configuration parameter must be provided"):
            await app_service.update_app_config(running_app.id)

    @pytest.mark.asyncio
    async def test_update_app_not_found(self, app_service):
        """Test updating non-existent app raises AppNotFoundError."""
        with pytest.raises(AppNotFoundError):
            await app_service.update_app_config("nonexistent-app", cpu_cores=2)

    @pytest.mark.asyncio
    async def test_update_stopped_app_no_restart(self, app_service, db_session, test_user):
        """Test updating stopped app doesn't call start/stop."""
        # Create stopped app
        stopped_app = DBApp(
            id="nginx-stopped",
            catalog_id="nginx",
            name="NGINX",
            hostname="nginx-stopped",
            status="stopped",
            lxc_id=100,
            node="pve",
            config={},
            owner_id=test_user.id
        )
        db_session.add(stopped_app)
        db_session.commit()

        app_service.proxmox_service.update_lxc_config = AsyncMock(return_value="task123")

        with patch.object(app_service, 'stop_app', new_callable=AsyncMock) as mock_stop, \
             patch.object(app_service, 'start_app', new_callable=AsyncMock) as mock_start:

            await app_service.update_app_config(stopped_app.id, cpu_cores=2)

            # Verify stop/start were NOT called
            mock_stop.assert_not_called()
            mock_start.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_failure_attempts_restart(self, app_service, running_app):
        """Test that update failure attempts to restart the app."""
        app_service.proxmox_service.update_lxc_config = AsyncMock(
            side_effect=Exception("Update failed")
        )

        with patch.object(app_service, 'stop_app', new_callable=AsyncMock), \
             patch.object(app_service, 'start_app', new_callable=AsyncMock) as mock_start:

            with pytest.raises(AppOperationError, match="Failed to update configuration"):
                await app_service.update_app_config(running_app.id, cpu_cores=4)

            # Verify start was attempted (rollback)
            mock_start.assert_called_once()
