"""
Settings Service for Proximity

Manages system configuration with encryption for sensitive values.
"""

from sqlalchemy.orm import Session
from models.database import Setting
from services.encryption_service import get_encryption_service
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class SettingsService:
    """Manage system settings with encryption for sensitive data"""

    # Define which settings should be encrypted
    ENCRYPTED_KEYS = {
        'proxmox_password',
        'proxmox_api_token',
        'smtp_password',
        'database_password',
        'encryption_key',
        # Add more sensitive keys as needed
    }

    def __init__(self):
        self.encryption = get_encryption_service()

    def get(self, db: Session, key: str, default: Any = None) -> Any:
        """
        Get setting value (auto-decrypts if encrypted)

        Args:
            db: Database session
            key: Setting key
            default: Default value if not found

        Returns:
            Setting value (decrypted if was encrypted)
        """
        setting = db.query(Setting).filter(Setting.key == key).first()

        if not setting:
            return default

        value = setting.value

        if setting.is_encrypted:
            try:
                value = self.encryption.decrypt(value)
            except ValueError as e:
                logger.error(f"Failed to decrypt setting '{key}': {e}")
                return default

        return value

    def set(
        self, db: Session, key: str, value: str,
        category: str = 'system', user_id: int = None,
        description: str = None
    ) -> Setting:
        """
        Set setting value (auto-encrypts if sensitive)

        Args:
            db: Database session
            key: Setting key
            value: Setting value
            category: Category (proxmox, network, system, resources)
            user_id: ID of user making the change
            description: Optional description

        Returns:
            Setting object
        """
        # Check if should encrypt
        is_encrypted = key in self.ENCRYPTED_KEYS
        stored_value = value

        if is_encrypted and value:
            stored_value = self.encryption.encrypt(value)

        # Update or create
        setting = db.query(Setting).filter(Setting.key == key).first()

        if setting:
            setting.value = stored_value
            setting.is_encrypted = is_encrypted
            setting.updated_by = user_id
            if description:
                setting.description = description
        else:
            setting = Setting(
                key=key,
                value=stored_value,
                is_encrypted=is_encrypted,
                category=category,
                updated_by=user_id,
                description=description
            )
            db.add(setting)

        db.commit()
        db.refresh(setting)

        logger.info(f"Setting '{key}' updated by user {user_id} (encrypted: {is_encrypted})")
        return setting

    def get_category(self, db: Session, category: str) -> Dict[str, Any]:
        """
        Get all settings in a category (decrypted)

        Args:
            db: Database session
            category: Category name

        Returns:
            Dictionary of key:value pairs
        """
        settings = db.query(Setting).filter(Setting.category == category).all()

        result = {}
        for setting in settings:
            value = setting.value
            if setting.is_encrypted:
                try:
                    value = self.encryption.decrypt(value)
                except ValueError:
                    logger.warning(f"Could not decrypt {setting.key}")
                    value = None
            result[setting.key] = value

        return result

    def delete(self, db: Session, key: str) -> bool:
        """Delete a setting"""
        setting = db.query(Setting).filter(Setting.key == key).first()
        if setting:
            db.delete(setting)
            db.commit()
            logger.info(f"Setting '{key}' deleted")
            return True
        return False

    # Convenience methods for common settings

    def set_proxmox_credentials(
        self, db: Session, host: str, user: str,
        password: str, port: int = 8006,
        verify_ssl: bool = False, user_id: int = None
    ):
        """Set Proxmox connection credentials"""
        self.set(db, 'proxmox_host', host, 'proxmox', user_id, 'Proxmox host IP/hostname')
        self.set(db, 'proxmox_user', user, 'proxmox', user_id, 'Proxmox username')
        self.set(db, 'proxmox_password', password, 'proxmox', user_id, 'Proxmox password (encrypted)')
        self.set(db, 'proxmox_port', str(port), 'proxmox', user_id, 'Proxmox API port')
        self.set(db, 'proxmox_verify_ssl', str(verify_ssl), 'proxmox', user_id, 'Verify SSL certificate')

        logger.info(f"Proxmox credentials updated by user {user_id}")

    def get_proxmox_credentials(self, db: Session) -> Dict[str, Any]:
        """Get Proxmox credentials (decrypted)"""
        return {
            'host': self.get(db, 'proxmox_host'),
            'user': self.get(db, 'proxmox_user'),
            'password': self.get(db, 'proxmox_password'),  # Auto-decrypted
            'port': int(self.get(db, 'proxmox_port', 8006)),
            'verify_ssl': self.get(db, 'proxmox_verify_ssl', 'false').lower() == 'true'
        }

    def set_network_settings(
        self, db: Session, lan_subnet: str = None, lan_gateway: str = None,
        dhcp_start: str = None, dhcp_end: str = None,
        dns_domain: str = None, user_id: int = None
    ):
        """Set network configuration"""
        if lan_subnet:
            self.set(db, 'lan_subnet', lan_subnet, 'network', user_id, 'LAN subnet (CIDR)')
        if lan_gateway:
            self.set(db, 'lan_gateway', lan_gateway, 'network', user_id, 'LAN gateway IP')
        if dhcp_start:
            self.set(db, 'dhcp_start', dhcp_start, 'network', user_id, 'DHCP range start')
        if dhcp_end:
            self.set(db, 'dhcp_end', dhcp_end, 'network', user_id, 'DHCP range end')
        if dns_domain:
            self.set(db, 'dns_domain', dns_domain, 'network', user_id, 'DNS domain suffix')

        logger.info(f"Network settings updated by user {user_id}")

    def get_network_settings(self, db: Session) -> Dict[str, str]:
        """Get network configuration"""
        return {
            'lan_subnet': self.get(db, 'lan_subnet', '10.20.0.0/24'),
            'lan_gateway': self.get(db, 'lan_gateway', '10.20.0.1'),
            'dhcp_start': self.get(db, 'dhcp_start', '10.20.0.100'),
            'dhcp_end': self.get(db, 'dhcp_end', '10.20.0.250'),
            'dns_domain': self.get(db, 'dns_domain', 'prox.local')
        }

    def set_default_resources(
        self, db: Session, lxc_memory: int = None, lxc_cores: int = None,
        lxc_disk: int = None, lxc_storage: str = None, user_id: int = None
    ):
        """Set default LXC resource allocations"""
        if lxc_memory:
            self.set(db, 'lxc_memory', str(lxc_memory), 'resources', user_id, 'Default LXC memory (MB)')
        if lxc_cores:
            self.set(db, 'lxc_cores', str(lxc_cores), 'resources', user_id, 'Default LXC CPU cores')
        if lxc_disk:
            self.set(db, 'lxc_disk', str(lxc_disk), 'resources', user_id, 'Default LXC disk size (GB)')
        if lxc_storage:
            self.set(db, 'lxc_storage', lxc_storage, 'resources', user_id, 'Default Proxmox storage')

        logger.info(f"Default resources updated by user {user_id}")

    def get_default_resources(self, db: Session) -> Dict[str, Any]:
        """Get default LXC resource allocations"""
        return {
            'lxc_memory': int(self.get(db, 'lxc_memory', 2048)),
            'lxc_cores': int(self.get(db, 'lxc_cores', 2)),
            'lxc_disk': int(self.get(db, 'lxc_disk', 8)),
            'lxc_storage': self.get(db, 'lxc_storage', 'local-lvm')
        }


# Singleton instance
settings_service = SettingsService()


def get_settings_service() -> SettingsService:
    """Get settings service singleton"""
    return settings_service
