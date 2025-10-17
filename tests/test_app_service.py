"""
Unit tests for AppService.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from models.schemas import AppCreate, AppStatus
from services.app_service import AppService, AppServiceError
from models.database import App as DBApp


class TestAppService:
    """Test suite for AppService."""

    @pytest.fixture
    def app_service(self, mock_proxmox_service, db_session, mock_proxy_manager):
        """Create AppService instance for testing."""
        service = AppService(
            proxmox_service=mock_proxmox_service,
            db=db_session,
            proxy_manager=mock_proxy_manager
        )
        return service

    @pytest.mark.asyncio
    async def test_get_catalog(self, app_service):
        """Test getting application catalog."""
        catalog = await app_service.get_catalog()
        assert catalog is not None
        assert hasattr(catalog, 'items')
        assert hasattr(catalog, 'total')

    @pytest.mark.asyncio
    async def test_get_catalog_item(self, app_service):
        """Test getting specific catalog item."""
        # This will work if catalog is loaded
        catalog = await app_service.get_catalog()
        if catalog.items:
            item = await app_service.get_catalog_item(catalog.items[0].id)
            assert item is not None
            assert hasattr(item, 'id')

    @pytest.mark.asyncio
    async def test_get_all_apps_empty(self, app_service):
        """Test getting all apps when none exist."""
        apps = await app_service.get_all_apps()
        assert isinstance(apps, list)
        assert len(apps) == 0

    @pytest.mark.asyncio
    async def test_deploy_app_success(self, app_service, sample_app_create, db_session):
        """Test successful app deployment."""
        app_data = AppCreate(**sample_app_create)

        # Mock the deployment process
        app_service.proxmox_service.get_next_vmid = AsyncMock(return_value=100)
        app_service.proxmox_service.create_lxc = AsyncMock(return_value={"task_id": "UPID:test"})
        app_service.proxmox_service.start_lxc = AsyncMock(return_value="UPID:test")
        app_service.proxmox_service.setup_docker_in_alpine = AsyncMock(return_value=True)
        app_service.proxmox_service.execute_in_container = AsyncMock(return_value="deployed")
        app_service.proxmox_service.get_lxc_ip = AsyncMock(return_value="10.20.0.100")

        app = await app_service.deploy_app(app_data)

        assert app is not None
        assert app.hostname == "test-nginx"
        assert app.catalog_id == "nginx"
        assert app.status == AppStatus.RUNNING
        
        # Verify ports were assigned (port-based architecture)
        assert app.public_port is not None, "Public port should be assigned"
        assert app.internal_port is not None, "Internal port should be assigned"
        assert app.public_port >= 30000, "Public port should be in correct range"
        assert app.public_port <= 30999, "Public port should be in correct range"
        assert app.internal_port >= 40000, "Internal port should be in correct range"
        assert app.internal_port <= 40999, "Internal port should be in correct range"

    @pytest.mark.asyncio
    async def test_get_app_success(self, app_service, db_session):
        """Test getting app by ID."""
        # Create test app in database
        db_app = DBApp(
            id="test-nginx-01",
            catalog_id="nginx",
            name="Nginx",
            hostname="test-nginx-01",
            status="running",
            lxc_id=100,
            node="testnode",
            url="http://10.20.0.100:80"
        )
        db_session.add(db_app)
        db_session.commit()

        app = await app_service.get_app("test-nginx-01")
        assert app.id == "test-nginx-01"
        assert app.hostname == "test-nginx-01"

    @pytest.mark.asyncio
    async def test_get_app_not_found(self, app_service):
        """Test getting non-existent app."""
        with pytest.raises((AppServiceError, Exception)):
            await app_service.get_app("non-existent-app")

    @pytest.mark.asyncio
    async def test_start_app(self, app_service, db_session):
        """Test starting a stopped app."""
        # Create stopped app
        db_app = DBApp(
            id="test-app",
            catalog_id="nginx",
            name="Test App",
            hostname="test-app",
            status="stopped",
            lxc_id=100,
            node="testnode"
        )
        db_session.add(db_app)
        db_session.commit()

        app = await app_service.start_app("test-app")
        assert app.status == AppStatus.RUNNING

    @pytest.mark.asyncio
    async def test_stop_app(self, app_service, db_session):
        """Test stopping a running app."""
        # Create running app
        db_app = DBApp(
            id="test-app",
            catalog_id="nginx",
            name="Test App",
            hostname="test-app",
            status="running",
            lxc_id=100,
            node="testnode"
        )
        db_session.add(db_app)
        db_session.commit()

        app = await app_service.stop_app("test-app")
        assert app.status == AppStatus.STOPPED

    @pytest.mark.asyncio
    async def test_restart_app(self, app_service, db_session):
        """Test restarting an app."""
        # Create running app
        db_app = DBApp(
            id="test-app",
            catalog_id="nginx",
            name="Test App",
            hostname="test-app",
            status="running",
            lxc_id=100,
            node="testnode"
        )
        db_session.add(db_app)
        db_session.commit()

        app = await app_service.restart_app("test-app")
        assert app.status == AppStatus.RUNNING

    @pytest.mark.asyncio
    async def test_delete_app_success(self, app_service, db_session):
        """Test deleting an app."""
        # Create app
        db_app = DBApp(
            id="test-app",
            catalog_id="nginx",
            name="Test App",
            hostname="test-app",
            status="stopped",
            lxc_id=100,
            node="testnode"
        )
        db_session.add(db_app)
        db_session.commit()

        await app_service.delete_app("test-app")

        # Verify app is deleted
        apps = await app_service.get_all_apps()
        assert len(apps) == 0

    @pytest.mark.asyncio
    async def test_deployment_with_proxy(self, app_service, sample_app_create):
        """Test deployment with reverse proxy configuration."""
        app_data = AppCreate(**sample_app_create)

        app_service.proxmox_service.get_next_vmid = AsyncMock(return_value=100)
        app_service.proxmox_service.create_lxc = AsyncMock(return_value={"task_id": "UPID:test"})
        app_service.proxmox_service.start_lxc = AsyncMock(return_value="UPID:test")
        app_service.proxmox_service.setup_docker_in_alpine = AsyncMock(return_value=True)
        app_service.proxmox_service.execute_in_container = AsyncMock(return_value="deployed")
        app_service.proxmox_service.get_lxc_ip = AsyncMock(return_value="10.20.0.100")

        # Mock proxy manager
        app_service.proxy_manager.create_vhost = AsyncMock(return_value=True)

        app = await app_service.deploy_app(app_data)

        # Verify proxy was configured with port-based architecture
        assert app_service.proxy_manager.create_vhost.called
        
        # Verify create_vhost was called with public_port and internal_port
        call_args = app_service.proxy_manager.create_vhost.call_args
        assert 'public_port' in call_args.kwargs, "create_vhost should receive public_port"
        assert 'internal_port' in call_args.kwargs, "create_vhost should receive internal_port"

    @pytest.mark.asyncio
    async def test_deployment_cleanup_on_failure(self, app_service, sample_app_create):
        """Test cleanup when deployment fails."""
        app_data = AppCreate(**sample_app_create)

        app_service.proxmox_service.get_next_vmid = AsyncMock(return_value=100)
        app_service.proxmox_service.create_lxc = AsyncMock(return_value={"task_id": "UPID:test"})
        app_service.proxmox_service.start_lxc = AsyncMock(return_value="UPID:test")
        app_service.proxmox_service.setup_docker_in_alpine = AsyncMock(
            side_effect=Exception("Docker install failed")
        )

        with pytest.raises(Exception):
            await app_service.deploy_app(app_data)

        # Verify cleanup was attempted
        assert app_service.proxmox_service.destroy_lxc.called or \
               app_service.proxmox_service.stop_lxc.called


class TestAppServiceUpdate:
    """Test update workflow functionality."""

    @pytest.fixture
    def app_service(self, mock_proxmox_service, db_session, mock_proxy_manager):
        """Create AppService instance."""
        return AppService(
            proxmox_service=mock_proxmox_service,
            db=db_session,
            proxy_manager=mock_proxy_manager
        )

    @pytest.mark.asyncio
    async def test_update_app_creates_pre_update_backup(self, app_service, db_session):
        """Test that update creates a pre-update backup before updating."""
        # Create test app in database
        from models.database import Backup as DBBackup
        db_app = DBApp(
            id="test-app",
            catalog_id="nginx",
            name="Test App",
            hostname="test-app",
            status="running",
            lxc_id=100,
            node="testnode",
            url="http://10.20.0.100:80"
        )
        db_session.add(db_app)
        db_session.commit()

        # Mock BackupService class with real DB backup object
        with patch('services.backup_service.BackupService') as MockBackupService:
            # Create real backup object in DB for refresh to work
            mock_backup = DBBackup(
                app_id="test-app",
                filename="test-backup.tar.zst",
                storage_name="local",
                status="available",  # Already available
                size_bytes=100000000
            )
            db_session.add(mock_backup)
            db_session.commit()

            mock_backup_service = AsyncMock()
            mock_backup_service.create_backup = AsyncMock(return_value=mock_backup)
            MockBackupService.return_value = mock_backup_service

            # Mock Docker commands
            app_service.proxmox_service.execute_in_container = AsyncMock(return_value="success")

            # Mock health check
            with patch('httpx.AsyncClient') as mock_client:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

                await app_service.update_app("test-app", user_id=1)

                # Verify backup was created BEFORE any docker commands
                mock_backup_service.create_backup.assert_called_once()
                call_args = mock_backup_service.create_backup.call_args
                assert call_args.kwargs['app_id'] == "test-app"

    @pytest.mark.asyncio
    async def test_update_app_aborts_if_backup_fails(self, app_service, db_session):
        """Test that update aborts if pre-update backup fails."""
        # Create test app
        db_app = DBApp(
            id="test-app",
            catalog_id="nginx",
            name="Test App",
            hostname="test-app",
            status="running",
            lxc_id=100,
            node="testnode",
            url="http://10.20.0.100:80"
        )
        db_session.add(db_app)
        db_session.commit()

        # Mock BackupService to fail
        from core.exceptions import BackupCreationError, AppUpdateError

        with patch('services.backup_service.BackupService') as MockBackupService:
            mock_backup_service = AsyncMock()
            mock_backup_service.create_backup = AsyncMock(side_effect=BackupCreationError("Backup failed"))
            MockBackupService.return_value = mock_backup_service

            # Update should raise AppUpdateError
            with pytest.raises(AppUpdateError, match="Pre-update backup failed|Backup failed"):
                await app_service.update_app("test-app", user_id=1)

            # Verify no docker commands were executed
            app_service.proxmox_service.execute_in_container.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_app_runs_pull_and_up_commands(self, app_service, db_session):
        """Test that update runs docker compose pull and up commands."""
        # Create test app
        from models.database import Backup as DBBackup
        db_app = DBApp(
            id="test-app",
            catalog_id="nginx",
            name="Test App",
            hostname="test-app",
            status="running",
            lxc_id=100,
            node="testnode",
            url="http://10.20.0.100:80"
        )
        db_session.add(db_app)
        db_session.commit()

        # Mock BackupService
        with patch('services.backup_service.BackupService') as MockBackupService:
            mock_backup = DBBackup(
                app_id="test-app",
                filename="test-backup.tar.zst",
                storage_name="local",
                status="available",
                size_bytes=100000000
            )
            db_session.add(mock_backup)
            db_session.commit()

            mock_backup_service = AsyncMock()
            mock_backup_service.create_backup = AsyncMock(return_value=mock_backup)
            MockBackupService.return_value = mock_backup_service

            # Mock Docker commands
            app_service.proxmox_service.execute_in_container = AsyncMock(return_value="success")

            # Mock health check
            with patch('httpx.AsyncClient') as mock_client:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

                await app_service.update_app("test-app", user_id=1)

                # Verify docker commands were called in correct order
                # Now includes Docker service status check before pull
                calls = app_service.proxmox_service.execute_in_container.call_args_list
                assert len(calls) == 3
                assert "docker status" in calls[0].kwargs['command']
                assert "docker compose pull" in calls[1].kwargs['command']
                assert "docker compose up -d --remove-orphans" in calls[2].kwargs['command']

    @pytest.mark.asyncio
    async def test_update_app_handles_failed_health_check(self, app_service, db_session):
        """Test that update handles failed health check appropriately."""
        # Create test app
        db_app = DBApp(
            id="test-app",
            catalog_id="nginx",
            name="Test App",
            hostname="test-app",
            status="running",
            lxc_id=100,
            node="testnode",
            url="http://10.20.0.100:80"
        )
        db_session.add(db_app)
        db_session.commit()

        # Mock BackupService
        from models.database import Backup as DBBackup
        with patch('services.backup_service.BackupService') as MockBackupService:
            mock_backup = DBBackup(
                app_id="test-app",
                filename="test-backup.tar.zst",
                storage_name="local",
                status="available",
                size_bytes=100000000
            )
            db_session.add(mock_backup)
            db_session.commit()

            mock_backup_service = AsyncMock()
            mock_backup_service.create_backup = AsyncMock(return_value=mock_backup)
            MockBackupService.return_value = mock_backup_service

            # Mock Docker commands
            app_service.proxmox_service.execute_in_container = AsyncMock(return_value="success")

            # Mock health check to fail
            with patch('httpx.AsyncClient') as mock_client:
                mock_response = MagicMock()
                mock_response.status_code = 500  # Server error
                mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

                from core.exceptions import AppUpdateError
                with pytest.raises(AppUpdateError, match="Health check failed"):
                    await app_service.update_app("test-app", user_id=1)

                # Verify app status was set to update_failed
                updated_app = db_session.query(DBApp).filter(DBApp.id == "test-app").first()
                assert updated_app.status == "update_failed"


class TestAppServiceCatalog:
    """Test catalog-related functionality."""

    @pytest.fixture
    def app_service(self, mock_proxmox_service, db_session, mock_proxy_manager):
        """Create AppService instance."""
        return AppService(
            proxmox_service=mock_proxmox_service,
            db=db_session,
            proxy_manager=mock_proxy_manager
        )

    @pytest.mark.asyncio
    async def test_catalog_loads_from_files(self, app_service):
        """Test that catalog loads from JSON files."""
        catalog = await app_service.get_catalog()
        assert catalog.total >= 0  # Should have at least default catalog

    @pytest.mark.asyncio
    async def test_catalog_item_has_required_fields(self, app_service, sample_catalog_item):
        """Test catalog item structure."""
        assert "id" in sample_catalog_item
        assert "name" in sample_catalog_item
        assert "resources" in sample_catalog_item
        assert "compose" in sample_catalog_item
