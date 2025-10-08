"""
Test per l'endpoint /exec che esegue comandi nei container
"""
import pytest
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException


@pytest.mark.asyncio
class TestExecEndpoint:
    """Test per l'endpoint POST /api/v1/apps/{app_id}/exec"""
    
    async def test_execute_command_success(self, app_service, db_session):
        """Test esecuzione comando con successo"""
        from api.endpoints.apps import execute_command
        from models.app import App
        
        # Create test app
        app = App(
            id="test-app-01",
            name="Test App",
            hostname="test.example.com",
            node="pve",
            lxc_id=100,
            status="running"
        )
        db_session.add(app)
        await db_session.commit()
        
        # Mock proxmox service
        with patch('api.endpoints.apps.proxmox_service') as mock_proxmox:
            mock_proxmox.execute_in_container = AsyncMock(
                return_value="total 0\ndrwxr-xr-x 2 root root 4096 Oct  9 00:00 .\ndrwxr-xr-x 3 root root 4096 Oct  9 00:00 .."
            )
            
            # Execute command
            result = await execute_command(
                app_id="test-app-01",
                command_data={"command": "ls -la"},
                service=app_service,
                current_user={"id": 1, "username": "testuser"}
            )
            
            # Verify
            assert result["success"] is True
            assert "total 0" in result["output"]
            
            # Verify execute_in_container was called correctly
            mock_proxmox.execute_in_container.assert_called_once()
            call_args = mock_proxmox.execute_in_container.call_args
            assert call_args.args[0] == "pve"  # node
            assert call_args.args[1] == 100    # lxc_id
            assert "ls -la" in call_args.args[2]  # command contains our command
    
    async def test_execute_command_empty(self, app_service, db_session):
        """Test esecuzione comando vuoto restituisce errore"""
        from api.endpoints.apps import execute_command
        from models.app import App
        
        # Create test app
        app = App(
            id="test-app-02",
            name="Test App 2",
            hostname="test2.example.com",
            node="pve",
            lxc_id=101,
            status="running"
        )
        db_session.add(app)
        await db_session.commit()
        
        # Try to execute empty command
        with pytest.raises(HTTPException) as exc_info:
            await execute_command(
                app_id="test-app-02",
                command_data={"command": ""},
                service=app_service,
                current_user={"id": 1, "username": "testuser"}
            )
        
        assert exc_info.value.status_code == 400
        assert "Command is required" in str(exc_info.value.detail)
    
    async def test_execute_command_nonexistent_app(self, app_service, db_session):
        """Test esecuzione comando su app inesistente"""
        from api.endpoints.apps import execute_command
        
        # Try to execute command on non-existent app
        with pytest.raises(HTTPException) as exc_info:
            await execute_command(
                app_id="nonexistent-app",
                command_data={"command": "ls"},
                service=app_service,
                current_user={"id": 1, "username": "testuser"}
            )
        
        assert exc_info.value.status_code == 404
    
    async def test_execute_command_with_special_chars(self, app_service, db_session):
        """Test esecuzione comando con caratteri speciali"""
        from api.endpoints.apps import execute_command
        from models.app import App
        
        # Create test app
        app = App(
            id="test-app-03",
            name="Test App 3",
            hostname="test3.example.com",
            node="pve",
            lxc_id=102,
            status="running"
        )
        db_session.add(app)
        await db_session.commit()
        
        # Mock proxmox service
        with patch('api.endpoints.apps.proxmox_service') as mock_proxmox:
            mock_proxmox.execute_in_container = AsyncMock(
                return_value="/root\n"
            )
            
            # Execute command with pipe
            result = await execute_command(
                app_id="test-app-03",
                command_data={"command": "echo 'test' | wc -l"},
                service=app_service,
                current_user={"id": 1, "username": "testuser"}
            )
            
            # Verify
            assert result["success"] is True
            
            # Verify command was passed correctly
            call_args = mock_proxmox.execute_in_container.call_args
            assert "echo 'test' | wc -l" in call_args.args[2]
    
    async def test_execute_command_timeout(self, app_service, db_session):
        """Test esecuzione comando con timeout"""
        from api.endpoints.apps import execute_command
        from models.app import App
        
        # Create test app
        app = App(
            id="test-app-04",
            name="Test App 4",
            hostname="test4.example.com",
            node="pve",
            lxc_id=103,
            status="running"
        )
        db_session.add(app)
        await db_session.commit()
        
        # Mock proxmox service to raise timeout
        with patch('api.endpoints.apps.proxmox_service') as mock_proxmox:
            mock_proxmox.execute_in_container = AsyncMock(
                side_effect=TimeoutError("Command timed out")
            )
            
            # Execute command that times out
            result = await execute_command(
                app_id="test-app-04",
                command_data={"command": "sleep 100"},
                service=app_service,
                current_user={"id": 1, "username": "testuser"}
            )
            
            # Should return error as output
            assert result["success"] is False
            assert "timed out" in result["output"].lower() or "error" in result["output"].lower()
    
    async def test_execute_command_requires_auth(self, app_service, db_session):
        """Test che l'endpoint richieda autenticazione"""
        from api.endpoints.apps import execute_command
        from models.app import App
        
        # Create test app
        app = App(
            id="test-app-05",
            name="Test App 5",
            hostname="test5.example.com",
            node="pve",
            lxc_id=104,
            status="running"
        )
        db_session.add(app)
        await db_session.commit()
        
        # Try without user - should raise error
        # Note: In real scenario, this would be caught by FastAPI dependency
        # Here we test that the function expects current_user parameter
        import inspect
        sig = inspect.signature(execute_command)
        assert 'current_user' in sig.parameters
        
        # Verify it's required (has Depends)
        from fastapi import Depends
        param = sig.parameters['current_user']
        assert param.default != inspect.Parameter.empty  # Has default (Depends)


@pytest.mark.asyncio 
class TestTerminalFunctionality:
    """Test della funzionalità terminale completa"""
    
    async def test_common_commands(self, app_service, db_session):
        """Test comandi comuni del terminale"""
        from api.endpoints.apps import execute_command
        from models.app import App
        
        # Create test app
        app = App(
            id="test-terminal-01",
            name="Terminal Test",
            hostname="terminal.test.com",
            node="pve",
            lxc_id=110,
            status="running"
        )
        db_session.add(app)
        await db_session.commit()
        
        # Test common commands
        test_commands = [
            ("ls", "Should list files"),
            ("pwd", "Should show current directory"),
            ("echo 'hello'", "Should echo text"),
            ("whoami", "Should show current user"),
            ("date", "Should show date")
        ]
        
        for cmd, description in test_commands:
            with patch('api.endpoints.apps.proxmox_service') as mock_proxmox:
                mock_proxmox.execute_in_container = AsyncMock(
                    return_value=f"Output of {cmd}"
                )
                
                result = await execute_command(
                    app_id="test-terminal-01",
                    command_data={"command": cmd},
                    service=app_service,
                    current_user={"id": 1, "username": "testuser"}
                )
                
                assert result["success"] is True, f"{description} failed"
                assert f"Output of {cmd}" in result["output"]
