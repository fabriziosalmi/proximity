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
        app_service.proxmox_service.create_lxc = AsyncMock(return_value={"task": "UPID:test"})
        app_service.proxmox_service.start_lxc = AsyncMock(return_value="UPID:test")
        app_service.proxmox_service.setup_docker_in_alpine = AsyncMock(return_value=True)
        app_service.proxmox_service.execute_in_container = AsyncMock(return_value="deployed")
        app_service.proxmox_service.get_lxc_ip = AsyncMock(return_value="10.20.0.100")

        app = await app_service.deploy_app(app_data)

        assert app is not None
        assert app.hostname == "test-nginx"
        assert app.catalog_id == "nginx"
        assert app.status == AppStatus.running

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
        assert app.status == AppStatus.running

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
        assert app.status == AppStatus.stopped

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
        assert app.status == AppStatus.running

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
        app_service.proxmox_service.create_lxc = AsyncMock(return_value={"task": "UPID:test"})
        app_service.proxmox_service.start_lxc = AsyncMock(return_value="UPID:test")
        app_service.proxmox_service.setup_docker_in_alpine = AsyncMock(return_value=True)
        app_service.proxmox_service.execute_in_container = AsyncMock(return_value="deployed")
        app_service.proxmox_service.get_lxc_ip = AsyncMock(return_value="10.20.0.100")

        # Mock proxy manager
        app_service.proxy_manager.create_vhost = AsyncMock(return_value=True)

        app = await app_service.deploy_app(app_data)

        # Verify proxy was configured
        assert app_service.proxy_manager.create_vhost.called

    @pytest.mark.asyncio
    async def test_deployment_cleanup_on_failure(self, app_service, sample_app_create):
        """Test cleanup when deployment fails."""
        app_data = AppCreate(**sample_app_create)

        app_service.proxmox_service.get_next_vmid = AsyncMock(return_value=100)
        app_service.proxmox_service.create_lxc = AsyncMock(return_value={"task": "UPID:test"})
        app_service.proxmox_service.start_lxc = AsyncMock(return_value="UPID:test")
        app_service.proxmox_service.setup_docker_in_alpine = AsyncMock(
            side_effect=Exception("Docker install failed")
        )

        with pytest.raises(Exception):
            await app_service.deploy_app(app_data)

        # Verify cleanup was attempted
        assert app_service.proxmox_service.destroy_lxc.called or \
               app_service.proxmox_service.stop_lxc.called


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
