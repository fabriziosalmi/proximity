"""
Tests for the dj-rest-auth API endpoints.

These are integration tests that verify the complete authentication flow,
including login, logout, and accessing protected user data.
"""

import pytest
from django.urls import reverse
from apps.core.models import User

# Mark the entire module to use the database
pytestmark = pytest.mark.django_db


@pytest.fixture
def test_user(db):
    """Fixture to create a standard test user."""
    user, _ = User.objects.get_or_create(
        username="testuser",
        defaults={
            "email": "test@example.com",
        },
    )
    user.set_password("testpassword123")
    user.save()
    return user


class TestAuthAPI:
    """Test suite for the authentication API endpoints."""

    def test_login_success(self, client, test_user):
        """Verify that a user can successfully log in and receive auth cookies."""
        login_url = reverse("rest_login")
        data = {"username": "testuser", "password": "testpassword123"}

        response = client.post(login_url, data, format="json")

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["user"]["username"] == test_user.username
        # Verify auth cookie is set in response
        # Note: Cookie attributes like 'httponly' are set by the server and enforced at the HTTP level
        assert "proximity-auth-cookie" in response.cookies

    def test_login_failure_bad_credentials(self, client, test_user):
        """Verify that login fails with incorrect credentials."""
        login_url = reverse("rest_login")
        data = {"username": "testuser", "password": "wrongpassword"}

        response = client.post(login_url, data, format="json")

        assert response.status_code == 400
        assert "non_field_errors" in response.json()
        assert "proximity-auth-cookie" not in response.cookies

    def test_user_endpoint_unauthenticated(self, client):
        """Verify that the user details endpoint is protected."""
        user_url = reverse("rest_user_details")
        response = client.get(user_url)

        # We expect 401 because our Ninja API is now globally protected
        assert response.status_code == 401

    def test_user_endpoint_authenticated(self, client, test_user):
        """Verify that an authenticated user can fetch their details."""
        # 1. Log in by POSTing to the login endpoint to get the auth cookie.
        login_url = reverse("rest_login")
        login_data = {"username": "testuser", "password": "testpassword123"}
        login_response = client.post(login_url, login_data, format="json")
        assert login_response.status_code == 200

        # 2. Access the protected user endpoint. The test client now has the cookie.
        user_url = reverse("rest_user_details")
        response = client.get(user_url)

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["username"] == test_user.username
        assert response_data["pk"] == test_user.pk

    def test_logout_success(self, client, test_user):
        """Verify that logging out clears the authentication cookie."""
        # 1. Log in to establish the session and get the cookie.
        login_url = reverse("rest_login")
        login_data = {"username": "testuser", "password": "testpassword123"}
        login_response = client.post(login_url, login_data, format="json")
        assert login_response.status_code == 200
        assert "proximity-auth-cookie" in client.cookies

        # 2. Log out.
        logout_url = reverse("rest_logout")
        logout_response = client.post(logout_url)
        assert logout_response.status_code == 200

        # The test client's cookie jar should now reflect the invalidated cookie.
        # A more robust check is to ensure a protected endpoint is no longer accessible.

        # 4. Verify we are logged out by trying to access a protected endpoint again.
        user_url = reverse("rest_user_details")
        final_response = client.get(user_url)
        assert final_response.status_code == 401
