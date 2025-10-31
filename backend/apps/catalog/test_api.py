import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken


User = get_user_model()


@pytest.fixture
def sample_user():
    """Create a test user for authentication."""
    user, _ = User.objects.get_or_create(
        username="testuser",
        defaults={
            "email": "test@example.com",
        },
    )
    user.set_password("testpass123")
    user.save()
    return user


@pytest.mark.django_db
def test_catalog_api_returns_data(client: APIClient, sample_user):
    """
    Verifies that the GET /api/catalog/ endpoint correctly loads
    and returns application data with proper authentication.
    """
    # Authenticate the client with JWT cookie
    access_token = AccessToken.for_user(sample_user)
    client.cookies["proximity-auth-cookie"] = str(access_token)

    # Call the catalog API endpoint
    response = client.get("/api/catalog/")

    # Verify successful response
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    response_data = response.json()

    # The endpoint returns a dictionary with an 'applications' key
    assert "applications" in response_data, "Response missing 'applications' key"
    applications = response_data["applications"]

    assert isinstance(applications, list), "Applications should be a list"
    assert len(applications) > 0, "Should return at least one application"

    # Verify the structure of the first application
    first_app = applications[0]
    required_fields = ["id", "name", "description", "category", "icon"]
    for field in required_fields:
        assert field in first_app, f"Application missing required field: {field}"
