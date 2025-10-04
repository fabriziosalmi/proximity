"""
Utility module for generating test data.

Provides functions for creating unique, randomized test data
to avoid collisions in concurrent test runs.
"""

import random
import string
from datetime import datetime
from faker import Faker

fake = Faker()


def generate_random_string(length: int = 8) -> str:
    """
    Generate a random alphanumeric string.
    
    Args:
        length: Length of the string to generate
    
    Returns:
        Random string of specified length
    """
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


def generate_timestamp() -> str:
    """
    Generate a timestamp string for unique identifiers.
    
    Returns:
        Timestamp in format YYYYMMDD_HHMMSS
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def generate_test_user() -> dict:
    """
    Generate a unique test user with randomized credentials.
    
    Returns:
        Dictionary with username, password, and email
    """
    timestamp = generate_timestamp()
    random_suffix = generate_random_string(4)
    
    return {
        "username": f"testuser_{timestamp}_{random_suffix}",
        "password": f"Test{generate_random_string(12)}!",
        "email": f"test_{timestamp}_{random_suffix}@example.com"
    }


def generate_hostname(app_name: str) -> str:
    """
    Generate a unique hostname for application deployment.
    
    Args:
        app_name: Base application name (e.g., 'nginx', 'wordpress')
    
    Returns:
        Unique hostname like 'nginx-e2e-20231204-ab12cd'
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M")
    random_suffix = generate_random_string(6)
    
    return f"{app_name}-e2e-{timestamp}-{random_suffix}"


def generate_port(min_port: int = 8000, max_port: int = 9000) -> int:
    """
    Generate a random port number.
    
    Args:
        min_port: Minimum port number
        max_port: Maximum port number
    
    Returns:
        Random port number
    """
    return random.randint(min_port, max_port)


def sanitize_hostname(hostname: str) -> str:
    """
    Sanitize a hostname to ensure it's valid.
    
    Args:
        hostname: Raw hostname string
    
    Returns:
        Sanitized hostname (lowercase, alphanumeric and hyphens only)
    """
    # Convert to lowercase
    hostname = hostname.lower()
    
    # Replace spaces and underscores with hyphens
    hostname = hostname.replace(' ', '-').replace('_', '-')
    
    # Remove any non-alphanumeric characters except hyphens
    hostname = ''.join(c for c in hostname if c.isalnum() or c == '-')
    
    # Remove leading/trailing hyphens
    hostname = hostname.strip('-')
    
    # Limit length to 63 characters (DNS label limit)
    hostname = hostname[:63]
    
    return hostname
