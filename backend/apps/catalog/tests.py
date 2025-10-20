"""
Tests for the Catalog service and API endpoints.
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from django.test import TestCase, override_settings
from ninja.testing import TestClient

from apps.catalog.services import CatalogService
from apps.catalog.schemas import CatalogAppSchema
from apps.catalog.api import router


# Sample valid catalog data
VALID_APP_DATA = {
    "id": "test-app",
    "name": "Test Application",
    "version": "1.0.0",
    "description": "A test application for unit testing",
    "icon": "https://example.com/icon.png",
    "category": "Testing",
    "docker_compose": {
        "version": "3.8",
        "services": {
            "test": {
                "image": "test:latest",
                "environment": {},
                "restart": "always"
            }
        }
    },
    "ports": [8080],
    "volumes": [],
    "environment": {},
    "min_memory": 256,
    "min_cpu": 1,
    "tags": ["test", "testing", "unit-test"],
    "author": "Test Author",
    "website": "https://test.example.com"
}

ANOTHER_VALID_APP = {
    "id": "another-app",
    "name": "Another Application",
    "version": "2.0.0",
    "description": "Another test application in a different category",
    "icon": "https://example.com/another-icon.png",
    "category": "Database",
    "docker_compose": {
        "version": "3.8",
        "services": {
            "db": {
                "image": "postgres:14",
                "environment": {"POSTGRES_PASSWORD": "secret"},
                "restart": "unless-stopped"
            }
        }
    },
    "ports": [5432],
    "volumes": ["/data"],
    "environment": {"DB_NAME": "testdb"},
    "min_memory": 512,
    "min_cpu": 2,
    "tags": ["database", "postgres", "sql"],
    "author": "DB Author",
    "website": "https://db.example.com"
}

# Invalid catalog data (missing required fields)
INVALID_APP_DATA = {
    "id": "invalid-app",
    "name": "Invalid Application",
    # Missing required fields: version, description, category, etc.
}


class CatalogServiceTestCase(TestCase):
    """Test cases for the CatalogService."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test catalog files
        self.temp_dir = tempfile.mkdtemp()
        self.catalog_path = Path(self.temp_dir)
        
        # Create test JSON files
        self.valid_file = self.catalog_path / "test-app.json"
        with open(self.valid_file, 'w') as f:
            json.dump(VALID_APP_DATA, f)
        
        self.another_valid_file = self.catalog_path / "another-app.json"
        with open(self.another_valid_file, 'w') as f:
            json.dump(ANOTHER_VALID_APP, f)
        
        self.invalid_file = self.catalog_path / "invalid-app.json"
        with open(self.invalid_file, 'w') as f:
            json.dump(INVALID_APP_DATA, f)
        
        # Reset singleton state for testing
        CatalogService._instance = None
        CatalogService._initialized = False
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
        
        # Reset singleton state
        CatalogService._instance = None
        CatalogService._initialized = False
    
    @patch('apps.catalog.services.CatalogService._get_catalog_path')
    def test_singleton_pattern(self, mock_get_path):
        """Test that CatalogService is a singleton."""
        mock_get_path.return_value = self.catalog_path
        
        service1 = CatalogService()
        service2 = CatalogService()
        
        self.assertIs(service1, service2)
    
    @patch('apps.catalog.services.CatalogService._get_catalog_path')
    def test_load_valid_apps(self, mock_get_path):
        """Test loading valid catalog files."""
        mock_get_path.return_value = self.catalog_path
        
        service = CatalogService()
        apps = service.get_all_apps()
        
        # Should load 2 valid apps, skip 1 invalid
        self.assertEqual(len(apps), 2)
        
        # Check that apps are sorted by name
        self.assertEqual(apps[0].id, "another-app")
        self.assertEqual(apps[1].id, "test-app")
    
    @patch('apps.catalog.services.CatalogService._get_catalog_path')
    def test_get_app_by_id_existing(self, mock_get_path):
        """Test getting an existing app by ID."""
        mock_get_path.return_value = self.catalog_path
        
        service = CatalogService()
        app = service.get_app_by_id("test-app")
        
        self.assertIsNotNone(app)
        self.assertEqual(app.id, "test-app")
        self.assertEqual(app.name, "Test Application")
        self.assertEqual(app.category, "Testing")
    
    @patch('apps.catalog.services.CatalogService._get_catalog_path')
    def test_get_app_by_id_nonexistent(self, mock_get_path):
        """Test getting a non-existent app by ID."""
        mock_get_path.return_value = self.catalog_path
        
        service = CatalogService()
        app = service.get_app_by_id("nonexistent-app")
        
        self.assertIsNone(app)
    
    @patch('apps.catalog.services.CatalogService._get_catalog_path')
    def test_get_categories(self, mock_get_path):
        """Test getting unique categories."""
        mock_get_path.return_value = self.catalog_path
        
        service = CatalogService()
        categories = service.get_categories()
        
        # Should have 2 unique categories
        self.assertEqual(len(categories), 2)
        self.assertIn("Testing", categories)
        self.assertIn("Database", categories)
        
        # Should be sorted
        self.assertEqual(categories, sorted(categories))
    
    @patch('apps.catalog.services.CatalogService._get_catalog_path')
    def test_search_apps_by_name(self, mock_get_path):
        """Test searching apps by name."""
        mock_get_path.return_value = self.catalog_path
        
        service = CatalogService()
        results = service.search_apps("Test")
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, "test-app")
    
    @patch('apps.catalog.services.CatalogService._get_catalog_path')
    def test_search_apps_by_description(self, mock_get_path):
        """Test searching apps by description."""
        mock_get_path.return_value = self.catalog_path
        
        service = CatalogService()
        results = service.search_apps("different category")
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, "another-app")
    
    @patch('apps.catalog.services.CatalogService._get_catalog_path')
    def test_search_apps_by_tag(self, mock_get_path):
        """Test searching apps by tag."""
        mock_get_path.return_value = self.catalog_path
        
        service = CatalogService()
        results = service.search_apps("postgres")
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, "another-app")
    
    @patch('apps.catalog.services.CatalogService._get_catalog_path')
    def test_search_apps_case_insensitive(self, mock_get_path):
        """Test that search is case-insensitive."""
        mock_get_path.return_value = self.catalog_path
        
        service = CatalogService()
        results_lower = service.search_apps("test")
        results_upper = service.search_apps("TEST")
        results_mixed = service.search_apps("TeSt")
        
        self.assertEqual(len(results_lower), 1)
        self.assertEqual(len(results_upper), 1)
        self.assertEqual(len(results_mixed), 1)
    
    @patch('apps.catalog.services.CatalogService._get_catalog_path')
    def test_search_apps_no_results(self, mock_get_path):
        """Test searching with no matching results."""
        mock_get_path.return_value = self.catalog_path
        
        service = CatalogService()
        results = service.search_apps("nonexistent")
        
        self.assertEqual(len(results), 0)
    
    @patch('apps.catalog.services.CatalogService._get_catalog_path')
    def test_search_apps_empty_query(self, mock_get_path):
        """Test searching with empty query returns all apps."""
        mock_get_path.return_value = self.catalog_path
        
        service = CatalogService()
        results = service.search_apps("")
        
        self.assertEqual(len(results), 2)
    
    @patch('apps.catalog.services.CatalogService._get_catalog_path')
    def test_filter_by_category(self, mock_get_path):
        """Test filtering apps by category."""
        mock_get_path.return_value = self.catalog_path
        
        service = CatalogService()
        
        testing_apps = service.filter_by_category("Testing")
        self.assertEqual(len(testing_apps), 1)
        self.assertEqual(testing_apps[0].id, "test-app")
        
        database_apps = service.filter_by_category("Database")
        self.assertEqual(len(database_apps), 1)
        self.assertEqual(database_apps[0].id, "another-app")
    
    @patch('apps.catalog.services.CatalogService._get_catalog_path')
    def test_filter_by_category_case_insensitive(self, mock_get_path):
        """Test that category filtering is case-insensitive."""
        mock_get_path.return_value = self.catalog_path
        
        service = CatalogService()
        
        results_lower = service.filter_by_category("testing")
        results_upper = service.filter_by_category("TESTING")
        
        self.assertEqual(len(results_lower), 1)
        self.assertEqual(len(results_upper), 1)
    
    @patch('apps.catalog.services.CatalogService._get_catalog_path')
    def test_get_stats(self, mock_get_path):
        """Test getting catalog statistics."""
        mock_get_path.return_value = self.catalog_path
        
        service = CatalogService()
        stats = service.get_stats()
        
        self.assertEqual(stats['total_apps'], 2)
        self.assertEqual(stats['total_categories'], 2)
    
    @patch('apps.catalog.services.CatalogService._get_catalog_path')
    def test_reload(self, mock_get_path):
        """Test reloading the catalog."""
        mock_get_path.return_value = self.catalog_path
        
        service = CatalogService()
        initial_count = len(service.get_all_apps())
        
        # Add a new valid app file
        new_app_data = VALID_APP_DATA.copy()
        new_app_data['id'] = 'new-app'
        new_app_data['name'] = 'New Application'
        
        new_file = self.catalog_path / "new-app.json"
        with open(new_file, 'w') as f:
            json.dump(new_app_data, f)
        
        # Reload catalog
        service.reload()
        
        # Should have one more app
        self.assertEqual(len(service.get_all_apps()), initial_count + 1)
        self.assertIsNotNone(service.get_app_by_id('new-app'))


class CatalogAPITestCase(TestCase):
    """Test cases for the Catalog API endpoints."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test catalog files
        self.temp_dir = tempfile.mkdtemp()
        self.catalog_path = Path(self.temp_dir)
        
        # Create test JSON files
        with open(self.catalog_path / "test-app.json", 'w') as f:
            json.dump(VALID_APP_DATA, f)
        
        with open(self.catalog_path / "another-app.json", 'w') as f:
            json.dump(ANOTHER_VALID_APP, f)
        
        # Reset singleton and initialize with test data
        CatalogService._instance = None
        CatalogService._initialized = False
        
        with patch('apps.catalog.services.CatalogService._get_catalog_path') as mock_path:
            mock_path.return_value = self.catalog_path
            self.service = CatalogService()
        
        # Create test client
        self.client = TestClient(router)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
        
        # Reset singleton state
        CatalogService._instance = None
        CatalogService._initialized = False
    
    def test_list_apps_endpoint(self):
        """Test the list apps endpoint."""
        response = self.client.get("/")
        
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['total'], 2)
        self.assertEqual(len(data['applications']), 2)
        
        # Check sorting
        self.assertEqual(data['applications'][0]['id'], 'another-app')
        self.assertEqual(data['applications'][1]['id'], 'test-app')
    
    def test_get_app_by_id_existing(self):
        """Test getting an existing app by ID."""
        response = self.client.get("/test-app")
        
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['id'], 'test-app')
        self.assertEqual(data['name'], 'Test Application')
    
    def test_get_app_by_id_nonexistent(self):
        """Test getting a non-existent app returns 404."""
        response = self.client.get("/nonexistent-app")
        
        self.assertEqual(response.status_code, 404)
        
        data = response.json()
        self.assertIn("not found", data['detail'].lower())
    
    def test_list_categories_endpoint(self):
        """Test the list categories endpoint."""
        response = self.client.get("/categories")
        
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(len(data['categories']), 2)
        self.assertIn('Testing', data['categories'])
        self.assertIn('Database', data['categories'])
    
    def test_search_endpoint(self):
        """Test the search endpoint."""
        response = self.client.get("/search?q=test")
        
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['total'], 1)
        self.assertEqual(data['applications'][0]['id'], 'test-app')
    
    def test_search_endpoint_empty_query(self):
        """Test search with empty query returns all apps."""
        response = self.client.get("/search?q=")
        
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['total'], 2)
    
    def test_filter_by_category_endpoint(self):
        """Test the filter by category endpoint."""
        response = self.client.get("/category/Testing")
        
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['total'], 1)
        self.assertEqual(data['applications'][0]['id'], 'test-app')
    
    def test_stats_endpoint(self):
        """Test the stats endpoint."""
        response = self.client.get("/stats")
        
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['total_apps'], 2)
        self.assertEqual(data['total_categories'], 2)
    
    def test_reload_endpoint(self):
        """Test the reload endpoint."""
        response = self.client.post("/reload")
        
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('message', data)
        self.assertIn('stats', data)
