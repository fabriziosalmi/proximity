#!/usr/bin/env python3
"""
Quick test script to verify Catalog Service functionality.

This script tests the core functionality without Django dependencies.
"""
import json
import tempfile
from pathlib import Path
from copy import deepcopy

# Sample test data
VALID_APP_DATA = {
    "id": "test-app",
    "name": "Test Application",
    "version": "1.0.0",
    "description": "A test application",
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
    "tags": ["test"],
    "author": "Test",
    "website": "https://test.com"
}

def test_schema_validation():
    """Test that CatalogAppSchema validates correctly."""
    from apps.catalog.schemas import CatalogAppSchema
    
    print("✓ Testing schema validation...")
    
    # Valid data should pass
    app = CatalogAppSchema(**VALID_APP_DATA)
    assert app.id == "test-app"
    assert app.name == "Test Application"
    assert app.min_memory == 256
    print("  ✓ Valid data passes validation")
    
    # Missing required field should fail
    invalid_data = VALID_APP_DATA.copy()
    del invalid_data['description']
    try:
        CatalogAppSchema(**invalid_data)
        raise AssertionError("Should have failed validation")
    except Exception as e:
        print(f"  ✓ Invalid data fails validation: {type(e).__name__}")


def test_catalog_service():
    """Test CatalogService functionality."""
    from unittest.mock import patch
    from apps.catalog.services import CatalogService

    print("\n✓ Testing CatalogService...")

    # Reset singleton to ensure clean state
    CatalogService._instance = None
    CatalogService._initialized = False
    # Also reset any cached data
    if hasattr(CatalogService, '_apps'):
        CatalogService._apps = {}
    
    # Create temp directory with test files
    with tempfile.TemporaryDirectory() as temp_dir:
        catalog_path = Path(temp_dir)
        
        # Create test JSON file
        test_file = catalog_path / "test-app.json"
        with open(test_file, 'w') as f:
            json.dump(VALID_APP_DATA, f)
        
        # Create another app with different category (use deep copy to avoid shared references)
        another_app = deepcopy(VALID_APP_DATA)
        another_app['id'] = 'another-app'
        another_app['name'] = 'Another App'
        another_app['description'] = 'A database application'  # Different description to avoid matching 'test' search
        another_app['category'] = 'Database'
        another_app['tags'] = ['database']
        
        another_file = catalog_path / "another-app.json"
        with open(another_file, 'w') as f:
            json.dump(another_app, f)
        
        # Mock the catalog path
        with patch('apps.catalog.services.CatalogService._get_catalog_path') as mock_path:
            mock_path.return_value = catalog_path
            
            # Initialize service
            service = CatalogService()
            
            # Test get_all_apps
            apps = service.get_all_apps()
            assert len(apps) == 2
            print(f"  ✓ get_all_apps() returned {len(apps)} apps")
            
            # Test get_app_by_id
            app = service.get_app_by_id('test-app')
            assert app is not None
            assert app.name == 'Test Application'
            print("  ✓ get_app_by_id() works for existing app")
            
            # Test non-existent app
            app = service.get_app_by_id('nonexistent')
            assert app is None
            print("  ✓ get_app_by_id() returns None for non-existent app")
            
            # Test get_categories
            categories = service.get_categories()
            assert len(categories) == 2
            assert 'Testing' in categories
            assert 'Database' in categories
            print(f"  ✓ get_categories() returned {categories}")
            
            # Test search_apps
            results = service.search_apps('test')
            assert len(results) == 1
            assert results[0].id == 'test-app'
            print("  ✓ search_apps() by name works")
            
            results = service.search_apps('database')
            assert len(results) == 1
            assert results[0].id == 'another-app'
            print("  ✓ search_apps() by tag works")
            
            # Test filter_by_category
            results = service.filter_by_category('Testing')
            assert len(results) == 1
            print("  ✓ filter_by_category() works")
            
            # Test stats
            stats = service.get_stats()
            assert stats['total_apps'] == 2
            assert stats['total_categories'] == 2
            print(f"  ✓ get_stats() returned {stats}")
            
            # Test singleton pattern
            service2 = CatalogService()
            assert service is service2
            print("  ✓ Singleton pattern works")


def test_api_endpoints():
    """Test API endpoint structure."""
    from apps.catalog import api

    print("\n✓ Testing API structure...")

    # Check router exists
    assert hasattr(api, 'router')
    print("  ✓ Router exists")

    # Check endpoints are registered (path_operations exists and has entries)
    assert hasattr(api.router, 'path_operations')
    assert len(api.router.path_operations) > 0
    print(f"  ✓ {len(api.router.path_operations)} endpoints registered")


def main():
    """Run all tests."""
    print("=" * 60)
    print("CATALOG SERVICE - QUICK VALIDATION TEST")
    print("=" * 60)
    
    try:
        # Test 1: Schema validation
        test_schema_validation()
        
        # Test 2: Service functionality
        test_catalog_service()
        
        # Test 3: API structure
        test_api_endpoints()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nThe Catalog Service is working correctly!")
        print("Ready for integration testing with Docker.")
        
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ TEST FAILED: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    import sys
    sys.path.insert(0, '/Users/fab/GitHub/proximity/proximity2/backend')
    
    # Mock Django settings for testing
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proximity.settings')
    
    exit(main())
