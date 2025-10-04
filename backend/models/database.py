"""
Database models for Proximity using SQLAlchemy.

This module defines the database schema for:
- Users (authentication)
- Apps (deployed applications)
- Deployment logs (audit trail)
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from datetime import datetime
from contextlib import contextmanager
import bcrypt
import os

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./proximity.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=False  # Set to True for SQL debugging
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# Dependency for FastAPI
def get_db():
    """Database session dependency for FastAPI endpoints"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database - create all tables"""
    Base.metadata.create_all(bind=engine)


# Models

class User(Base):
    """User model for authentication and authorization"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=True, index=True)  # Made optional
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="user")  # 'admin' or 'user'
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    apps = relationship("App", back_populates="owner", cascade="all, delete-orphan")

    def verify_password(self, password: str) -> bool:
        """Verify password against stored hash"""
        return bcrypt.checkpw(
            password.encode('utf-8'),
            self.hashed_password.encode('utf-8')
        )

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        return bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

    def __repr__(self):
        return f"<User(username='{self.username}', role='{self.role}')>"


class App(Base):
    """Deployed application model"""
    __tablename__ = "apps"

    id = Column(String(255), primary_key=True, index=True)
    catalog_id = Column(String(100), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    hostname = Column(String(255), nullable=False, unique=True, index=True)
    status = Column(String(50), nullable=False, index=True)
    url = Column(String(512))
    lxc_id = Column(Integer, nullable=False, unique=True, index=True)
    node = Column(String(100), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # JSON fields
    config = Column(JSON, default=dict)
    ports = Column(JSON, default=dict)
    volumes = Column(JSON, default=list)
    environment = Column(JSON, default=dict)

    # Foreign key to user
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Nullable for migration

    # Relationships
    owner = relationship("User", back_populates="apps")
    deployment_logs = relationship("DeploymentLog", back_populates="app", cascade="all, delete-orphan")
    backups = relationship("Backup", back_populates="app", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<App(id='{self.id}', name='{self.name}', status='{self.status}')>"


class DeploymentLog(Base):
    """Deployment event log for audit trail"""
    __tablename__ = "deployment_logs"

    id = Column(Integer, primary_key=True, index=True)
    app_id = Column(String(255), ForeignKey("apps.id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    level = Column(String(20), nullable=False)  # 'info', 'warning', 'error'
    message = Column(String(1000), nullable=False)
    step = Column(String(255))

    # Relationships
    app = relationship("App", back_populates="deployment_logs")

    def __repr__(self):
        return f"<DeploymentLog(app_id='{self.app_id}', level='{self.level}', timestamp='{self.timestamp}')>"


class Backup(Base):
    """Backup model for application backups"""
    __tablename__ = "backups"

    id = Column(Integer, primary_key=True, index=True)
    app_id = Column(String(255), ForeignKey("apps.id"), nullable=False, index=True)
    filename = Column(String(500), nullable=False)
    storage_name = Column(String(100), nullable=False, default="local")  # Proxmox storage name
    size_bytes = Column(Integer, nullable=True)  # Size in bytes, nullable until backup completes
    backup_type = Column(String(50), nullable=False, default="vzdump")  # 'vzdump', 'snapshot', etc.
    status = Column(String(50), nullable=False, index=True)  # 'creating', 'available', 'failed', 'restoring'
    error_message = Column(String(1000), nullable=True)  # Error details if failed
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)  # When backup finished

    # Relationships
    app = relationship("App", back_populates="backups")

    def __repr__(self):
        return f"<Backup(id={self.id}, app_id='{self.app_id}', filename='{self.filename}', status='{self.status}')>"


class AuditLog(Base):
    """Audit log for tracking user actions"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Nullable for system events
    username = Column(String(50), index=True)
    action = Column(String(100), nullable=False, index=True)  # e.g., 'deploy_app', 'delete_app', 'login'
    resource_type = Column(String(50))  # e.g., 'app', 'user', 'system'
    resource_id = Column(String(255))
    details = Column(JSON)  # Additional context
    ip_address = Column(String(50))
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<AuditLog(username='{self.username}', action='{self.action}', timestamp='{self.timestamp}')>"


class Setting(Base):
    """System settings with encryption support"""
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(String(1000))  # Encrypted if sensitive
    is_encrypted = Column(Boolean, default=False)
    category = Column(String(50), index=True)  # 'proxmox', 'network', 'system', 'resources'
    description = Column(String(500))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(Integer, ForeignKey("users.id"))

    def __repr__(self):
        return f"<Setting(key='{self.key}', category='{self.category}', encrypted={self.is_encrypted})>"
