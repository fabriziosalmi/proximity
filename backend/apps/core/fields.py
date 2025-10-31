"""
Custom Django fields with built-in encryption.
"""

from django.db import models
from .encryption import EncryptionManager


class EncryptedTextField(models.TextField):
    """
    TextField that automatically encrypts/decrypts data.

    Usage:
        password = EncryptedTextField()

    Data is encrypted when saved to database and decrypted when retrieved.
    """

    def get_prep_value(self, value):
        """
        Encrypt the value before saving to database.
        """
        if value is None:
            return value
        return EncryptionManager.encrypt(str(value))

    def from_db_value(self, value, expression, connection):
        """
        Decrypt the value when retrieved from database.
        """
        if value is None:
            return value
        return EncryptionManager.decrypt(value)

    def to_python(self, value):
        """
        Convert value to Python type. For encrypted fields, we return as-is
        since from_db_value handles decryption.
        """
        if isinstance(value, str):
            # Only decrypt if it looks like an encrypted token (starts with 'gAAAAA')
            # which is Fernet's default format
            if value.startswith("gAAAAA"):
                return EncryptionManager.decrypt(value)
        return value


class EncryptedCharField(models.CharField):
    """
    CharField that automatically encrypts/decrypts data.

    Usage:
        password = EncryptedCharField(max_length=500)

    Data is encrypted when saved to database and decrypted when retrieved.
    """

    def get_prep_value(self, value):
        """
        Encrypt the value before saving to database.
        """
        if value is None:
            return value
        return EncryptionManager.encrypt(str(value))

    def from_db_value(self, value, expression, connection):
        """
        Decrypt the value when retrieved from database.
        """
        if value is None:
            return value
        return EncryptionManager.decrypt(value)

    def to_python(self, value):
        """
        Convert value to Python type. For encrypted fields, we return as-is
        since from_db_value handles decryption.
        """
        if isinstance(value, str):
            # Only decrypt if it looks like an encrypted token (starts with 'gAAAAA')
            if value.startswith("gAAAAA"):
                return EncryptionManager.decrypt(value)
        return value
