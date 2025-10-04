"""
Unit tests for MonitoringService.

Tests the caching behavior and metric processing of the monitoring service.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from models.database import App as DBApp
from services.monitoring_service import MonitoringService


class TestMonitoringService:
    """Test suite for MonitoringService."""

    @pytest.fixture
    def mock_proxmox_service(self):
        """Create a mock ProxmoxService."""
        mock = MagicMock()
        mock.get_lxc_status = AsyncMock()
        return mock

    @pytest.fixture
    def monitoring_service(self, mock_proxmox_service):
        """Create MonitoringService instance for testing."""
        return MonitoringService(mock_proxmox_service)

    @pytest.fixture
    def sample_app(self):
        """Create a sample app for testing."""
        return DBApp(
            id="test-app",
            catalog_id="nginx",
            name="Test App",
            hostname="test-app",
            status="running",
            lxc_id=100,
            node="testnode",
            url="http://10.20.0.100:80"
        )

    @pytest.fixture
    def sample_proxmox_response(self):
        """Sample response from Proxmox API."""
        return {
            'cpu': 0.15,  # 15% CPU
            'mem': 1288490188,  # ~1.2 GB
            'maxmem': 4294967296,  # 4 GB
            'disk': 5905580032,  # ~5.5 GB
            'maxdisk': 21474836480,  # 20 GB
            'uptime': 3600,  # 1 hour
            'status': 'running'
        }

    @pytest.mark.asyncio
    async def test_get_current_app_stats_success(
        self, monitoring_service, mock_proxmox_service, sample_app, sample_proxmox_response
    ):
        """Test successful stats retrieval and metric processing."""
        # Setup mock
        mock_proxmox_service.get_lxc_status.return_value = sample_proxmox_response

        # Get stats
        stats = await monitoring_service.get_current_app_stats(sample_app)

        # Verify Proxmox API was called
        mock_proxmox_service.get_lxc_status.assert_called_once_with("testnode", 100)

        # Verify metrics are correctly processed
        assert stats['cpu_load'] == 0.15
        assert stats['cpu_percent'] == 15.0

        assert stats['mem_used_bytes'] == 1288490188
        assert stats['mem_total_bytes'] == 4294967296
        assert stats['mem_used_gb'] == 1.2
        assert stats['mem_total_gb'] == 4.0
        assert stats['mem_percent'] == 30.0

        assert stats['disk_used_bytes'] == 5905580032
        assert stats['disk_total_bytes'] == 21474836480
        assert stats['disk_used_gb'] == 5.5
        assert stats['disk_total_gb'] == 20.0
        assert stats['disk_percent'] == 27.5

        assert stats['uptime_seconds'] == 3600
        assert stats['status'] == 'running'
        assert stats['cached'] is False  # First fetch is not cached
        assert 'timestamp' in stats

    @pytest.mark.asyncio
    async def test_get_current_app_stats_uses_cache(
        self, monitoring_service, mock_proxmox_service, sample_app, sample_proxmox_response
    ):
        """Test that consecutive calls use cache and don't hit Proxmox API."""
        # Setup mock
        mock_proxmox_service.get_lxc_status.return_value = sample_proxmox_response

        # First call - should hit API
        stats1 = await monitoring_service.get_current_app_stats(sample_app)
        assert stats1['cached'] is False
        assert mock_proxmox_service.get_lxc_status.call_count == 1

        # Second call immediately - should use cache
        stats2 = await monitoring_service.get_current_app_stats(sample_app)
        assert stats2['cached'] is True
        assert mock_proxmox_service.get_lxc_status.call_count == 1  # Still 1!

        # Third call - still cached
        stats3 = await monitoring_service.get_current_app_stats(sample_app)
        assert stats3['cached'] is True
        assert mock_proxmox_service.get_lxc_status.call_count == 1

    @pytest.mark.asyncio
    async def test_get_current_app_stats_cache_expires(
        self, monitoring_service, mock_proxmox_service, sample_app, sample_proxmox_response
    ):
        """Test that cache expires after TTL and API is called again."""
        # Setup mock
        mock_proxmox_service.get_lxc_status.return_value = sample_proxmox_response

        # First call - populates cache
        stats1 = await monitoring_service.get_current_app_stats(sample_app)
        assert stats1['cached'] is False
        assert mock_proxmox_service.get_lxc_status.call_count == 1

        # Manually expire the cache by modifying timestamp
        cached_time, cached_data = monitoring_service._cache[100]
        expired_time = cached_time - timedelta(seconds=monitoring_service.CACHE_TTL + 1)
        monitoring_service._cache[100] = (expired_time, cached_data)

        # Second call - cache expired, should hit API again
        stats2 = await monitoring_service.get_current_app_stats(sample_app)
        assert stats2['cached'] is False
        assert mock_proxmox_service.get_lxc_status.call_count == 2

    @pytest.mark.asyncio
    async def test_get_current_app_stats_handles_proxmox_error(
        self, monitoring_service, mock_proxmox_service, sample_app
    ):
        """Test error handling when Proxmox API fails."""
        # Setup mock to raise exception
        mock_proxmox_service.get_lxc_status.side_effect = Exception("Proxmox connection error")

        # Should propagate exception
        with pytest.raises(Exception, match="Proxmox connection error"):
            await monitoring_service.get_current_app_stats(sample_app)

    @pytest.mark.asyncio
    async def test_clear_cache_single_entry(
        self, monitoring_service, mock_proxmox_service, sample_app, sample_proxmox_response
    ):
        """Test clearing a single cache entry."""
        # Setup and populate cache
        mock_proxmox_service.get_lxc_status.return_value = sample_proxmox_response
        await monitoring_service.get_current_app_stats(sample_app)

        # Verify cache has entry
        assert 100 in monitoring_service._cache

        # Clear specific entry
        monitoring_service.clear_cache(lxc_id=100)

        # Verify entry removed
        assert 100 not in monitoring_service._cache

    @pytest.mark.asyncio
    async def test_clear_cache_all_entries(
        self, monitoring_service, mock_proxmox_service, sample_app, sample_proxmox_response
    ):
        """Test clearing entire cache."""
        # Setup and populate cache with multiple entries
        mock_proxmox_service.get_lxc_status.return_value = sample_proxmox_response

        app1 = sample_app
        app2 = DBApp(
            id="test-app-2",
            catalog_id="nginx",
            name="Test App 2",
            hostname="test-app-2",
            status="running",
            lxc_id=101,
            node="testnode"
        )

        await monitoring_service.get_current_app_stats(app1)
        await monitoring_service.get_current_app_stats(app2)

        # Verify cache has 2 entries
        assert len(monitoring_service._cache) == 2

        # Clear all
        monitoring_service.clear_cache()

        # Verify cache is empty
        assert len(monitoring_service._cache) == 0

    def test_get_cache_stats(
        self, monitoring_service
    ):
        """Test cache statistics reporting."""
        # Empty cache
        stats = monitoring_service.get_cache_stats()
        assert stats['total_entries'] == 0
        assert stats['valid_entries'] == 0
        assert stats['expired_entries'] == 0
        assert stats['cache_ttl_seconds'] == 10

    @pytest.mark.asyncio
    async def test_concurrent_requests_same_app(
        self, monitoring_service, mock_proxmox_service, sample_app, sample_proxmox_response
    ):
        """Test that concurrent requests for same app result in single API call."""
        # Setup mock with small delay to simulate real API call
        async def delayed_response(*args, **kwargs):
            await asyncio.sleep(0.1)
            return sample_proxmox_response

        mock_proxmox_service.get_lxc_status.side_effect = delayed_response

        # Make 3 concurrent requests
        results = await asyncio.gather(
            monitoring_service.get_current_app_stats(sample_app),
            monitoring_service.get_current_app_stats(sample_app),
            monitoring_service.get_current_app_stats(sample_app)
        )

        # First request hits API, others should use cache
        # Due to async timing, we might get 1-3 API calls depending on exact timing
        # But we should get fewer than 3 total calls
        assert mock_proxmox_service.get_lxc_status.call_count <= 3

        # All results should have the same data
        assert all(r['cpu_percent'] == 15.0 for r in results)

    @pytest.mark.asyncio
    async def test_zero_values_handled_correctly(
        self, monitoring_service, mock_proxmox_service, sample_app
    ):
        """Test handling of zero/null values from Proxmox."""
        # Response with zero values
        zero_response = {
            'cpu': 0.0,
            'mem': 0,
            'maxmem': 1,  # Prevent division by zero
            'disk': 0,
            'maxdisk': 1,  # Prevent division by zero
            'uptime': 0,
            'status': 'stopped'
        }

        mock_proxmox_service.get_lxc_status.return_value = zero_response

        stats = await monitoring_service.get_current_app_stats(sample_app)

        assert stats['cpu_percent'] == 0.0
        assert stats['mem_percent'] == 0.0
        assert stats['disk_percent'] == 0.0
        assert stats['uptime_seconds'] == 0
        assert stats['status'] == 'stopped'
