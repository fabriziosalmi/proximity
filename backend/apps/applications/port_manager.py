"""
Port Manager Service - Allocates and releases unique ports for applications.
"""

import logging
from typing import Optional, Tuple
from django.db import transaction

logger = logging.getLogger(__name__)


class PortManagerService:
    """
    Manages port allocation for deployed applications.
    Ensures unique port assignments for public and internal access.
    """

    # Port ranges (configurable)
    PUBLIC_PORT_START = 8100
    PUBLIC_PORT_END = 8999
    INTERNAL_PORT_START = 9100
    INTERNAL_PORT_END = 9999

    def __init__(self):
        """Initialize port manager."""
        pass

    @transaction.atomic
    def allocate_ports(self) -> Tuple[int, int]:
        """
        Allocate a unique public and internal port pair.

        Returns:
            Tuple of (public_port, internal_port)

        Raises:
            ValueError: If no ports are available
        """
        from apps.applications.models import Application

        # Find next available public port
        public_port = self._find_next_available_port(
            Application, "public_port", self.PUBLIC_PORT_START, self.PUBLIC_PORT_END
        )

        if public_port is None:
            raise ValueError("No available public ports in range")

        # Find next available internal port
        internal_port = self._find_next_available_port(
            Application, "internal_port", self.INTERNAL_PORT_START, self.INTERNAL_PORT_END
        )

        if internal_port is None:
            raise ValueError("No available internal ports in range")

        logger.info(f"Allocated ports: public={public_port}, internal={internal_port}")
        return public_port, internal_port

    def _find_next_available_port(
        self, model, field_name: str, start_port: int, end_port: int
    ) -> Optional[int]:
        """
        Find the next available port in the given range.

        Args:
            model: Django model to query
            field_name: Field name to check
            start_port: Start of port range
            end_port: End of port range

        Returns:
            Available port number or None if no ports available
        """
        # Get all allocated ports in range
        allocated_ports = set(
            model.objects.filter(
                **{
                    f"{field_name}__gte": start_port,
                    f"{field_name}__lte": end_port,
                }
            ).values_list(field_name, flat=True)
        )

        # Find first available port
        for port in range(start_port, end_port + 1):
            if port not in allocated_ports:
                return port

        return None

    def release_ports(self, public_port: Optional[int], internal_port: Optional[int]):
        """
        Release ports back to the pool.

        In Django, ports are automatically released when the Application
        record is deleted, so this is mainly for logging purposes.

        Args:
            public_port: Public port to release
            internal_port: Internal port to release
        """
        logger.info(f"Released ports: public={public_port}, internal={internal_port}")

    def is_port_available(self, port: int, port_type: str = "public") -> bool:
        """
        Check if a specific port is available.

        Args:
            port: Port number to check
            port_type: 'public' or 'internal'

        Returns:
            True if port is available
        """
        from apps.applications.models import Application

        field_name = "public_port" if port_type == "public" else "internal_port"

        return not Application.objects.filter(**{field_name: port}).exists()

    def get_port_range_usage(self) -> dict:
        """
        Get statistics about port usage.

        Returns:
            Dictionary with port usage statistics
        """
        from apps.applications.models import Application

        public_used = Application.objects.filter(
            public_port__gte=self.PUBLIC_PORT_START, public_port__lte=self.PUBLIC_PORT_END
        ).count()

        internal_used = Application.objects.filter(
            internal_port__gte=self.INTERNAL_PORT_START, internal_port__lte=self.INTERNAL_PORT_END
        ).count()

        public_total = self.PUBLIC_PORT_END - self.PUBLIC_PORT_START + 1
        internal_total = self.INTERNAL_PORT_END - self.INTERNAL_PORT_START + 1

        return {
            "public": {
                "used": public_used,
                "available": public_total - public_used,
                "total": public_total,
                "range": f"{self.PUBLIC_PORT_START}-{self.PUBLIC_PORT_END}",
            },
            "internal": {
                "used": internal_used,
                "available": internal_total - internal_used,
                "total": internal_total,
                "range": f"{self.INTERNAL_PORT_START}-{self.INTERNAL_PORT_END}",
            },
        }
