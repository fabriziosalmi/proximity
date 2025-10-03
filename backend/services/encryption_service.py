"""
Encryption Service for Proximity

Handles encryption/decryption of sensitive data (Proxmox credentials, etc.)
Uses Fernet (symmetric encryption) from cryptography library.
"""

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import base64
import os
import logging

logger = logging.getLogger(__name__)


class EncryptionService:
    """Service for encrypting/decrypting sensitive configuration data"""

    def __init__(self):
        """Initialize encryption service with key derivation"""
        # Get encryption key from environment or generate one
        self._encryption_key = self._get_or_create_key()
        self._fernet = Fernet(self._encryption_key)

    def _get_or_create_key(self) -> bytes:
        """
        Get encryption key from environment or generate a new one.

        In production, this should be:
        1. Generated once during installation
        2. Stored securely (environment variable, secrets manager)
        3. NEVER changed (would make existing encrypted data unreadable)

        Returns:
            32-byte encryption key
        """
        key_str = os.getenv("ENCRYPTION_KEY")

        if key_str:
            # Use existing key from environment
            return base64.urlsafe_b64decode(key_str)

        # Generate new key (development only)
        logger.warning("⚠️  No ENCRYPTION_KEY found - generating new key")
        logger.warning("⚠️  This will make previously encrypted data unreadable!")

        # Derive key from JWT secret (ensures consistency)
        jwt_secret = os.getenv("JWT_SECRET_KEY", "INSECURE_DEFAULT")
        salt = b"proximity_encryption_salt_v1"  # Fixed salt for consistency

        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(jwt_secret.encode()))

        logger.info("✓ Generated encryption key from JWT secret")
        logger.info(f"  Add to .env: ENCRYPTION_KEY={key.decode()}")

        return key

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a string value.

        Args:
            plaintext: String to encrypt (e.g., password)

        Returns:
            Base64-encoded encrypted string
        """
        if not plaintext:
            return ""

        try:
            encrypted_bytes = self._fernet.encrypt(plaintext.encode())
            return encrypted_bytes.decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise ValueError(f"Failed to encrypt value: {e}")

    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt an encrypted string.

        Args:
            ciphertext: Base64-encoded encrypted string

        Returns:
            Decrypted plaintext string
        """
        if not ciphertext:
            return ""

        try:
            decrypted_bytes = self._fernet.decrypt(ciphertext.encode())
            return decrypted_bytes.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError(f"Failed to decrypt value (key may have changed): {e}")

    def encrypt_dict(self, data: dict, keys_to_encrypt: list) -> dict:
        """
        Encrypt specific keys in a dictionary.

        Args:
            data: Dictionary with sensitive data
            keys_to_encrypt: List of keys to encrypt

        Returns:
            Dictionary with encrypted values
        """
        encrypted_data = data.copy()

        for key in keys_to_encrypt:
            if key in encrypted_data and encrypted_data[key]:
                encrypted_data[key] = self.encrypt(str(encrypted_data[key]))

        return encrypted_data

    def decrypt_dict(self, data: dict, keys_to_decrypt: list) -> dict:
        """
        Decrypt specific keys in a dictionary.

        Args:
            data: Dictionary with encrypted data
            keys_to_decrypt: List of keys to decrypt

        Returns:
            Dictionary with decrypted values
        """
        decrypted_data = data.copy()

        for key in keys_to_decrypt:
            if key in decrypted_data and decrypted_data[key]:
                try:
                    decrypted_data[key] = self.decrypt(decrypted_data[key])
                except ValueError:
                    # If decryption fails, keep encrypted value and log warning
                    logger.warning(f"Could not decrypt {key} - encryption key may have changed")

        return decrypted_data


# Singleton instance
_encryption_service = None

def get_encryption_service() -> EncryptionService:
    """Get or create encryption service singleton"""
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = EncryptionService()
    return _encryption_service
