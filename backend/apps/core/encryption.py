"""
Encryption utilities for sensitive data like passwords.

Uses Fernet (symmetric encryption) from the cryptography library
with the Django SECRET_KEY as the encryption key.
"""

import base64
import os
from cryptography.fernet import Fernet
from django.conf import settings


class EncryptionManager:
    """
    Manages encryption/decryption of sensitive data.
    Uses Fernet symmetric encryption with Django's SECRET_KEY.
    """

    @staticmethod
    def _get_cipher_key():
        """
        Get or generate the Fernet cipher key from Django's SECRET_KEY.

        The key must be 32 bytes encoded in base64.
        We use the first 32 bytes of SHA256 hash of SECRET_KEY.
        """
        secret_key = settings.SECRET_KEY.encode()
        # Use first 32 bytes for Fernet key (256 bits)
        import hashlib
        hash_digest = hashlib.sha256(secret_key).digest()[:32]
        cipher_key = base64.urlsafe_b64encode(hash_digest)
        return cipher_key

    @classmethod
    def encrypt(cls, plaintext: str) -> str:
        """
        Encrypt a plaintext string.

        Args:
            plaintext: String to encrypt

        Returns:
            Encrypted string (base64-encoded token)
        """
        if not plaintext:
            return plaintext

        cipher_key = cls._get_cipher_key()
        cipher = Fernet(cipher_key)
        encrypted = cipher.encrypt(plaintext.encode())
        return encrypted.decode('utf-8')

    @classmethod
    def decrypt(cls, ciphertext: str) -> str:
        """
        Decrypt a ciphertext string.

        Args:
            ciphertext: Encrypted string to decrypt

        Returns:
            Decrypted plaintext string
        """
        if not ciphertext:
            return ciphertext

        try:
            cipher_key = cls._get_cipher_key()
            cipher = Fernet(cipher_key)
            decrypted = cipher.decrypt(ciphertext.encode())
            return decrypted.decode('utf-8')
        except Exception as e:
            # If decryption fails, it might be plaintext (for migration compatibility)
            # Log this but don't fail - it will be encrypted on next save
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to decrypt value, assuming plaintext: {str(e)}")
            return ciphertext
