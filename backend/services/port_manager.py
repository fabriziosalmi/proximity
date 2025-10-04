"""
Port Manager Service for Proximity Platinum Edition

This service manages port allocation for the port-based reverse proxy architecture.
Each deployed application receives two unique ports:
- Public port (30000-30999): For standard external access
- Internal port (40000-40999): For iframe embedding with stripped security headers

Architecture:
    - Sequential port allocation within defined ranges
    - Database-backed port tracking
    - Automatic conflict resolution
    - Port recycling on app deletion

Author: Proximity Team
Date: October 2025
"""

import logging
from typing import Tuple, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from models.database import App as DBApp
from core.config import settings
from core.exceptions import AppOperationError

logger = logging.getLogger(__name__)


class PortManagerService:
    """
    Manages port allocation for deployed applications.
    
    This service ensures each application gets unique ports for both
    public and internal (iframe) access paths.
    """
    
    def __init__(self, db: Session):
        """
        Initialize the Port Manager.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.public_port_start = settings.PUBLIC_PORT_RANGE_START
        self.public_port_end = settings.PUBLIC_PORT_RANGE_END
        self.internal_port_start = settings.INTERNAL_PORT_RANGE_START
        self.internal_port_end = settings.INTERNAL_PORT_RANGE_END
        
        logger.info(
            f"Port Manager initialized: "
            f"Public range: {self.public_port_start}-{self.public_port_end}, "
            f"Internal range: {self.internal_port_start}-{self.internal_port_end}"
        )
    
    async def assign_next_available_ports(self, app_id: str) -> Tuple[int, int]:
        """
        Assign the next available public and internal ports for an application.
        
        This method queries the database to find all currently assigned ports
        and returns the next available port in each range. Ports are assigned
        sequentially to make tracking and debugging easier.
        
        Args:
            app_id: Application ID (for logging purposes)
            
        Returns:
            Tuple of (public_port, internal_port)
            
        Raises:
            AppOperationError: If no ports are available in either range
            
        Example:
            public_port, internal_port = await port_manager.assign_next_available_ports("app-123")
            # Returns: (30001, 40001) for the first app
        """
        try:
            # Get all currently assigned ports
            used_public_ports = self._get_used_public_ports()
            used_internal_ports = self._get_used_internal_ports()
            
            # Find next available public port
            public_port = self._find_next_available_port(
                self.public_port_start,
                self.public_port_end,
                used_public_ports
            )
            
            if public_port is None:
                raise AppOperationError(
                    f"No available public ports in range "
                    f"{self.public_port_start}-{self.public_port_end}"
                )
            
            # Find next available internal port
            internal_port = self._find_next_available_port(
                self.internal_port_start,
                self.internal_port_end,
                used_internal_ports
            )
            
            if internal_port is None:
                raise AppOperationError(
                    f"No available internal ports in range "
                    f"{self.internal_port_start}-{self.internal_port_end}"
                )
            
            logger.info(
                f"Assigned ports for app {app_id}: "
                f"public={public_port}, internal={internal_port}"
            )
            
            return (public_port, internal_port)
            
        except Exception as e:
            logger.error(f"Failed to assign ports for app {app_id}: {e}", exc_info=True)
            raise AppOperationError(f"Port assignment failed: {e}")
    
    def _get_used_public_ports(self) -> List[int]:
        """
        Get all currently assigned public ports from the database.
        
        Returns:
            List of public ports currently in use
        """
        apps = self.db.query(DBApp.public_port).filter(
            DBApp.public_port.isnot(None)
        ).all()
        
        return [app.public_port for app in apps if app.public_port is not None]
    
    def _get_used_internal_ports(self) -> List[int]:
        """
        Get all currently assigned internal ports from the database.
        
        Returns:
            List of internal ports currently in use
        """
        apps = self.db.query(DBApp.internal_port).filter(
            DBApp.internal_port.isnot(None)
        ).all()
        
        return [app.internal_port for app in apps if app.internal_port is not None]
    
    def _find_next_available_port(
        self, 
        start: int, 
        end: int, 
        used_ports: List[int]
    ) -> Optional[int]:
        """
        Find the next available port in the given range.
        
        This implementation uses sequential allocation, starting from the
        beginning of the range and finding the first available port.
        
        Args:
            start: Start of port range (inclusive)
            end: End of port range (inclusive)
            used_ports: List of ports already in use
            
        Returns:
            Next available port, or None if range is exhausted
        """
        used_ports_set = set(used_ports)
        
        for port in range(start, end + 1):
            if port not in used_ports_set:
                return port
        
        return None
    
    async def release_ports_for_app(self, app_id: str) -> None:
        """
        Release ports for a deleted application by clearing the port assignments.
        
        Args:
            app_id: Application ID
        """
        try:
            app = self.db.query(DBApp).filter(DBApp.id == app_id).first()
            if app:
                logger.info(
                    f"Releasing ports for app {app_id}: "
                    f"public_port={app.public_port}, internal_port={app.internal_port}"
                )
                app.public_port = None
                app.internal_port = None
                self.db.commit()
                logger.info(f"Ports released for app {app_id}")
            else:
                logger.warning(f"App {app_id} not found, ports may already be released")
        except Exception as e:
            logger.error(f"Error releasing ports for app {app_id}: {e}", exc_info=True)
            self.db.rollback()
            # Don't raise - port release failures shouldn't block app deletion
    
    def get_port_usage_stats(self) -> dict:
        """
        Get statistics about port usage across both ranges.
        
        Returns:
            Dictionary with port usage statistics
        """
        used_public = len(self._get_used_public_ports())
        used_internal = len(self._get_used_internal_ports())
        
        total_public = self.public_port_end - self.public_port_start + 1
        total_internal = self.internal_port_end - self.internal_port_start + 1
        
        return {
            "public_ports": {
                "used": used_public,
                "total": total_public,
                "available": total_public - used_public,
                "usage_percent": round((used_public / total_public) * 100, 2)
            },
            "internal_ports": {
                "used": used_internal,
                "total": total_internal,
                "available": total_internal - used_internal,
                "usage_percent": round((used_internal / total_internal) * 100, 2)
            }
        }
    
    def validate_port_in_range(self, port: int, port_type: str = "public") -> bool:
        """
        Validate if a port is within the allowed range.
        
        Args:
            port: Port number to validate
            port_type: Either "public" or "internal"
            
        Returns:
            True if port is in valid range, False otherwise
        """
        if port_type == "public":
            return self.public_port_start <= port <= self.public_port_end
        elif port_type == "internal":
            return self.internal_port_start <= port <= self.internal_port_end
        else:
            return False
