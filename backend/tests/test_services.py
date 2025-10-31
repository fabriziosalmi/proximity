"""
Unit tests for service layer classes.
"""
import pytest
from apps.applications.port_manager import PortManagerService
from apps.catalog.services import CatalogService
from apps.catalog.schemas import CatalogAppSchema


class TestPortManagerService:
    """Test PortManagerService."""
    
    def test_allocate_ports_success(self, db):
        """Test successful port allocation."""
        service = PortManagerService()
        public_port, internal_port = service.allocate_ports()
        
        assert 8100 <= public_port <= 8999
        assert 9100 <= internal_port <= 9999
        assert public_port != internal_port
    
    def test_allocate_ports_no_duplicates(self, db, test_application):
        """Test that allocated ports don't conflict with existing ones."""
        service = PortManagerService()
        
        # test_application uses port 8080
        public_port, internal_port = service.allocate_ports()
        
        # Should not allocate the same port
        assert public_port != test_application.public_port
        assert internal_port != test_application.internal_port
    
    def test_is_port_available_true(self, db):
        """Test checking if port is available."""
        service = PortManagerService()
        assert service.is_port_available(9999, 'public') is True
    
    def test_is_port_available_false(self, db, test_application):
        """Test checking if port is not available."""
        service = PortManagerService()
        # test_application uses public_port=8080
        assert service.is_port_available(8080, 'public') is False
    
    def test_release_ports(self, db):
        """Test releasing ports (logging only)."""
        service = PortManagerService()
        # Should not raise any exceptions
        service.release_ports(8080, 10080)


class TestCatalogService:
    """Test CatalogService with real JSON loading."""
    
    def test_get_all_apps(self):
        """Test getting all catalog apps."""
        service = CatalogService()
        apps = service.get_all_apps()
        
        assert isinstance(apps, list)
        # Each app should be a CatalogAppSchema
        if len(apps) > 0:
            assert isinstance(apps[0], CatalogAppSchema)
            # Apps should be sorted by name
            names = [app.name.lower() for app in apps]
            assert names == sorted(names)
    
    def test_get_app_by_id(self):
        """Test getting app by ID."""
        service = CatalogService()
        
        # If catalog has apps, test fetching one
        all_apps = service.get_all_apps()
        if len(all_apps) > 0:
            first_app = all_apps[0]
            fetched_app = service.get_app_by_id(first_app.id)
            assert fetched_app is not None
            assert fetched_app.id == first_app.id
            assert fetched_app.name == first_app.name
        
        # Test non-existent ID
        assert service.get_app_by_id('nonexistent') is None
    
    def test_get_categories(self):
        """Test getting all categories."""
        service = CatalogService()
        categories = service.get_categories()
        
        assert isinstance(categories, list)
        # Categories should be sorted
        assert categories == sorted(categories)
        # Categories should be unique
        assert len(categories) == len(set(categories))
    
    def test_filter_by_category(self):
        """Test filtering apps by category."""
        service = CatalogService()
        categories = service.get_categories()
        
        if len(categories) > 0:
            category = categories[0]
            apps = service.filter_by_category(category)
            
            assert isinstance(apps, list)
            # All apps should be in the requested category
            for app in apps:
                assert app.category.lower() == category.lower()
    
    def test_search_apps(self):
        """Test searching apps by query."""
        service = CatalogService()
        all_apps = service.get_all_apps()
        
        if len(all_apps) > 0:
            # Search by part of the first app's name
            first_app = all_apps[0]
            query = first_app.name[:3]  # First 3 chars
            results = service.search_apps(query)
            
            assert isinstance(results, list)
            # Should find at least the first app
            found_ids = [app.id for app in results]
            assert first_app.id in found_ids
    
    def test_get_stats(self):
        """Test getting catalog statistics."""
        service = CatalogService()
        stats = service.get_stats()
        
        assert isinstance(stats, dict)
        assert 'total_apps' in stats
        assert 'total_categories' in stats
        assert isinstance(stats['total_apps'], int)
        assert isinstance(stats['total_categories'], int)
        assert stats['total_apps'] >= 0
        assert stats['total_categories'] >= 0


class TestProxmoxService:
    """Test ProxmoxService."""
    
    def test_init_with_host_id(self, db, proxmox_host):
        """Test initializing service with host ID."""
        from apps.proxmox.services import ProxmoxService
        
        service = ProxmoxService(host_id=proxmox_host.id)
        assert service.host_id == proxmox_host.id
        assert service._client is None
    
    def test_init_without_host_id(self, db, proxmox_host):
        """Test initializing service without host ID (uses default)."""
        from apps.proxmox.services import ProxmoxService
        
        # Make sure we have a default host
        proxmox_host.is_default = True
        proxmox_host.save()
        
        service = ProxmoxService()
        assert service.host_id is None
        assert service._client is None
    
    def test_get_host(self, db, proxmox_host):
        """Test getting host instance."""
        from apps.proxmox.services import ProxmoxService
        
        proxmox_host.is_default = True
        proxmox_host.save()
        
        service = ProxmoxService()
        host = service.get_host()
        
        assert host is not None
        assert host.id == proxmox_host.id
        assert host.name == proxmox_host.name
    
    def test_get_host_with_no_active_host(self, db):
        """Test getting host when no active host exists."""
        from apps.proxmox.services import ProxmoxService, ProxmoxError
        from apps.proxmox.models import ProxmoxHost
        from apps.applications.models import Application

        # Delete applications first (to avoid ProtectedError on ProxmoxHost)
        Application.objects.all().delete()

        # Ensure no active hosts exist
        ProxmoxHost.objects.all().delete()

        service = ProxmoxService()

        with pytest.raises(ProxmoxError, match="No active Proxmox host"):
            service.get_host()
