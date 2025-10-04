"""
Unit tests for database models.
Tests model relationships, constraints, and methods.
"""

import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from models.database import User, App, DeploymentLog, AuditLog


class TestUserModel:
    """Test suite for User model."""

    def test_create_user(self, db_session):
        """Test creating a user."""
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=User.hash_password("password123"),
            role="user"
        )
        db_session.add(user)
        db_session.commit()

        assert user.id is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.role == "user"
        assert user.is_active is True
        assert user.created_at is not None

    def test_user_unique_username(self, db_session, test_user):
        """Test username uniqueness constraint."""
        duplicate_user = User(
            username="testuser",  # Same as test_user
            email="another@example.com",
            hashed_password=User.hash_password("password")
        )
        db_session.add(duplicate_user)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_user_unique_email(self, db_session, test_user):
        """Test email uniqueness constraint."""
        duplicate_user = User(
            username="anotheruser",
            email="test@example.com",  # Same as test_user
            hashed_password=User.hash_password("password")
        )
        db_session.add(duplicate_user)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_user_password_hashing(self):
        """Test password hashing produces different hashes."""
        password = "mypassword"
        hash1 = User.hash_password(password)
        hash2 = User.hash_password(password)

        # Different hashes due to salt
        assert hash1 != hash2
        assert hash1 != password
        assert hash2 != password

    def test_user_password_verification(self, test_user):
        """Test password verification."""
        # Correct password
        assert test_user.verify_password("testpass123") is True

        # Wrong password
        assert test_user.verify_password("wrongpassword") is False

    def test_user_without_email(self, db_session):
        """Test creating user without email (nullable)."""
        user = User(
            username="noemail",
            email=None,
            hashed_password=User.hash_password("password")
        )
        db_session.add(user)
        db_session.commit()

        assert user.id is not None
        assert user.email is None

    def test_user_role_default(self, db_session):
        """Test default role is 'user'."""
        user = User(
            username="defaultrole",
            hashed_password=User.hash_password("password")
        )
        db_session.add(user)
        db_session.commit()

        assert user.role == "user"

    def test_user_is_active_default(self, db_session):
        """Test default is_active is True."""
        user = User(
            username="active",
            hashed_password=User.hash_password("password")
        )
        db_session.add(user)
        db_session.commit()

        assert user.is_active is True

    def test_user_representation(self, test_user):
        """Test user string representation."""
        repr_str = repr(test_user)
        assert "User" in repr_str
        assert "testuser" in repr_str
        assert "user" in repr_str


class TestAppModel:
    """Test suite for App model."""

    def test_create_app(self, db_session, test_user):
        """Test creating an app."""
        app = App(
            id="nginx-test",
            catalog_id="nginx",
            name="Nginx",
            hostname="test-nginx",
            status="running",
            url="http://10.20.0.100:80",
            lxc_id=100,
            node="testnode",
            owner_id=test_user.id,
            config={"key": "value"},
            ports={80: 80},
            volumes=["/data"],
            environment={"ENV": "prod"}
        )
        db_session.add(app)
        db_session.commit()

        assert app.id == "nginx-test"
        assert app.catalog_id == "nginx"
        assert app.name == "Nginx"
        assert app.hostname == "test-nginx"
        assert app.status == "running"
        assert app.lxc_id == 100
        assert app.node == "testnode"
        assert app.owner_id == test_user.id
        assert app.config == {"key": "value"}
        # JSON storage converts integer keys to strings
        assert app.ports == {"80": 80} or app.ports == {80: 80}
        assert app.volumes == ["/data"]
        assert app.environment == {"ENV": "prod"}

    def test_app_unique_hostname(self, db_session, test_user):
        """Test hostname uniqueness constraint."""
        app1 = App(
            id="app1",
            catalog_id="nginx",
            name="App 1",
            hostname="unique-host",
            status="running",
            lxc_id=100,
            node="node1",
            owner_id=test_user.id
        )
        db_session.add(app1)
        db_session.commit()

        app2 = App(
            id="app2",
            catalog_id="nginx",
            name="App 2",
            hostname="unique-host",  # Duplicate
            status="running",
            lxc_id=101,
            node="node1",
            owner_id=test_user.id
        )
        db_session.add(app2)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_app_unique_lxc_id(self, db_session, test_user):
        """Test lxc_id uniqueness constraint."""
        app1 = App(
            id="app1",
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

        app2 = App(
            id="app2",
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

    def test_app_without_owner(self, db_session):
        """Test creating app without owner (nullable for migration)."""
        app = App(
            id="orphan-app",
            catalog_id="nginx",
            name="Orphan",
            hostname="orphan",
            status="running",
            lxc_id=100,
            node="node1",
            owner_id=None
        )
        db_session.add(app)
        db_session.commit()

        assert app.owner_id is None

    def test_app_user_relationship(self, db_session, test_user):
        """Test app-user relationship."""
        app = App(
            id="related-app",
            catalog_id="nginx",
            name="Related",
            hostname="related",
            status="running",
            lxc_id=100,
            node="node1",
            owner_id=test_user.id
        )
        db_session.add(app)
        db_session.commit()
        db_session.refresh(app)

        # Test relationship
        assert app.owner is not None
        assert app.owner.username == "testuser"
        assert app in test_user.apps

    def test_app_cascade_delete_logs(self, db_session, test_user):
        """Test cascade delete of deployment logs."""
        app = App(
            id="cascade-app",
            catalog_id="nginx",
            name="Cascade",
            hostname="cascade",
            status="running",
            lxc_id=100,
            node="node1",
            owner_id=test_user.id
        )
        db_session.add(app)
        db_session.commit()

        # Add deployment log
        log = DeploymentLog(
            app_id=app.id,
            level="info",
            message="Test log"
        )
        db_session.add(log)
        db_session.commit()

        # Delete app
        db_session.delete(app)
        db_session.commit()

        # Log should be deleted
        logs = db_session.query(DeploymentLog).filter(
            DeploymentLog.app_id == "cascade-app"
        ).all()
        assert len(logs) == 0

    def test_app_json_fields_default(self, db_session, test_user):
        """Test JSON fields default to empty dict/list."""
        app = App(
            id="defaults-app",
            catalog_id="nginx",
            name="Defaults",
            hostname="defaults",
            status="running",
            lxc_id=100,
            node="node1",
            owner_id=test_user.id
        )
        db_session.add(app)
        db_session.commit()
        db_session.refresh(app)

        assert app.config == {}
        assert app.ports == {}
        assert app.volumes == []
        assert app.environment == {}

    def test_app_updated_at_auto_update(self, db_session, test_user):
        """Test updated_at auto-updates on modification."""
        app = App(
            id="update-app",
            catalog_id="nginx",
            name="Update",
            hostname="update",
            status="running",
            lxc_id=100,
            node="node1",
            owner_id=test_user.id
        )
        db_session.add(app)
        db_session.commit()

        original_updated = app.updated_at

        # Update app
        import time
        time.sleep(0.1)  # Ensure time difference
        app.status = "stopped"
        db_session.commit()
        db_session.refresh(app)

        assert app.updated_at > original_updated

    def test_app_representation(self, db_session, test_user):
        """Test app string representation."""
        app = App(
            id="repr-app",
            catalog_id="nginx",
            name="Repr",
            hostname="repr",
            status="running",
            lxc_id=100,
            node="node1",
            owner_id=test_user.id
        )
        db_session.add(app)
        db_session.commit()

        repr_str = repr(app)
        assert "App" in repr_str
        assert "repr-app" in repr_str
        assert "Repr" in repr_str
        assert "running" in repr_str


class TestDeploymentLogModel:
    """Test suite for DeploymentLog model."""

    def test_create_deployment_log(self, db_session, test_user):
        """Test creating a deployment log."""
        app = App(
            id="log-app",
            catalog_id="nginx",
            name="Log App",
            hostname="log-app",
            status="deploying",
            lxc_id=100,
            node="node1",
            owner_id=test_user.id
        )
        db_session.add(app)
        db_session.commit()

        log = DeploymentLog(
            app_id=app.id,
            level="info",
            message="Deployment started",
            step="initialization"
        )
        db_session.add(log)
        db_session.commit()

        assert log.id is not None
        assert log.app_id == "log-app"
        assert log.level == "info"
        assert log.message == "Deployment started"
        assert log.step == "initialization"
        assert log.timestamp is not None

    def test_deployment_log_levels(self, db_session, test_user):
        """Test different log levels."""
        app = App(
            id="levels-app",
            catalog_id="nginx",
            name="Levels",
            hostname="levels",
            status="running",
            lxc_id=100,
            node="node1",
            owner_id=test_user.id
        )
        db_session.add(app)
        db_session.commit()

        for level in ["info", "warning", "error"]:
            log = DeploymentLog(
                app_id=app.id,
                level=level,
                message=f"Test {level} message"
            )
            db_session.add(log)

        db_session.commit()

        logs = db_session.query(DeploymentLog).filter(
            DeploymentLog.app_id == "levels-app"
        ).all()

        assert len(logs) == 3
        levels = [log.level for log in logs]
        assert "info" in levels
        assert "warning" in levels
        assert "error" in levels

    def test_deployment_log_app_relationship(self, db_session, test_user):
        """Test deployment log - app relationship."""
        app = App(
            id="rel-app",
            catalog_id="nginx",
            name="Relationship",
            hostname="rel",
            status="running",
            lxc_id=100,
            node="node1",
            owner_id=test_user.id
        )
        db_session.add(app)
        db_session.commit()

        log = DeploymentLog(
            app_id=app.id,
            level="info",
            message="Test"
        )
        db_session.add(log)
        db_session.commit()
        db_session.refresh(log)

        assert log.app is not None
        assert log.app.id == "rel-app"
        assert log in app.deployment_logs

    def test_deployment_log_representation(self, db_session, test_user):
        """Test deployment log string representation."""
        app = App(
            id="repr-log-app",
            catalog_id="nginx",
            name="Repr",
            hostname="repr-log",
            status="running",
            lxc_id=100,
            node="node1",
            owner_id=test_user.id
        )
        db_session.add(app)
        db_session.commit()

        log = DeploymentLog(
            app_id=app.id,
            level="info",
            message="Test"
        )
        db_session.add(log)
        db_session.commit()

        repr_str = repr(log)
        assert "DeploymentLog" in repr_str
        assert "repr-log-app" in repr_str
        assert "info" in repr_str


class TestAuditLogModel:
    """Test suite for AuditLog model."""

    def test_create_audit_log(self, db_session, test_user):
        """Test creating an audit log."""
        log = AuditLog(
            user_id=test_user.id,
            username=test_user.username,
            action="deploy_app",
            resource_type="app",
            resource_id="test-app",
            details={"catalog_id": "nginx"},
            ip_address="127.0.0.1"
        )
        db_session.add(log)
        db_session.commit()

        assert log.id is not None
        assert log.user_id == test_user.id
        assert log.username == "testuser"
        assert log.action == "deploy_app"
        assert log.resource_type == "app"
        assert log.resource_id == "test-app"
        assert log.details == {"catalog_id": "nginx"}
        assert log.ip_address == "127.0.0.1"
        assert log.timestamp is not None

    def test_audit_log_without_user(self, db_session):
        """Test system audit log (no user)."""
        log = AuditLog(
            user_id=None,
            username="system",
            action="system_startup",
            resource_type="system",
            details={"version": "1.0"}
        )
        db_session.add(log)
        db_session.commit()

        assert log.user_id is None
        assert log.username == "system"

    def test_audit_log_actions(self, db_session, test_user):
        """Test different audit actions."""
        actions = [
            "login",
            "logout",
            "deploy_app",
            "delete_app",
            "start_app",
            "stop_app"
        ]

        for action in actions:
            log = AuditLog(
                user_id=test_user.id,
                username=test_user.username,
                action=action,
                resource_type="app"
            )
            db_session.add(log)

        db_session.commit()

        logs = db_session.query(AuditLog).filter(
            AuditLog.user_id == test_user.id
        ).all()

        assert len(logs) == len(actions)
        logged_actions = [log.action for log in logs]
        for action in actions:
            assert action in logged_actions

    def test_audit_log_representation(self, db_session, test_user):
        """Test audit log string representation."""
        log = AuditLog(
            user_id=test_user.id,
            username=test_user.username,
            action="test_action"
        )
        db_session.add(log)
        db_session.commit()

        repr_str = repr(log)
        assert "AuditLog" in repr_str
        assert "testuser" in repr_str
        assert "test_action" in repr_str


class TestDatabaseConstraints:
    """Test database constraints and integrity."""

    def test_cascade_delete_user_apps(self, db_session, test_user):
        """Test cascade delete of user apps."""
        # Create apps for user
        for i in range(3):
            app = App(
                id=f"cascade-{i}",
                catalog_id="nginx",
                name=f"App {i}",
                hostname=f"cascade-{i}",
                status="running",
                lxc_id=100 + i,
                node="node1",
                owner_id=test_user.id
            )
            db_session.add(app)
        db_session.commit()

        # Verify apps exist
        apps = db_session.query(App).filter(App.owner_id == test_user.id).all()
        assert len(apps) == 3

        # Delete user
        db_session.delete(test_user)
        db_session.commit()

        # Apps should be deleted
        apps = db_session.query(App).filter(App.owner_id == test_user.id).all()
        assert len(apps) == 0

    def test_app_requires_catalog_id(self, db_session, test_user):
        """Test catalog_id is required."""
        app = App(
            id="no-catalog",
            catalog_id=None,  # Required field
            name="No Catalog",
            hostname="no-catalog",
            status="running",
            lxc_id=100,
            node="node1",
            owner_id=test_user.id
        )
        db_session.add(app)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_app_requires_lxc_id(self, db_session, test_user):
        """Test lxc_id is required."""
        app = App(
            id="no-lxc",
            catalog_id="nginx",
            name="No LXC",
            hostname="no-lxc",
            status="running",
            lxc_id=None,  # Required field
            node="node1",
            owner_id=test_user.id
        )
        db_session.add(app)

        with pytest.raises(IntegrityError):
            db_session.commit()
