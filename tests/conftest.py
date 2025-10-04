"""
Pytest configuration and fixtures for Proximity tests.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from models.database import Base, User
from services.proxmox_service import ProxmoxService
from services.auth_service import AuthService


@pytest.fixture(scope="session")
def test_db_engine():
    """Create a test database engine."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(test_db_engine):
    """Create a fresh database session for each test."""
    SessionLocal = sessionmaker(bind=test_db_engine)
    session = SessionLocal()

    yield session

    session.rollback()
    session.close()
    
    # Clean all tables after each test to ensure isolation
    for table in reversed(Base.metadata.sorted_tables):
        session.execute(table.delete())
    session.commit()


@pytest.fixture
def test_user(db_session: Session):
    """Create a test user."""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=User.hash_password("testpass123"),
        role="user",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_admin(db_session: Session):
    """Create a test admin user."""
    admin = User(
        username="admin",
        email="admin@example.com",
        hashed_password=User.hash_password("adminpass123"),
        role="admin",
        is_active=True
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


@pytest.fixture
def mock_proxmox_service():
    """Create a mock ProxmoxService."""
    mock = AsyncMock(spec=ProxmoxService)

    # Mock common methods
    mock.test_connection = AsyncMock(return_value=True)
    mock.get_nodes = AsyncMock(return_value=[
        {"node": "testnode", "status": "online", "cpu": 0.1, "maxcpu": 8}
    ])
    mock.get_next_vmid = AsyncMock(return_value=100)
    mock.get_best_node = AsyncMock(return_value="testnode")
    mock.create_lxc = AsyncMock(return_value={"task_id": "UPID:test"})
    mock.start_lxc = AsyncMock(return_value="UPID:test")
    mock.stop_lxc = AsyncMock(return_value="UPID:test")
    mock.destroy_lxc = AsyncMock(return_value="UPID:test")
    mock.wait_for_task = AsyncMock(return_value=True)
    mock.setup_docker_in_alpine = AsyncMock(return_value=True)
    mock.execute_in_container = AsyncMock(return_value="OK")
    mock.get_lxc_ip = AsyncMock(return_value="10.0.0.100")
    mock.get_lxc_status = AsyncMock(return_value={
        "vmid": 100,
        "status": "running",
        "name": "test-container"
    })

    return mock


@pytest.fixture
def mock_proxy_manager():
    """Create a mock ReverseProxyManager."""
    mock = AsyncMock()
    mock.create_vhost = AsyncMock(return_value=True)
    mock.remove_vhost = AsyncMock(return_value=True)
    mock.get_status = AsyncMock(return_value={"status": "running"})
    return mock


@pytest.fixture
def sample_catalog_item():
    """Sample catalog item for testing."""
    return {
        "id": "nginx",
        "name": "Nginx",
        "description": "High-performance web server",
        "category": "web",
        "icon": "server",
        "version": "1.25",
        "resources": {
            "cpu": 1,
            "memory": 512,
            "disk": 8
        },
        "compose": {
            "version": "3.8",
            "services": {
                "nginx": {
                    "image": "nginx:alpine",
                    "ports": ["80:80"],
                    "restart": "unless-stopped"
                }
            }
        }
    }


@pytest.fixture
def sample_app_create():
    """Sample AppCreate data for testing."""
    return {
        "catalog_id": "nginx",
        "hostname": "test-nginx",
        "config": {},
        "environment": {}
    }


@pytest.fixture
async def cleanup_test_containers():
    """Cleanup fixture to remove test containers after tests."""
    test_containers = []

    def register_container(vmid: int, node: str):
        test_containers.append((vmid, node))

    yield register_container

    # Cleanup would happen here if needed
    # For unit tests, this is mocked, so no actual cleanup needed
