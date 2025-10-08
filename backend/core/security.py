"""
Utility functions for password generation and security
"""

import secrets
import string
import base64
from cryptography.fernet import Fernet
from core.config import settings


def generate_secure_password(length: int = 16, include_special: bool = True) -> str:
    """
    Generate a cryptographically secure random password.
    
    Args:
        length: Length of the password (default: 16)
        include_special: Include special characters (default: True)
    
    Returns:
        A secure random password string
    
    Example:
        >>> pwd = generate_secure_password(16)
        >>> len(pwd)
        16
    """
    # Define character sets
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    special = "!@#$%^&*()-_=+[]{}|;:,.<>?" if include_special else ""
    
    # Combine all character sets
    all_characters = lowercase + uppercase + digits + special
    
    # Ensure at least one character from each set
    password = [
        secrets.choice(lowercase),
        secrets.choice(uppercase),
        secrets.choice(digits),
    ]
    
    if include_special:
        password.append(secrets.choice(special))
    
    # Fill the rest with random characters
    remaining_length = length - len(password)
    password.extend(secrets.choice(all_characters) for _ in range(remaining_length))
    
    # Shuffle to avoid predictable patterns
    secrets.SystemRandom().shuffle(password)
    
    return ''.join(password)


def generate_lxc_password(length: int = 16) -> str:
    """
    Generate a password suitable for LXC containers.
    
    Uses only alphanumeric and safe special characters to avoid
    issues with shell escaping and system commands.
    
    Args:
        length: Length of the password (default: 16)
    
    Returns:
        A secure random password safe for LXC use
    """
    # Use a more limited character set for LXC to avoid shell escaping issues
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    safe_special = "!@#$%^&*-_=+"  # Safe special chars that don't need escaping
    
    all_characters = lowercase + uppercase + digits + safe_special
    
    # Ensure at least one of each type
    password = [
        secrets.choice(lowercase),
        secrets.choice(uppercase),
        secrets.choice(digits),
        secrets.choice(safe_special),
    ]
    
    # Fill the rest
    remaining_length = length - len(password)
    password.extend(secrets.choice(all_characters) for _ in range(remaining_length))
    
    # Shuffle
    secrets.SystemRandom().shuffle(password)
    
    return ''.join(password)


def get_encryption_key() -> bytes:
    """
    Get or generate encryption key for password storage.
    
    The key is derived from the JWT_SECRET_KEY in settings to ensure
    consistency across application restarts.
    
    Returns:
        Fernet encryption key
    """
    # Use first 32 bytes of JWT_SECRET_KEY for Fernet (needs 32 url-safe base64-encoded bytes)
    key_material = settings.JWT_SECRET_KEY.encode()[:32].ljust(32, b'0')
    return base64.urlsafe_b64encode(key_material)


def encrypt_password(password: str) -> str:
    """
    Encrypt a password for storage in the database.
    
    Args:
        password: Plain text password to encrypt
    
    Returns:
        Encrypted password as base64 string
    """
    key = get_encryption_key()
    f = Fernet(key)
    encrypted = f.encrypt(password.encode())
    return encrypted.decode()


def decrypt_password(encrypted_password: str) -> str:
    """
    Decrypt a password from database storage.
    
    Args:
        encrypted_password: Encrypted password from database
    
    Returns:
        Plain text password
    """
    key = get_encryption_key()
    f = Fernet(key)
    decrypted = f.decrypt(encrypted_password.encode())
    return decrypted.decode()
