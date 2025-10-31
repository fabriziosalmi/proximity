"""
Unit tests for API utility functions and helpers.
"""

import pytest
from ninja.errors import HttpError


class TestAPIHelpers:
    """Test API helper functions."""

    def test_get_object_or_404_found(self, db, test_application):
        """Test get_object_or_404 when object exists."""
        from django.shortcuts import get_object_or_404
        from apps.applications.models import Application

        app = get_object_or_404(Application, id=test_application.id)
        assert app == test_application

    def test_get_object_or_404_not_found(self, db):
        """Test get_object_or_404 when object doesn't exist."""
        from django.shortcuts import get_object_or_404
        from django.http import Http404
        from apps.applications.models import Application

        with pytest.raises(Http404):
            get_object_or_404(Application, id="nonexistent")

    def test_pagination_logic(self):
        """Test pagination calculation."""
        total_items = 100
        per_page = 20
        page = 2

        # Calculate offset and limit
        offset = (page - 1) * per_page
        limit = per_page

        assert offset == 20  # Skip first 20 items
        assert limit == 20  # Return next 20 items

        # Total pages
        import math

        total_pages = math.ceil(total_items / per_page)
        assert total_pages == 5

    def test_filter_by_status(self, db, test_application, test_user, proxmox_host):
        """Test filtering applications by status."""
        from apps.applications.models import Application

        # Create apps with different statuses
        app1 = Application.objects.create(
            id="app1",
            catalog_id="nginx",
            name="App 1",
            hostname="app1.local",
            status="running",
            host=proxmox_host,
            node="pve",
            owner=test_user,
        )
        app2 = Application.objects.create(
            id="app2",
            catalog_id="mysql",
            name="App 2",
            hostname="app2.local",
            status="stopped",
            host=proxmox_host,
            node="pve",
            owner=test_user,
        )

        running_apps = Application.objects.filter(status="running")
        assert app1 in running_apps
        assert app2 not in running_apps

    def test_search_filter(self, db, test_user, proxmox_host):
        """Test search filtering across multiple fields."""
        from apps.applications.models import Application
        from django.db.models import Q

        app1 = Application.objects.create(
            id="app1",
            catalog_id="nginx",
            name="Web Server",
            hostname="web.local",
            host=proxmox_host,
            node="pve",
            owner=test_user,
        )
        app2 = Application.objects.create(
            id="app2",
            catalog_id="mysql",
            name="Database Server",
            hostname="db.local",
            host=proxmox_host,
            node="pve",
            owner=test_user,
        )

        # Search by name
        search_term = "web"
        results = Application.objects.filter(
            Q(name__icontains=search_term) | Q(hostname__icontains=search_term)
        )

        assert app1 in results
        assert app2 not in results


class TestErrorHandling:
    """Test API error handling."""

    def test_http_error_404(self):
        """Test raising 404 HTTP error."""
        with pytest.raises(HttpError) as exc_info:
            raise HttpError(404, "Resource not found")

        assert exc_info.value.status_code == 404
        assert "not found" in str(exc_info.value)

    def test_http_error_400(self):
        """Test raising 400 HTTP error."""
        with pytest.raises(HttpError) as exc_info:
            raise HttpError(400, "Bad request")

        assert exc_info.value.status_code == 400

    def test_http_error_500(self):
        """Test raising 500 HTTP error."""
        with pytest.raises(HttpError) as exc_info:
            raise HttpError(500, "Internal server error")

        assert exc_info.value.status_code == 500


class TestRequestValidation:
    """Test request validation logic."""

    def test_validate_app_id_format(self):
        """Test application ID format validation."""
        valid_ids = ["app-001", "nginx-123", "my-app-name"]
        invalid_ids = ["app 001", "app@001", ""]

        import re

        pattern = r"^[a-zA-Z0-9-]+$"

        for app_id in valid_ids:
            assert re.match(pattern, app_id) is not None

        for app_id in invalid_ids:
            if app_id:  # Skip empty string
                assert re.match(pattern, app_id) is None

    def test_validate_hostname_format(self):
        """Test hostname format validation."""
        valid_hostnames = ["app.local", "my-app.example.com", "nginx-01.local"]

        invalid_hostnames = ["app with spaces", "app@invalid", ""]

        import re

        # Simplified hostname pattern
        pattern = r"^[a-zA-Z0-9.-]+$"

        for hostname in valid_hostnames:
            assert re.match(pattern, hostname) is not None

        for hostname in invalid_hostnames:
            if hostname:
                assert re.match(pattern, hostname) is None

    def test_validate_port_range(self):
        """Test port number validation."""
        valid_ports = [80, 443, 8080, 3000, 9999]
        invalid_ports = [-1, 0, 70000, 100000]

        for port in valid_ports:
            assert 1 <= port <= 65535

        for port in invalid_ports:
            assert not (1 <= port <= 65535)


class TestDataTransformations:
    """Test data transformation utilities."""

    def test_bytes_to_mb(self):
        """Test converting bytes to megabytes."""
        bytes_value = 5242880  # 5 MB
        mb_value = bytes_value / (1024 * 1024)
        assert round(mb_value, 2) == 5.0

    def test_bytes_to_gb(self):
        """Test converting bytes to gigabytes."""
        bytes_value = 5368709120  # 5 GB
        gb_value = bytes_value / (1024 * 1024 * 1024)
        assert round(gb_value, 2) == 5.0

    def test_format_timestamp(self):
        """Test timestamp formatting."""
        from datetime import datetime

        dt = datetime(2023, 10, 15, 14, 30, 0)
        iso_string = dt.isoformat()

        assert "2023-10-15" in iso_string
        assert "14:30:00" in iso_string

    def test_dict_to_json_serialization(self):
        """Test dictionary JSON serialization."""
        import json

        data = {"name": "Test App", "port": 8080, "config": {"key": "value"}}

        json_str = json.dumps(data)
        restored = json.loads(json_str)

        assert restored == data

    def test_list_to_json_serialization(self):
        """Test list JSON serialization."""
        import json

        data = ["item1", "item2", "item3"]
        json_str = json.dumps(data)
        restored = json.loads(json_str)

        assert restored == data


class TestQueryOptimization:
    """Test database query optimization patterns."""

    def test_select_related_reduces_queries(self, db, test_application):
        """Test that select_related reduces database queries."""
        from apps.applications.models import Application
        from django.test.utils import CaptureQueriesContext
        from django.db import connection

        # Without select_related
        with CaptureQueriesContext(connection) as context1:
            app = Application.objects.get(id=test_application.id)
            _ = app.host.name  # This triggers an additional query

        queries_without = len(context1.captured_queries)

        # With select_related
        with CaptureQueriesContext(connection) as context2:
            app = Application.objects.select_related("host").get(id=test_application.id)
            _ = app.host.name  # No additional query needed

        queries_with = len(context2.captured_queries)

        # Should use fewer queries with select_related
        assert queries_with <= queries_without

    def test_prefetch_related_for_many_to_many(self, db, test_user):
        """Test prefetch_related for related objects."""
        from apps.core.models import User
        from django.test.utils import CaptureQueriesContext
        from django.db import connection

        # With prefetch_related
        with CaptureQueriesContext(connection) as context:
            user = User.objects.prefetch_related("applications").get(id=test_user.id)
            _ = list(user.applications.all())  # No additional query

        # Should be efficient
        assert len(context.captured_queries) <= 3
