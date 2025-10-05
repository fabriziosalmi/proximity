"""
Authentication Service for Proximity

Handles JWT token generation, verification, and user authentication.
"""

from datetime import datetime, timedelta, UTC
from jose import JWTError, jwt
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from models.database import User, AuditLog
from models.schemas import TokenData
import os
import logging

logger = logging.getLogger(__name__)

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "INSECURE_DEV_KEY_CHANGE_IN_PRODUCTION")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# Warn if using default secret in production
if SECRET_KEY == "INSECURE_DEV_KEY_CHANGE_IN_PRODUCTION" and not os.getenv("DEBUG", "false").lower() == "true":
    logger.warning("⚠️  SECURITY WARNING: Using default JWT secret key! Set JWT_SECRET_KEY in .env")


class AuthService:
    """Authentication and authorization service"""

    @staticmethod
    def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
        """
        Create JWT access token

        Args:
            data: Payload to encode (should include 'sub', 'role', 'user_id')
            expires_delta: Custom expiration time (optional)

        Returns:
            Encoded JWT token
        """
        to_encode = data.copy()
        expire = datetime.now(UTC) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(UTC)
        })

        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def verify_token(token: str) -> TokenData:
        """
        Verify and decode JWT token

        Args:
            token: JWT token string

        Returns:
            TokenData with username, role, user_id

        Raises:
            HTTPException: If token is invalid or expired
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            role: str = payload.get("role")
            user_id: int = payload.get("user_id")

            if username is None or role is None or user_id is None:
                raise credentials_exception

            return TokenData(username=username, role=role, user_id=user_id)

        except JWTError as e:
            logger.warning(f"JWT verification failed: {e}")
            raise credentials_exception

    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> User:
        """
        Authenticate user with username and password

        Args:
            db: Database session
            username: Username
            password: Plain text password

        Returns:
            User object if authentication successful

        Raises:
            HTTPException: If authentication fails
        """
        user = db.query(User).filter(User.username == username).first()

        if not user:
            logger.warning(f"Authentication failed: User '{username}' not found")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            logger.warning(f"Authentication failed: User '{username}' is inactive")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.verify_password(password):
            logger.warning(f"Authentication failed: Invalid password for user '{username}'")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        logger.info(f"User '{username}' authenticated successfully")
        return user

    @staticmethod
    def create_user(db: Session, username: str, email: str | None, password: str, role: str = "user") -> User:
        """
        Create new user

        Args:
            db: Database session
            username: Username
            email: Email address (optional)
            password: Plain text password (will be hashed)
            role: User role ('user' or 'admin')

        Returns:
            Created User object

        Raises:
            HTTPException: If user already exists
        """
        # Check if user exists
        if db.query(User).filter(User.username == username).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Username '{username}' already exists"
            )

        # Only check email if provided
        if email and db.query(User).filter(User.email == email).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Email '{email}' already registered"
            )

        # Create user
        user = User(
            username=username,
            email=email,
            hashed_password=User.hash_password(password),
            role=role
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        logger.info(f"Created new user: {username} (role: {role})")
        return user

    @staticmethod
    def change_password(db: Session, user: User, old_password: str, new_password: str) -> bool:
        """
        Change user password

        Args:
            db: Database session
            user: User object
            old_password: Current password
            new_password: New password

        Returns:
            True if successful

        Raises:
            HTTPException: If old password is incorrect
        """
        if not user.verify_password(old_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Current password is incorrect"
            )

        user.hashed_password = User.hash_password(new_password)
        db.commit()

        logger.info(f"Password changed for user: {user.username}")
        return True

    @staticmethod
    def log_audit(db: Session, user_id: int, username: str, action: str,
                  resource_type: str = None, resource_id: str = None,
                  details: dict = None, ip_address: str = None):
        """
        Log user action for audit trail

        Args:
            db: Database session
            user_id: User ID
            username: Username
            action: Action performed
            resource_type: Type of resource affected
            resource_id: ID of resource affected
            details: Additional details (JSON)
            ip_address: IP address of request
        """
        audit_log = AuditLog(
            user_id=user_id,
            username=username,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address
        )

        db.add(audit_log)
        db.commit()

        logger.info(f"Audit: {username} performed {action} on {resource_type}:{resource_id}")
