"""
Tests for database transaction safety and ACID properties.
Ensures all operations are atomic and handle failures correctly.
"""

import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy.exc import IntegrityError
from models.database import User, App, DeploymentLog
from models.schemas import AppCreate, AppStatus
from services.app_service import AppService
from services.proxmox_service import ProxmoxError


class TestTransactionAtomicity:
    """Test that operations are atomic - all or nothing."""

    @pytest.mark.asyncio
    async def test_deploy_app_rollback_on_proxmox_error(
        self, db_session, mock_proxmox_service, mock_proxy_manager
    ):
        """Test deployment rollback when Proxmox fails."""
        app_service = AppService(mock_proxmox_service, db_session, mock_proxy_manager)

        # Mock Proxmox to fail after getting VMID
        mock_proxmox_service.get_next_vmid = AsyncMock(return_value=100)
        mock_proxmox_service.create_lxc = AsyncMock(
            side_effect=ProxmoxError("LXC creation failed")
        )
        mock_proxmox_service.get_best_node = AsyncMock(return_value="testnode")

        # Load catalog first
        await app_service._load_catalog()

        app_data = AppCreate(
            catalog_id="nginx",
            hostname="test-rollback",
            config={},
            environment={}
        )

        # Deployment should fail
        with pytest.raises(Exception):
            await app_service.deploy_app(app_data)

        # Database should NOT have the app record
        apps = db_session.query(App).filter(
            App.hostname == "test-rollback"
        ).all()
        assert len(apps) == 0

    @pytest.mark.asyncio
    async def test_delete_app_rollback_on_error(
        self, db_session, mock_proxmox_service, mock_proxy_manager, test_user
    ):
        """Test app deletion rollback when database error occurs."""
        app_service = AppService(mock_proxmox_service, db_session, mock_proxy_manager)

        # Create app in database
        app = App(
            id="delete-rollback",
            catalog_id="nginx",
            name="Delete Rollback",
            hostname="delete-rollback",
            status="stopped",
            lxc_id=100,
            node="testnode",
            owner_id=test_user.id
        )
        db_session.add(app)
        db_session.commit()

        # Mock Proxmox to succeed but force DB error
        mock_proxmox_service.destroy_lxc = AsyncMock(return_value="UPID:task")

        # Patch db.delete to raise error
        original_delete = db_session.delete

        def failing_delete(obj):
            original_delete(obj)
            raise Exception("Simulated DB error")

        with patch.object(db_session, 'delete', side_effect=failing_delete):
            with pytest.raises(Exception):
                await app_service.delete_app("delete-rollback")

        # Rollback should have occurred
        # Note: The app will still exist because we rolled back
        db_session.rollback()  # Clean up the failed transaction
        app = db_session.query(App).filter(App.id == "delete-rollback").first()
        assert app is not None


class TestTransactionIsolation:
    """Test transaction isolation and consistency."""

    def test_concurrent_user_creation(self, db_session):
        """Test that duplicate users can't be created concurrently."""
        user1 = User(
            username="concurrent",
            hashed_password=User.hash_password("pass1")
        )
        db_session.add(user1)
        db_session.commit()

        # Try to create duplicate (simulating concurrent request)
        user2 = User(
            username="concurrent",
            hashed_password=User.hash_password("pass2")
        )
        db_session.add(user2)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_app_hostname_uniqueness_enforced(self, db_session, test_user):
        """Test hostname uniqueness across concurrent deployments."""
        app1 = App(
            id="unique1",
            catalog_id="nginx",
            name="App 1",
            hostname="unique-hostname",
            status="running",
            lxc_id=100,
            node="node1",
            owner_id=test_user.id
        )
        db_session.add(app1)
        db_session.commit()

        # Try to create app with same hostname
        app2 = App(
            id="unique2",
            catalog_id="nginx",
            name="App 2",
            hostname="unique-hostname",  # Duplicate
            status="running",
            lxc_id=101,
            node="node1",
            owner_id=test_user.id
        )
        db_session.add(app2)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_lxc_id_uniqueness_enforced(self, db_session, test_user):
        """Test LXC ID uniqueness across deployments."""
        app1 = App(
            id="lxc1",
            catalog_id="nginx",
            name="App 1",
            hostname="host1",
            status="running",
            lxc_id=100,
            node="node1",
            owner_id=test_user.id
        )
        db_session.add(app1)
        db_session.commit()

        # Try to create app with same LXC ID
        app2 = App(
            id="lxc2",
            catalog_id="nginx",
            name="App 2",
            hostname="host2",
            status="running",
            lxc_id=100,  # Duplicate
            node="node1",
            owner_id=test_user.id
        )
        db_session.add(app2)

        with pytest.raises(IntegrityError):
            db_session.commit()


class TestTransactionConsistency:
    """Test that database state remains consistent."""

    @pytest.mark.asyncio
    async def test_app_status_consistency(
        self, db_session, mock_proxmox_service, mock_proxy_manager, test_user
    ):
        """Test app status remains consistent across operations."""
        app_service = AppService(mock_proxmox_service, db_session, mock_proxy_manager)

        # Create app
        app = App(
            id="status-consistency",
            catalog_id="nginx",
            name="Status Test",
            hostname="status-test",
            status="stopped",
            lxc_id=100,
            node="testnode",
            owner_id=test_user.id
        )
        db_session.add(app)
        db_session.commit()

        # Start app successfully
        mock_proxmox_service.start_lxc = AsyncMock(return_value="UPID:task")
        mock_proxmox_service.execute_in_container = AsyncMock(return_value="OK")

        await app_service.start_app("status-consistency")

        # Check status in database
        db_app = db_session.query(App).filter(App.id == "status-consistency").first()
        assert db_app.status == AppStatus.RUNNING.value

    @pytest.mark.asyncio
    async def test_app_status_consistency_on_error(
        self, db_session, mock_proxmox_service, mock_proxy_manager, test_user
    ):
        """Test app status set to error when operation fails."""
        app_service = AppService(mock_proxmox_service, db_session, mock_proxy_manager)

        # Create running app
        app = App(
            id="error-consistency",
            catalog_id="nginx",
            name="Error Test",
            hostname="error-test",
            status="running",
            lxc_id=100,
            node="testnode",
            owner_id=test_user.id
        )
        db_session.add(app)
        db_session.commit()

        # Mock Proxmox to fail
        mock_proxmox_service.start_lxc = AsyncMock(
            side_effect=ProxmoxError("Start failed")
        )

        # Try to start (will fail)
        with pytest.raises(Exception):
            await app_service.start_app("error-consistency")

        # Status should be set to error
        db_app = db_session.query(App).filter(App.id == "error-consistency").first()
        assert db_app.status == AppStatus.ERROR.value

    def test_user_cascade_delete_consistency(self, db_session, test_user):
        """Test cascade delete maintains consistency."""
        # Create apps
        app1 = App(
            id="cascade1",
            catalog_id="nginx",
            name="App 1",
            hostname="cascade1",
            status="running",
            lxc_id=100,
            node="node1",
            owner_id=test_user.id
        )
        app2 = App(
            id="cascade2",
            catalog_id="nginx",
            name="App 2",
            hostname="cascade2",
            status="running",
            lxc_id=101,
            node="node1",
            owner_id=test_user.id
        )
        db_session.add(app1)
        db_session.add(app2)
        db_session.commit()

        # Add deployment logs
        log1 = DeploymentLog(app_id="cascade1", level="info", message="Log 1")
        log2 = DeploymentLog(app_id="cascade2", level="info", message="Log 2")
        db_session.add(log1)
        db_session.add(log2)
        db_session.commit()

        # Delete user
        db_session.delete(test_user)
        db_session.commit()

        # All apps should be deleted
        apps = db_session.query(App).filter(App.owner_id == test_user.id).all()
        assert len(apps) == 0

        # All logs should be deleted
        logs = db_session.query(DeploymentLog).filter(
            DeploymentLog.app_id.in_(["cascade1", "cascade2"])
        ).all()
        assert len(logs) == 0


class TestTransactionDurability:
    """Test that committed transactions persist."""

    @pytest.mark.asyncio
    async def test_deployed_app_persists(
        self, db_session, mock_proxmox_service, mock_proxy_manager, test_user
    ):
        """Test successfully deployed app persists in database."""
        app_service = AppService(mock_proxmox_service, db_session, mock_proxy_manager)

        # Mock successful deployment
        mock_proxmox_service.get_next_vmid = AsyncMock(return_value=100)
        mock_proxmox_service.get_best_node = AsyncMock(return_value="testnode")
        mock_proxmox_service.create_lxc = AsyncMock(return_value={"task_id": "UPID:1"})
        mock_proxmox_service.start_lxc = AsyncMock(return_value="UPID:2")
        mock_proxmox_service.setup_docker_in_alpine = AsyncMock(return_value=True)
        mock_proxmox_service.execute_in_container = AsyncMock(return_value="OK")
        mock_proxmox_service.get_lxc_ip = AsyncMock(return_value="10.20.0.100")
        mock_proxmox_service.wait_for_task = AsyncMock(return_value=True)

        # Load catalog
        await app_service._load_catalog()

        app_data = AppCreate(
            catalog_id="wordpress",
            hostname="persist-test",
            config={},
            environment={}
        )

        # Deploy
        deployed_app = await app_service.deploy_app(app_data)

        # Query database directly
        db_app = db_session.query(App).filter(
            App.id == deployed_app.id
        ).first()

        assert db_app is not None
        assert db_app.hostname == "persist-test"
        assert db_app.status == AppStatus.RUNNING.value
        assert db_app.lxc_id == 100
        assert db_app.node == "testnode"

    def test_updated_app_status_persists(self, db_session, test_user):
        """Test app status update persists."""
        app = App(
            id="update-persist",
            catalog_id="nginx",
            name="Update Test",
            hostname="update-persist",
            status="running",
            lxc_id=100,
            node="node1",
            owner_id=test_user.id
        )
        db_session.add(app)
        db_session.commit()

        # Update status
        app.status = "stopped"
        db_session.commit()

        # Query fresh from database
        db_session.expire_all()
        db_app = db_session.query(App).filter(App.id == "update-persist").first()
        assert db_app.status == "stopped"

    def test_deleted_app_removal_persists(self, db_session, test_user):
        """Test app deletion persists."""
        app = App(
            id="delete-persist",
            catalog_id="nginx",
            name="Delete Test",
            hostname="delete-persist",
            status="stopped",
            lxc_id=100,
            node="node1",
            owner_id=test_user.id
        )
        db_session.add(app)
        db_session.commit()

        # Delete
        db_session.delete(app)
        db_session.commit()

        # Query fresh from database
        db_session.expire_all()
        db_app = db_session.query(App).filter(App.id == "delete-persist").first()
        assert db_app is None


class TestMultipleOperations:
    """Test multiple operations in sequence."""

    @pytest.mark.asyncio
    async def test_deploy_start_stop_delete_sequence(
        self, db_session, mock_proxmox_service, mock_proxy_manager
    ):
        """Test full app lifecycle maintains database consistency."""
        app_service = AppService(mock_proxmox_service, db_session, mock_proxy_manager)

        # Setup mocks for deployment
        mock_proxmox_service.get_next_vmid = AsyncMock(return_value=100)
        mock_proxmox_service.get_best_node = AsyncMock(return_value="testnode")
        mock_proxmox_service.create_lxc = AsyncMock(return_value={"task_id": "UPID:1"})
        mock_proxmox_service.start_lxc = AsyncMock(return_value="UPID:2")
        mock_proxmox_service.stop_lxc = AsyncMock(return_value="UPID:3")
        mock_proxmox_service.destroy_lxc = AsyncMock(return_value="UPID:4")
        mock_proxmox_service.setup_docker_in_alpine = AsyncMock(return_value=True)
        mock_proxmox_service.execute_in_container = AsyncMock(return_value="OK")
        mock_proxmox_service.get_lxc_ip = AsyncMock(return_value="10.20.0.100")
        mock_proxmox_service.wait_for_task = AsyncMock(return_value=True)

        # Load catalog
        await app_service._load_catalog()

        # 1. Deploy
        app_data = AppCreate(
            catalog_id="wordpress",
            hostname="lifecycle-test",
            config={},
            environment={}
        )
        app = await app_service.deploy_app(app_data)
        app_id = app.id

        # Verify deployed
        db_app = db_session.query(App).filter(App.id == app_id).first()
        assert db_app is not None
        assert db_app.status == AppStatus.RUNNING.value

        # 2. Stop
        await app_service.stop_app(app_id)
        db_session.expire_all()
        db_app = db_session.query(App).filter(App.id == app_id).first()
        assert db_app.status == AppStatus.STOPPED.value

        # 3. Start
        await app_service.start_app(app_id)
        db_session.expire_all()
        db_app = db_session.query(App).filter(App.id == app_id).first()
        assert db_app.status == AppStatus.RUNNING.value

        # 4. Delete
        await app_service.delete_app(app_id)
        db_session.expire_all()
        db_app = db_session.query(App).filter(App.id == app_id).first()
        assert db_app is None

    def test_multiple_apps_independent_transactions(self, db_session, test_user):
        """Test that operations on different apps are independent."""
        # Create app 1
        app1 = App(
            id="independent1",
            catalog_id="nginx",
            name="App 1",
            hostname="independent1",
            status="running",
            lxc_id=100,
            node="node1",
            owner_id=test_user.id
        )
        db_session.add(app1)
        db_session.commit()

        # Create app 2
        app2 = App(
            id="independent2",
            catalog_id="nginx",
            name="App 2",
            hostname="independent2",
            status="running",
            lxc_id=101,
            node="node1",
            owner_id=test_user.id
        )
        db_session.add(app2)
        db_session.commit()

        # Update app 1
        app1.status = "stopped"
        db_session.commit()

        # App 2 should be unaffected
        db_session.expire_all()
        db_app2 = db_session.query(App).filter(App.id == "independent2").first()
        assert db_app2.status == "running"

        # Delete app 1
        db_session.delete(app1)
        db_session.commit()

        # App 2 should still exist
        db_session.expire_all()
        db_app2 = db_session.query(App).filter(App.id == "independent2").first()
        assert db_app2 is not None


class TestRollbackScenarios:
    """Test various rollback scenarios."""

    def test_rollback_reverts_changes(self, db_session, test_user):
        """Test that rollback reverts uncommitted changes."""
        # Create app
        app = App(
            id="rollback-test",
            catalog_id="nginx",
            name="Rollback",
            hostname="rollback-test",
            status="running",
            lxc_id=100,
            node="node1",
            owner_id=test_user.id
        )
        db_session.add(app)
        db_session.commit()

        # Modify without committing
        app.status = "stopped"
        assert app.status == "stopped"

        # Rollback
        db_session.rollback()

        # Changes should be reverted
        db_session.expire_all()
        db_app = db_session.query(App).filter(App.id == "rollback-test").first()
        assert db_app.status == "running"

    def test_rollback_after_integrity_error(self, db_session, test_user):
        """Test database still usable after integrity error and rollback."""
        # Create app
        app1 = App(
            id="integrity1",
            catalog_id="nginx",
            name="App 1",
            hostname="integrity-test",
            status="running",
            lxc_id=100,
            node="node1",
            owner_id=test_user.id
        )
        db_session.add(app1)
        db_session.commit()

        # Try to create duplicate hostname
        app2 = App(
            id="integrity2",
            catalog_id="nginx",
            name="App 2",
            hostname="integrity-test",  # Duplicate
            status="running",
            lxc_id=101,
            node="node1",
            owner_id=test_user.id
        )
        db_session.add(app2)

        with pytest.raises(IntegrityError):
            db_session.commit()

        # Rollback
        db_session.rollback()

        # Database should still be usable
        app3 = App(
            id="integrity3",
            catalog_id="nginx",
            name="App 3",
            hostname="integrity-test-3",  # Unique
            status="running",
            lxc_id=102,
            node="node1",
            owner_id=test_user.id
        )
        db_session.add(app3)
        db_session.commit()

        # Verify app3 was created
        db_app = db_session.query(App).filter(App.id == "integrity3").first()
        assert db_app is not None
