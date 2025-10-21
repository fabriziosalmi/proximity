"""
Unit tests for JWT authentication.
"""
import pytest
import jwt
from datetime import datetime, timedelta
from django.conf import settings
from apps.core.auth import JWTAuth


def create_jwt_token(user, token_type='access'):
    """Helper function to create JWT tokens for testing."""
    if token_type == 'access':
        lifetime = timedelta(minutes=30)
    else:
        lifetime = timedelta(days=7)
    
    payload = {
        'user_id': user.id,
        'username': user.username,
        'token_type': token_type,
        'exp': datetime.utcnow() + lifetime,
        'iat': datetime.utcnow(),
    }
    
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


@pytest.mark.django_db
class TestJWTAuth:
    """Test JWT authentication."""
    
    def test_create_jwt_token(self, test_user):
        """Test creating a JWT token."""
        token = create_jwt_token(test_user)
        
        assert token is not None
        assert isinstance(token, str)
        
        # Decode and verify
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        assert payload['user_id'] == test_user.id
        assert payload['username'] == test_user.username
    
    def test_jwt_token_expiration(self, test_user):
        """Test JWT token expiration."""
        token = create_jwt_token(test_user)
        
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        exp_time = datetime.fromtimestamp(payload['exp'])
        
        # Token should expire in the future
        assert exp_time > datetime.now()
    
    def test_jwt_auth_valid_token(self, test_user):
        """Test JWT authentication with valid token."""
        token = create_jwt_token(test_user)
        
        auth = JWTAuth()
        
        # Mock request with token
        class MockRequest:
            headers = {'Authorization': f'Bearer {token}'}
        
        user = auth.authenticate(MockRequest(), token)
        assert user == test_user
    
    def test_jwt_auth_invalid_token(self):
        """Test JWT authentication with invalid token."""
        auth = JWTAuth()
        
        class MockRequest:
            headers = {'Authorization': 'Bearer invalid_token'}
        
        # Should return None for invalid token
        user = auth.authenticate(MockRequest(), 'invalid_token')
        assert user is None
    
    def test_jwt_auth_expired_token(self, test_user):
        """Test JWT authentication with expired token."""
        # Create token that expires immediately
        payload = {
            'user_id': test_user.id,
            'username': test_user.username,
            'exp': datetime.utcnow() - timedelta(hours=1)  # Expired 1 hour ago
        }
        expired_token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        
        auth = JWTAuth()
        
        class MockRequest:
            headers = {'Authorization': f'Bearer {expired_token}'}
        
        # Should return None for expired token
        user = auth.authenticate(MockRequest(), expired_token)
        assert user is None
    
    def test_jwt_auth_missing_token(self):
        """Test JWT authentication with missing token."""
        auth = JWTAuth()
        
        class MockRequest:
            headers = {}
        
        # Should return None for missing token
        user = auth.authenticate(MockRequest(), '')
        assert user is None


@pytest.mark.django_db
class TestPasswordHashing:
    """Test password hashing and verification."""
    
    def test_password_is_hashed(self, test_user):
        """Test that passwords are stored hashed."""
        # The raw password should not be stored
        assert test_user.password != 'testpass123'
        
        # Should be hashed
        assert test_user.password.startswith('pbkdf2_sha256$')
    
    def test_check_password_correct(self, test_user):
        """Test checking correct password."""
        assert test_user.check_password('testpass123') is True
    
    def test_check_password_incorrect(self, test_user):
        """Test checking incorrect password."""
        assert test_user.check_password('wrongpassword') is False
    
    def test_set_password(self, test_user):
        """Test changing user password."""
        test_user.set_password('newpassword123')
        test_user.save()
        
        # Old password should not work
        test_user.refresh_from_db()
        assert test_user.check_password('testpass123') is False
        
        # New password should work
        assert test_user.check_password('newpassword123') is True


@pytest.mark.django_db
class TestUserPermissions:
    """Test user permissions and ownership."""
    
    def test_user_can_access_own_applications(self, test_user, test_application):
        """Test that user can access their own applications."""
        assert test_application.owner == test_user
        
        # User's applications
        user_apps = test_user.applications.all()
        assert test_application in user_apps
    
    def test_user_cannot_access_other_applications(self, test_user, admin_user, proxmox_host):
        """Test that user cannot access other users' applications."""
        from apps.applications.models import Application
        
        # Create app owned by admin
        admin_app = Application.objects.create(
            id='admin-app',
            catalog_id='nginx',
            name='Admin App',
            hostname='admin.local',
            host=proxmox_host,
            node='pve',
            owner=admin_user
        )
        
        # test_user should not have access
        user_apps = test_user.applications.all()
        assert admin_app not in user_apps
    
    def test_superuser_is_staff(self, admin_user):
        """Test that superuser has staff privileges."""
        assert admin_user.is_staff is True
        assert admin_user.is_superuser is True
    
    def test_regular_user_not_staff(self, test_user):
        """Test that regular user doesn't have staff privileges."""
        assert test_user.is_staff is False
        assert test_user.is_superuser is False
