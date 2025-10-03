"""
Custom Exceptions for Proximity

This module defines application-specific exceptions to provide
clear, structured error handling throughout the application.

All custom exceptions inherit from a base ProximityError class
to allow for centralized exception handling.

Author: Proximity Team
Date: October 2025
"""


class ProximityError(Exception):
    """Base exception for all Proximity-specific errors"""
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


# Application Management Exceptions

class AppError(ProximityError):
    """Base class for application-related errors"""
    pass


class AppNotFoundError(AppError):
    """Raised when an application cannot be found"""
    pass


class AppAlreadyExistsError(AppError):
    """Raised when attempting to create an app that already exists"""
    pass


class AppDeploymentError(AppError):
    """Raised when application deployment fails"""
    pass


class AppDeletionError(AppError):
    """Raised when application deletion fails"""
    pass


class AppOperationError(AppError):
    """Raised when application operations (start/stop/restart) fail"""
    pass


class AppStateError(AppError):
    """Raised when app is in invalid state for requested operation"""
    pass


# Infrastructure Exceptions

class InfrastructureError(ProximityError):
    """Base class for infrastructure-related errors"""
    pass


class NetworkApplianceError(InfrastructureError):
    """Raised when network appliance operations fail"""
    pass


class BridgeConfigurationError(InfrastructureError):
    """Raised when bridge configuration fails"""
    pass


class ProxmoxConnectionError(InfrastructureError):
    """Raised when Proxmox connection fails"""
    pass


class LXCCreationError(InfrastructureError):
    """Raised when LXC container creation fails"""
    pass


class LXCNotFoundError(InfrastructureError):
    """Raised when LXC container cannot be found"""
    pass


# Authentication & Authorization Exceptions

class AuthenticationError(ProximityError):
    """Base class for authentication errors"""
    pass


class InvalidCredentialsError(AuthenticationError):
    """Raised when credentials are invalid"""
    pass


class TokenExpiredError(AuthenticationError):
    """Raised when JWT token has expired"""
    pass


class TokenInvalidError(AuthenticationError):
    """Raised when JWT token is invalid or malformed"""
    pass


class PermissionDeniedError(AuthenticationError):
    """Raised when user lacks required permissions"""
    pass


# Database Exceptions

class DatabaseError(ProximityError):
    """Base class for database errors"""
    pass


class RecordNotFoundError(DatabaseError):
    """Raised when database record cannot be found"""
    pass


class DuplicateRecordError(DatabaseError):
    """Raised when attempting to create duplicate record"""
    pass


class DatabaseMigrationError(DatabaseError):
    """Raised when database migration fails"""
    pass


# Configuration Exceptions

class ConfigurationError(ProximityError):
    """Base class for configuration errors"""
    pass


class InvalidConfigurationError(ConfigurationError):
    """Raised when configuration is invalid"""
    pass


class MissingConfigurationError(ConfigurationError):
    """Raised when required configuration is missing"""
    pass


class EncryptionError(ConfigurationError):
    """Raised when encryption/decryption operations fail"""
    pass


# Catalog Exceptions

class CatalogError(ProximityError):
    """Base class for catalog errors"""
    pass


class CatalogItemNotFoundError(CatalogError):
    """Raised when catalog item cannot be found"""
    pass


class CatalogLoadError(CatalogError):
    """Raised when catalog cannot be loaded"""
    pass


# Command Execution Exceptions

class CommandExecutionError(ProximityError):
    """Base class for command execution errors"""
    pass


class UnsafeCommandError(CommandExecutionError):
    """Raised when attempting to execute unsafe command"""
    pass


class CommandTimeoutError(CommandExecutionError):
    """Raised when command execution times out"""
    pass


# Network Exceptions

class NetworkError(ProximityError):
    """Base class for network-related errors"""
    pass


class IPAllocationError(NetworkError):
    """Raised when IP address allocation fails"""
    pass


class DNSConfigurationError(NetworkError):
    """Raised when DNS configuration fails"""
    pass


class ReverseProxyError(NetworkError):
    """Raised when reverse proxy configuration fails"""
    pass


# Validation Exceptions

class ValidationError(ProximityError):
    """Base class for validation errors"""
    pass


class InvalidInputError(ValidationError):
    """Raised when user input is invalid"""
    pass


class ResourceLimitError(ValidationError):
    """Raised when resource limits are exceeded"""
    pass


# Backup & Restore Exceptions

class BackupError(ProximityError):
    """Base class for backup/restore errors"""
    pass


class BackupCreationError(BackupError):
    """Raised when backup creation fails"""
    pass


class BackupNotFoundError(BackupError):
    """Raised when backup cannot be found"""
    pass


class RestoreError(BackupError):
    """Raised when restore operation fails"""
    pass
