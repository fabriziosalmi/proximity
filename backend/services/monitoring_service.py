"""
Monitoring Service for Proximity

This service provides scalable, on-demand container resource monitoring
with intelligent caching to prevent API abuse and ensure performance
at scale (hundreds/thousands of containers).

Performance Characteristics:
- In-memory cache with TTL prevents redundant Proxmox API calls
- Single API call per container fetches all metrics
- Zero polling overhead when metrics not being viewed
- Handles concurrent requests efficiently via cache

Author: Proximity Team
Date: October 2025
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from models.database import App

logger = logging.getLogger(__name__)


class MonitoringService:
    """
    Lightweight monitoring service with intelligent caching.

    Design Philosophy:
    - On-demand only: Metrics fetched when requested, not continuously polled
    - Cache-first: Check cache before hitting Proxmox API
    - Single source: One API call returns all metrics (CPU, RAM, disk)
    - Auto-cleanup: Stale cache entries naturally expire

    Performance:
    - 10 users viewing same app = 1 API call per 10 seconds
    - App not being viewed = 0 API calls
    - Sub-millisecond response time on cache hit
    """

    def __init__(self, proxmox_service):
        """
        Initialize monitoring service.

        Args:
            proxmox_service: ProxmoxService instance for API calls
        """
        self.proxmox = proxmox_service

        # In-memory cache: {lxc_id: (timestamp, metrics_dict)}
        self._cache: Dict[int, Tuple[datetime, dict]] = {}

        # Cache TTL in seconds - balance freshness vs API load
        self.CACHE_TTL = 10

        logger.info("MonitoringService initialized with %d second cache TTL", self.CACHE_TTL)

    async def get_current_app_stats(self, app: App) -> dict:
        """
        Get current resource usage stats for an application.

        This is the core method that implements the caching strategy:
        1. Check cache for recent data
        2. On miss: fetch from Proxmox API
        3. Process and normalize data
        4. Update cache
        5. Return metrics

        Args:
            app: App object with node, lxc_id populated

        Returns:
            Dict with normalized metrics:
            {
                "cpu_load": float,          # 0.0-1.0 (0-100%)
                "cpu_percent": float,       # 0-100
                "mem_used_bytes": int,      # Bytes
                "mem_total_bytes": int,     # Bytes
                "mem_used_gb": float,       # GB (2 decimals)
                "mem_total_gb": float,      # GB (2 decimals)
                "mem_percent": float,       # 0-100
                "disk_used_bytes": int,     # Bytes
                "disk_total_bytes": int,    # Bytes
                "disk_used_gb": float,      # GB (2 decimals)
                "disk_total_gb": float,     # GB (2 decimals)
                "disk_percent": float,      # 0-100
                "uptime_seconds": int,      # Uptime
                "status": str,              # running/stopped
                "cached": bool,             # Was this a cache hit?
                "timestamp": str            # ISO timestamp
            }

        Raises:
            Exception: If Proxmox API call fails
        """
        lxc_id = app.lxc_id
        node = app.node

        # ================================================================
        # PHASE 1: CHECK CACHE
        # ================================================================
        if lxc_id in self._cache:
            cached_time, cached_data = self._cache[lxc_id]
            age = (datetime.utcnow() - cached_time).total_seconds()

            if age < self.CACHE_TTL:
                logger.debug(
                    f"📊 Cache HIT for LXC {lxc_id} (age: {age:.1f}s, TTL: {self.CACHE_TTL}s)"
                )
                cached_data['cached'] = True
                return cached_data
            else:
                logger.debug(
                    f"📊 Cache EXPIRED for LXC {lxc_id} (age: {age:.1f}s > TTL: {self.CACHE_TTL}s)"
                )
        else:
            logger.debug(f"📊 Cache MISS for LXC {lxc_id} (first request)")

        # ================================================================
        # PHASE 2: FETCH FROM PROXMOX API
        # ================================================================
        logger.debug(f"🔍 Fetching current stats for LXC {lxc_id} on node {node}")

        try:
            # Single API call gets all metrics
            # Reference: https://pve.proxmox.com/pve-docs/api-viewer/#/nodes/{node}/lxc/{vmid}/status/current
            raw_stats = await self.proxmox.get_lxc_status(node, lxc_id)

            logger.debug(f"✓ Received stats for LXC {lxc_id}: {list(raw_stats.keys())}")

        except Exception as e:
            logger.error(f"❌ Failed to fetch stats for LXC {lxc_id}: {e}")
            raise

        # ================================================================
        # PHASE 3: PROCESS AND NORMALIZE METRICS
        # ================================================================

        # CPU metrics
        cpu_load = raw_stats.get('cpu', 0.0)  # Already 0.0-1.0
        cpu_percent = round(cpu_load * 100, 2)

        # Memory metrics (Proxmox returns bytes)
        mem_used_bytes = raw_stats.get('mem', 0)
        mem_total_bytes = raw_stats.get('maxmem', 1)  # Avoid division by zero
        mem_used_gb = round(mem_used_bytes / (1024**3), 2)
        mem_total_gb = round(mem_total_bytes / (1024**3), 2)
        mem_percent = round((mem_used_bytes / mem_total_bytes) * 100, 2) if mem_total_bytes > 0 else 0.0

        # Disk metrics (Proxmox returns bytes)
        disk_used_bytes = raw_stats.get('disk', 0)
        disk_total_bytes = raw_stats.get('maxdisk', 1)  # Avoid division by zero
        disk_used_gb = round(disk_used_bytes / (1024**3), 2)
        disk_total_gb = round(disk_total_bytes / (1024**3), 2)
        disk_percent = round((disk_used_bytes / disk_total_bytes) * 100, 2) if disk_total_bytes > 0 else 0.0

        # Other metrics
        uptime_seconds = raw_stats.get('uptime', 0)
        status = raw_stats.get('status', 'unknown')

        # Build normalized response
        metrics = {
            # CPU
            "cpu_load": cpu_load,
            "cpu_percent": cpu_percent,

            # Memory
            "mem_used_bytes": mem_used_bytes,
            "mem_total_bytes": mem_total_bytes,
            "mem_used_gb": mem_used_gb,
            "mem_total_gb": mem_total_gb,
            "mem_percent": mem_percent,

            # Disk
            "disk_used_bytes": disk_used_bytes,
            "disk_total_bytes": disk_total_bytes,
            "disk_used_gb": disk_used_gb,
            "disk_total_gb": disk_total_gb,
            "disk_percent": disk_percent,

            # Status
            "uptime_seconds": uptime_seconds,
            "status": status,

            # Metadata
            "cached": False,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        # ================================================================
        # PHASE 4: UPDATE CACHE
        # ================================================================
        self._cache[lxc_id] = (datetime.utcnow(), metrics)
        logger.debug(f"💾 Cached stats for LXC {lxc_id} (cache size: {len(self._cache)})")

        return metrics

    def clear_cache(self, lxc_id: Optional[int] = None):
        """
        Clear cache entries.

        Args:
            lxc_id: If provided, clear only this container's cache.
                   If None, clear entire cache.
        """
        if lxc_id is not None:
            if lxc_id in self._cache:
                del self._cache[lxc_id]
                logger.debug(f"🗑️  Cleared cache for LXC {lxc_id}")
        else:
            count = len(self._cache)
            self._cache.clear()
            logger.debug(f"🗑️  Cleared entire cache ({count} entries)")

    def get_cache_stats(self) -> dict:
        """
        Get cache statistics for monitoring/debugging.

        Returns:
            Dict with cache metrics
        """
        now = datetime.utcnow()

        valid_entries = 0
        expired_entries = 0

        for cached_time, _ in self._cache.values():
            age = (now - cached_time).total_seconds()
            if age < self.CACHE_TTL:
                valid_entries += 1
            else:
                expired_entries += 1

        return {
            "total_entries": len(self._cache),
            "valid_entries": valid_entries,
            "expired_entries": expired_entries,
            "cache_ttl_seconds": self.CACHE_TTL
        }


# Singleton instance
_monitoring_service: Optional[MonitoringService] = None


def get_monitoring_service(proxmox_service) -> MonitoringService:
    """
    Get or create the singleton MonitoringService instance.

    Args:
        proxmox_service: ProxmoxService instance

    Returns:
        MonitoringService singleton
    """
    global _monitoring_service

    if _monitoring_service is None:
        _monitoring_service = MonitoringService(proxmox_service)
        logger.info("✓ MonitoringService singleton created")

    return _monitoring_service
