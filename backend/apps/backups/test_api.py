"""
Integration tests for Backup API endpoints.

These tests verify HTTP endpoints, status codes, and authentication.
"""
import pytest
from unittest.mock import patch
from django.test import Client

from apps.backups.models import Backup
from apps.applications.models import Application


@pytest.mark.django_db
class TestBackupAPIEndpoints:
    """Integration tests for backup API endpoints."""
    
    def test_list_backups_unauthorized(self, client):
        """Test that listing backups requires authentication."""
        response = client.get('/api/apps/test-app-id/backups')
        assert response.status_code == 401
    
    def test_list_backups_empty(self, auth_client, sample_application):
        """Test listing backups when none exist."""
        response = auth_client.get(f'/api/apps/{sample_application.id}/backups')
        assert response.status_code == 200
        
        data = response.json()
        assert data['total'] == 0
        assert len(data['backups']) == 0
    
    def test_list_backups_with_data(
        self,
        auth_client,
        sample_application,
        sample_backup
    ):
        """Test listing backups with existing data."""
        response = auth_client.get(f'/api/apps/{sample_application.id}/backups')
        assert response.status_code == 200
        
        data = response.json()
        assert data['total'] == 1
        assert len(data['backups']) == 1
        
        backup_data = data['backups'][0]
        assert backup_data['id'] == sample_backup.id
        assert backup_data['file_name'] == sample_backup.file_name
        assert backup_data['status'] == sample_backup.status
    
    def test_list_backups_other_user_app(
        self,
        auth_client,
        other_user_application
    ):
        """Test that users cannot list backups for other users' apps."""
        response = auth_client.get(f'/api/apps/{other_user_application.id}/backups')
        assert response.status_code == 404
    
    def test_create_backup_success(self, auth_client, sample_application):
        """Test creating a backup."""
        with patch('apps.backups.api.create_backup_task') as mock_task:
            mock_task.delay.return_value = None
            
            response = auth_client.post(
                f'/api/apps/{sample_application.id}/backups',
                json={
                    'backup_type': 'snapshot',
                    'compression': 'zstd'
                },
                content_type='application/json'
            )
            
            assert response.status_code == 202
            
            data = response.json()
            assert 'id' in data
            assert data['status'] == 'creating'
            assert 'started' in data['message'].lower()
            
            # Verify backup record was created
            backup = Backup.objects.get(id=data['id'])
            assert backup.application == sample_application
            assert backup.status == 'creating'
            assert backup.backup_type == 'snapshot'
            assert backup.compression == 'zstd'
            
            # Verify task was triggered
            mock_task.delay.assert_called_once()
    
    def test_create_backup_unauthorized(self, client, sample_application):
        """Test that creating a backup requires authentication."""
        response = client.post(
            f'/api/apps/{sample_application.id}/backups',
            json={'backup_type': 'snapshot'},
            content_type='application/json'
        )
        assert response.status_code == 401
    
    def test_create_backup_app_not_found(self, auth_client):
        """Test creating backup for non-existent app."""
        response = auth_client.post(
            '/api/apps/non-existent/backups',
            json={'backup_type': 'snapshot'},
            content_type='application/json'
        )
        assert response.status_code == 404
    
    def test_create_backup_app_in_error_state(
        self,
        auth_client,
        sample_application
    ):
        """Test that backup cannot be created for app in error state."""
        sample_application.status = 'error'
        sample_application.save()

        response = auth_client.post(
            f'/api/apps/{sample_application.id}/backups',
            json={'backup_type': 'snapshot'},
            content_type='application/json'
        )
        # Verify the request is rejected with proper error status
        assert response.status_code == 400
    
    def test_create_backup_already_in_progress(
        self,
        auth_client,
        sample_application
    ):
        """Test that only one backup can be in progress at a time."""
        # Create backup in progress
        Backup.objects.create(
            application=sample_application,
            file_name='test.tar.zst',
            status='creating'
        )

        response = auth_client.post(
            f'/api/apps/{sample_application.id}/backups',
            json={'backup_type': 'snapshot'},
            content_type='application/json'
        )
        # Verify conflict response when operation already in progress
        assert response.status_code == 409
    
    def test_get_backup_details(
        self,
        auth_client,
        sample_application,
        sample_backup
    ):
        """Test getting backup details."""
        response = auth_client.get(
            f'/api/apps/{sample_application.id}/backups/{sample_backup.id}'
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data['id'] == sample_backup.id
        assert data['file_name'] == sample_backup.file_name
        assert data['status'] == sample_backup.status
        assert data['size'] == sample_backup.size
    
    def test_get_backup_details_not_found(self, auth_client, sample_application):
        """Test getting details for non-existent backup."""
        response = auth_client.get(
            f'/api/apps/{sample_application.id}/backups/99999'
        )
        assert response.status_code == 404
    
    def test_restore_backup_success(
        self,
        auth_client,
        sample_application,
        sample_backup
    ):
        """Test restoring from a backup."""
        with patch('apps.backups.api.restore_backup_task') as mock_task:
            mock_task.delay.return_value = None
            
            response = auth_client.post(
                f'/api/apps/{sample_application.id}/backups/{sample_backup.id}/restore'
            )
            
            assert response.status_code == 202
            
            data = response.json()
            assert data['backup_id'] == sample_backup.id
            assert data['application_id'] == sample_application.id
            assert data['status'] == 'restoring'
            
            # Verify task was triggered
            mock_task.delay.assert_called_once_with(backup_id=sample_backup.id)
    
    def test_restore_backup_not_completed(
        self,
        auth_client,
        sample_application
    ):
        """Test that only completed backups can be restored."""
        # Create backup in creating state
        backup = Backup.objects.create(
            application=sample_application,
            file_name='test.tar.zst',
            status='creating'
        )

        response = auth_client.post(
            f'/api/apps/{sample_application.id}/backups/{backup.id}/restore'
        )
        # Verify bad request when backup is not completed
        assert response.status_code == 400
    
    def test_restore_backup_already_in_progress(
        self,
        auth_client,
        sample_application,
        sample_backup
    ):
        """Test that restore cannot start if operation already in progress."""
        # Create another backup in progress
        Backup.objects.create(
            application=sample_application,
            file_name='other.tar.zst',
            status='restoring'
        )

        response = auth_client.post(
            f'/api/apps/{sample_application.id}/backups/{sample_backup.id}/restore'
        )
        # Verify conflict when operation is already in progress
        assert response.status_code == 409
    
    def test_delete_backup_success(
        self,
        auth_client,
        sample_application,
        sample_backup
    ):
        """Test deleting a backup."""
        with patch('apps.backups.api.delete_backup_task') as mock_task:
            mock_task.delay.return_value = None
            
            response = auth_client.delete(
                f'/api/apps/{sample_application.id}/backups/{sample_backup.id}'
            )
            
            assert response.status_code == 202
            
            data = response.json()
            assert data['backup_id'] == sample_backup.id
            assert data['status'] == 'deleting'
            
            # Verify task was triggered
            mock_task.delay.assert_called_once_with(backup_id=sample_backup.id)
    
    def test_delete_backup_in_progress(
        self,
        auth_client,
        sample_application
    ):
        """Test that backups in progress cannot be deleted."""
        backup = Backup.objects.create(
            application=sample_application,
            file_name='test.tar.zst',
            status='creating'
        )

        response = auth_client.delete(
            f'/api/apps/{sample_application.id}/backups/{backup.id}'
        )
        # Verify conflict when backup is in progress
        assert response.status_code == 409
    
    def test_get_backup_stats(
        self,
        auth_client,
        sample_application,
        sample_backup
    ):
        """Test getting backup statistics."""
        # Create additional backups
        Backup.objects.create(
            application=sample_application,
            file_name='backup2.tar.zst',
            storage_name='local',
            status='completed',
            size=1073741824  # 1 GB
        )
        Backup.objects.create(
            application=sample_application,
            file_name='backup3.tar.zst',
            storage_name='local',
            status='failed'
        )
        
        response = auth_client.get(
            f'/api/apps/{sample_application.id}/backups/stats'
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data['total_backups'] == 3
        assert data['completed_backups'] == 2
        assert data['failed_backups'] == 1
        assert data['in_progress_backups'] == 0
        assert data['total_size_gb'] > 0
