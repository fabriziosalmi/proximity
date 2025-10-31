"""
Catalog service for loading and managing application definitions.

This service reads JSON files from the catalog directory and provides
methods to query the catalog data.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from django.conf import settings
from pydantic import ValidationError

from .schemas import CatalogAppSchema


logger = logging.getLogger(__name__)


class CatalogService:
    """
    Singleton service for managing the application catalog.

    This service loads all catalog JSON files from disk into memory
    on initialization and provides methods to query the catalog.
    """

    _instance: Optional["CatalogService"] = None
    _initialized: bool = False

    def __new__(cls):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """
        Initialize the catalog service.

        Loads all JSON files from the catalog directory and validates them
        against the CatalogAppSchema.
        """
        # Only initialize once (singleton pattern)
        if CatalogService._initialized:
            return

        self._apps: Dict[str, CatalogAppSchema] = {}
        self._catalog_path: Path = self._get_catalog_path()

        logger.info(f"Initializing CatalogService from {self._catalog_path}")
        self._load_catalog()

        CatalogService._initialized = True
        logger.info(f"CatalogService initialized with {len(self._apps)} applications")

    def _get_catalog_path(self) -> Path:
        """
        Get the path to the catalog directory.

        Returns:
            Path to the catalog_data directory
        """
        # Try to get from settings first, fall back to default
        if hasattr(settings, "CATALOG_DATA_PATH"):
            return Path(settings.CATALOG_DATA_PATH)

        # Default: catalog_data/ in project root
        return settings.BASE_DIR / "catalog_data"

    def _load_catalog(self) -> None:
        """
        Load all JSON files from the catalog directory.

        Validates each file against the CatalogAppSchema and stores
        valid applications in memory. Invalid files are logged and skipped.
        """
        if not self._catalog_path.exists():
            logger.warning(f"Catalog directory does not exist: {self._catalog_path}")
            logger.info("Creating catalog directory...")
            self._catalog_path.mkdir(parents=True, exist_ok=True)
            return

        if not self._catalog_path.is_dir():
            logger.error(f"Catalog path is not a directory: {self._catalog_path}")
            return

        # Find all JSON files
        json_files = list(self._catalog_path.glob("*.json"))

        if not json_files:
            logger.warning(f"No JSON files found in {self._catalog_path}")
            return

        logger.info(f"Found {len(json_files)} JSON files to load")

        # Load and validate each file
        for json_file in json_files:
            try:
                self._load_app_file(json_file)
            except Exception as e:
                logger.error(f"Failed to load {json_file.name}: {str(e)}")
                continue

    def _load_app_file(self, file_path: Path) -> None:
        """
        Load and validate a single catalog JSON file.

        Args:
            file_path: Path to the JSON file

        Raises:
            Exception: If the file cannot be read or validated
        """
        logger.debug(f"Loading {file_path.name}")

        # Read JSON file
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Validate against schema
        try:
            app = CatalogAppSchema(**data)
        except ValidationError as e:
            logger.error(f"Validation error in {file_path.name}: {e}")
            raise

        # Check for duplicate IDs
        if app.id in self._apps:
            logger.warning(
                f"Duplicate app ID '{app.id}' in {file_path.name}, overwriting previous entry"
            )

        # Store in memory
        self._apps[app.id] = app
        logger.debug(f"Loaded {app.name} (ID: {app.id})")

    def get_all_apps(self) -> List[CatalogAppSchema]:
        """
        Get all applications from the catalog.

        Returns:
            List of all catalog applications, sorted by name
        """
        apps = list(self._apps.values())
        return sorted(apps, key=lambda x: x.name.lower())

    def get_app_by_id(self, app_id: str) -> Optional[CatalogAppSchema]:
        """
        Get a single application by its ID.

        Args:
            app_id: The application ID

        Returns:
            The application if found, None otherwise
        """
        return self._apps.get(app_id)

    def get_categories(self) -> List[str]:
        """
        Get all unique categories from the catalog.

        Returns:
            Sorted list of unique category names
        """
        categories = {app.category for app in self._apps.values()}
        return sorted(categories)

    def search_apps(self, query: str) -> List[CatalogAppSchema]:
        """
        Search for applications matching the query.

        Searches in:
        - Application name
        - Application description
        - Application tags

        Args:
            query: Search query string (case-insensitive)

        Returns:
            List of matching applications, sorted by name
        """
        if not query:
            return self.get_all_apps()

        query_lower = query.lower()
        matching_apps = []

        for app in self._apps.values():
            # Search in name
            if query_lower in app.name.lower():
                matching_apps.append(app)
                continue

            # Search in description
            if query_lower in app.description.lower():
                matching_apps.append(app)
                continue

            # Search in tags
            if any(query_lower in tag.lower() for tag in app.tags):
                matching_apps.append(app)
                continue

        return sorted(matching_apps, key=lambda x: x.name.lower())

    def filter_by_category(self, category: str) -> List[CatalogAppSchema]:
        """
        Filter applications by category.

        Args:
            category: The category name

        Returns:
            List of applications in the category, sorted by name
        """
        matching_apps = [
            app for app in self._apps.values() if app.category.lower() == category.lower()
        ]
        return sorted(matching_apps, key=lambda x: x.name.lower())

    def reload(self) -> None:
        """
        Reload the catalog from disk.

        This can be called to refresh the catalog without restarting
        the application.
        """
        logger.info("Reloading catalog...")
        self._apps.clear()
        self._load_catalog()
        logger.info(f"Catalog reloaded with {len(self._apps)} applications")

    def get_stats(self) -> Dict[str, int]:
        """
        Get statistics about the catalog.

        Returns:
            Dictionary with catalog statistics
        """
        return {
            "total_apps": len(self._apps),
            "total_categories": len(self.get_categories()),
        }


# Singleton instance
catalog_service = CatalogService()
