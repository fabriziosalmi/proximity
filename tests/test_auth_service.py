"""
Unit tests for AuthService.
"""

import pytest
from datetime import datetime, timedelta
from jose import jwt
from services.auth_service import AuthService
from models.database import User, AuditLog


class TestAuthService:
    """Test suite for AuthService."""

    def test_create_access_token(self):
        """Test JWT token creation."""
        data = {
            "sub": "testuser",
            "role": "user",
            "user_id": 1
        }

        token = AuthService.create_access_token(data)
        assert token is not None
        assert isinstance(token, str)

    def test_verify_token_success(self):
        """Test successful token verification."""
        data = {
            "sub": "testuser",
            "role": "user",
            "user_id": 1
        }

        token = AuthService.create_access_token(data)
        token_data = AuthService.verify_token(token)

        assert token_data.username == "testuser"
        assert token_data.role == "user"
        assert token_data.user_id == 1

    def test_verify_token_expired(self):
        """Test token verification with expired token."""
        data = {
            "sub": "testuser",
            "role": "user",
            "user_id": 1
        }

        # Create token with negative expiration
        token = AuthService.create_access_token(
            data,
            expires_delta=timedelta(seconds=-1)
        )

        with pytest.raises(Exception):  # Should raise HTTPException
            AuthService.verify_token(token)

    def test_verify_token_invalid(self):
        """Test token verification with invalid token."""
        with pytest.raises(Exception):
            AuthService.verify_token("invalid.token.here")

    def test_authenticate_user_success(self, db_session, test_user):
        """Test successful user authentication."""
        user = AuthService.authenticate_user(
            db=db_session,
            username="testuser",
            password="testpass123"
        )

        assert user is not None
        assert user.username == "testuser"

    def test_authenticate_user_wrong_password(self, db_session, test_user):
        """Test authentication with wrong password."""
        with pytest.raises(Exception):
            AuthService.authenticate_user(
                db=db_session,
                username="testuser",
                password="wrongpassword"
            )

    def test_authenticate_user_not_found(self, db_session):
        """Test authentication with non-existent user."""
        with pytest.raises(Exception):
            AuthService.authenticate_user(
                db=db_session,
                username="nonexistent",
                password="password"
            )

    def test_authenticate_inactive_user(self, db_session):
        """Test authentication with inactive user."""
        # Create inactive user
        inactive_user = User(
            username="inactive",
            hashed_password=User.hash_password("password"),
            is_active=False
        )
        db_session.add(inactive_user)
        db_session.commit()

        with pytest.raises(Exception):
            AuthService.authenticate_user(
                db=db_session,
                username="inactive",
                password="password"
            )

    def test_create_user_success(self, db_session):
        """Test successful user creation."""
        user = AuthService.create_user(
            db=db_session,
            username="newuser",
            email="new@example.com",
            password="password123",
            role="user"
        )

        assert user.username == "newuser"
        assert user.email == "new@example.com"
        assert user.role == "user"
        assert user.is_active is True

    def test_create_user_duplicate_username(self, db_session, test_user):
        """Test user creation with duplicate username."""
        with pytest.raises(Exception):
            AuthService.create_user(
                db=db_session,
                username="testuser",  # Already exists
                email="another@example.com",
                password="password123"
            )

    def test_create_user_duplicate_email(self, db_session, test_user):
        """Test user creation with duplicate email."""
        with pytest.raises(Exception):
            AuthService.create_user(
                db=db_session,
                username="anotheruser",
                email="test@example.com",  # Already exists
                password="password123"
            )

    def test_create_user_without_email(self, db_session):
        """Test user creation without email (should succeed)."""
        user = AuthService.create_user(
            db=db_session,
            username="noemail",
            email=None,
            password="password123"
        )

        assert user.username == "noemail"
        assert user.email is None

    def test_change_password_success(self, db_session, test_user):
        """Test successful password change."""
        result = AuthService.change_password(
            db=db_session,
            user=test_user,
            old_password="testpass123",
            new_password="newpassword123"
        )

        assert result is True

        # Verify new password works
        user = AuthService.authenticate_user(
            db=db_session,
            username="testuser",
            password="newpassword123"
        )
        assert user is not None

    def test_change_password_wrong_old_password(self, db_session, test_user):
        """Test password change with wrong old password."""
        with pytest.raises(Exception):
            AuthService.change_password(
                db=db_session,
                user=test_user,
                old_password="wrongpassword",
                new_password="newpassword123"
            )

    def test_log_audit(self, db_session, test_user):
        """Test audit logging."""
        AuthService.log_audit(
            db=db_session,
            user_id=test_user.id,
            username=test_user.username,
            action="test_action",
            resource_type="test_resource",
            resource_id="123",
            details={"key": "value"},
            ip_address="127.0.0.1"
        )

        # Verify audit log was created
        audit = db_session.query(AuditLog).filter(
            AuditLog.user_id == test_user.id,
            AuditLog.action == "test_action"
        ).first()

        assert audit is not None
        assert audit.username == test_user.username
        assert audit.resource_type == "test_resource"
        assert audit.ip_address == "127.0.0.1"


class TestPasswordHashing:
    """Test password hashing functionality."""

    def test_hash_password(self):
        """Test password hashing."""
        hashed = User.hash_password("testpassword")
        assert hashed is not None
        assert hashed != "testpassword"

    def test_verify_password_correct(self, test_user):
        """Test password verification with correct password."""
        assert test_user.verify_password("testpass123") is True

    def test_verify_password_incorrect(self, test_user):
        """Test password verification with incorrect password."""
        assert test_user.verify_password("wrongpassword") is False

    def test_password_hash_unique(self):
        """Test that same password produces different hashes."""
        hash1 = User.hash_password("samepassword")
        hash2 = User.hash_password("samepassword")

        # Hashes should be different due to random salt
        assert hash1 != hash2


class TestTokenDataExtraction:
    """Test token data extraction."""

    def test_token_contains_all_fields(self):
        """Test that token contains all required fields."""
        data = {
            "sub": "testuser",
            "role": "admin",
            "user_id": 1
        }

        token = AuthService.create_access_token(data)
        token_data = AuthService.verify_token(token)

        assert token_data.username == "testuser"
        assert token_data.role == "admin"
        assert token_data.user_id == 1

    def test_token_missing_fields(self):
        """Test token verification with missing fields."""
        # Create token manually with missing fields
        from core.config import settings

        data = {
            "sub": "testuser"
            # Missing role and user_id
        }

        token = jwt.encode(data, settings.JWT_SECRET_KEY, algorithm="HS256")

        with pytest.raises(Exception):
            AuthService.verify_token(token)
