# ABOUTME: Test suite for the web server module
# ABOUTME: Verifies API endpoints, WebSocket connections, and orchestrator monitoring

import pytest
import asyncio
import json
import tempfile
import shutil
import os
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from datetime import datetime
import jwt

from fastapi.testclient import TestClient
from fastapi.websockets import WebSocketDisconnect
import httpx

from src.ralph_orchestrator.web.server import app, OrchestratorMonitor, register_orchestrator, unregister_orchestrator
from src.ralph_orchestrator.web.auth import AuthManager
from src.ralph_orchestrator.web.database import DatabaseManager


class TestOrchestratorMonitor:
    """Test suite for OrchestratorMonitor class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test data."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def monitor(self, temp_dir):
        """Create an OrchestratorMonitor instance for testing."""
        monitor = OrchestratorMonitor(data_dir=temp_dir, enable_auth=False)
        yield monitor
        # Cleanup
        monitor.orchestrators.clear()
    
    @pytest.fixture
    def mock_orchestrator(self):
        """Create a mock orchestrator instance."""
        mock = MagicMock()
        mock.id = 'test-orch-123'
        mock.prompt_file = '/path/to/prompt.md'
        mock.status = 'running'
        mock.current_iteration = 5
        mock.max_iterations = 10
        mock.start_time = datetime.now()
        mock.task_queue = ['Task 1', 'Task 2']
        mock.current_task = 'Current task'
        mock.completed_tasks = ['Done 1', 'Done 2']
        
        mock.get_orchestrator_state.return_value = {
            'id': 'test-orch-123',
            'prompt_file': '/path/to/prompt.md',
            'status': 'running',
            'current_iteration': 5,
            'max_iterations': 10,
            'start_time': mock.start_time.isoformat(),
            'elapsed_time': '00:05:30'
        }
        
        mock.get_task_status.return_value = {
            'queue': ['Task 1', 'Task 2'],
            'current': 'Current task',
            'completed': ['Done 1', 'Done 2']
        }
        
        return mock
    
    def test_register_orchestrator(self, monitor, mock_orchestrator):
        """Test registering an orchestrator."""
        orch_id = monitor.register_orchestrator(mock_orchestrator)
        
        assert orch_id == 'test-orch-123'
        assert orch_id in monitor.orchestrators
        assert monitor.orchestrators[orch_id] == mock_orchestrator
    
    def test_unregister_orchestrator(self, monitor, mock_orchestrator):
        """Test unregistering an orchestrator."""
        orch_id = monitor.register_orchestrator(mock_orchestrator)
        
        monitor.unregister_orchestrator(orch_id)
        assert orch_id not in monitor.orchestrators
    
    def test_get_orchestrator(self, monitor, mock_orchestrator):
        """Test getting a specific orchestrator."""
        orch_id = monitor.register_orchestrator(mock_orchestrator)
        
        orch = monitor.get_orchestrator(orch_id)
        assert orch == mock_orchestrator
        
        # Test non-existent orchestrator
        assert monitor.get_orchestrator('non-existent') is None
    
    def test_get_all_orchestrators(self, monitor):
        """Test getting all orchestrators."""
        # Register multiple orchestrators
        mocks = []
        for i in range(3):
            mock = MagicMock()
            mock.id = f'orch-{i}'
            mock.get_orchestrator_state.return_value = {'id': f'orch-{i}'}
            mocks.append(mock)
            monitor.register_orchestrator(mock)
        
        all_orchs = monitor.get_all_orchestrators()
        assert len(all_orchs) == 3
        assert all(orch['id'] == f'orch-{i}' for i, orch in enumerate(all_orchs))
    
    def test_pause_resume_orchestrator(self, monitor, mock_orchestrator):
        """Test pausing and resuming an orchestrator."""
        mock_orchestrator.pause = MagicMock()
        mock_orchestrator.resume = MagicMock()
        
        orch_id = monitor.register_orchestrator(mock_orchestrator)
        
        # Test pause
        success = monitor.pause_orchestrator(orch_id)
        assert success
        mock_orchestrator.pause.assert_called_once()
        
        # Test resume
        success = monitor.resume_orchestrator(orch_id)
        assert success
        mock_orchestrator.resume.assert_called_once()
        
        # Test with non-existent orchestrator
        assert not monitor.pause_orchestrator('non-existent')
        assert not monitor.resume_orchestrator('non-existent')


class TestWebServerAPI:
    """Test suite for FastAPI web server endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create a test client for the FastAPI app."""
        # Reset monitor state before each test
        app.state.monitor = OrchestratorMonitor(enable_auth=False)
        with TestClient(app) as client:
            yield client
    
    @pytest.fixture
    def auth_client(self):
        """Create a test client with authentication enabled."""
        temp_dir = tempfile.mkdtemp()
        app.state.monitor = OrchestratorMonitor(data_dir=temp_dir, enable_auth=True)
        app.state.monitor.auth_manager.create_user('testuser', 'testpass')
        
        with TestClient(app) as client:
            # Login to get token
            response = client.post('/api/auth/login', json={
                'username': 'testuser',
                'password': 'testpass'
            })
            token = response.json()['token']
            client.headers['Authorization'] = f'Bearer {token}'
            yield client
        
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_orchestrator(self):
        """Create and register a mock orchestrator."""
        mock = MagicMock()
        mock.id = 'test-orch-123'
        mock.prompt_file = '/path/to/prompt.md'
        mock.status = 'running'
        mock.current_iteration = 5
        mock.max_iterations = 10
        mock.start_time = datetime.now()
        
        mock.get_orchestrator_state.return_value = {
            'id': 'test-orch-123',
            'prompt_file': '/path/to/prompt.md',
            'status': 'running',
            'current_iteration': 5,
            'max_iterations': 10,
            'start_time': mock.start_time.isoformat()
        }
        
        mock.get_task_status.return_value = {
            'queue': ['Task 1', 'Task 2'],
            'current': 'Current task',
            'completed': ['Done 1', 'Done 2']
        }
        
        # Register with the global monitor
        app.state.monitor.register_orchestrator(mock)
        return mock
    
    def test_status_endpoint(self, client):
        """Test /api/status endpoint."""
        response = client.get('/api/status')
        assert response.status_code == 200
        
        data = response.json()
        assert 'status' in data
        assert 'active_orchestrators' in data
        assert 'system_metrics' in data
        assert data['status'] == 'running'
    
    def test_list_orchestrators(self, client, mock_orchestrator):
        """Test /api/orchestrators endpoint."""
        response = client.get('/api/orchestrators')
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 1
        assert data[0]['id'] == 'test-orch-123'
    
    def test_get_orchestrator(self, client, mock_orchestrator):
        """Test /api/orchestrators/{id} endpoint."""
        response = client.get('/api/orchestrators/test-orch-123')
        assert response.status_code == 200
        
        data = response.json()
        assert data['id'] == 'test-orch-123'
        assert data['status'] == 'running'
        
        # Test non-existent orchestrator
        response = client.get('/api/orchestrators/non-existent')
        assert response.status_code == 404
    
    def test_pause_orchestrator(self, client, mock_orchestrator):
        """Test /api/orchestrators/{id}/pause endpoint."""
        mock_orchestrator.pause = MagicMock()
        
        response = client.post('/api/orchestrators/test-orch-123/pause')
        assert response.status_code == 200
        assert response.json()['success'] is True
        mock_orchestrator.pause.assert_called_once()
        
        # Test non-existent orchestrator
        response = client.post('/api/orchestrators/non-existent/pause')
        assert response.status_code == 404
    
    def test_resume_orchestrator(self, client, mock_orchestrator):
        """Test /api/orchestrators/{id}/resume endpoint."""
        mock_orchestrator.resume = MagicMock()
        
        response = client.post('/api/orchestrators/test-orch-123/resume')
        assert response.status_code == 200
        assert response.json()['success'] is True
        mock_orchestrator.resume.assert_called_once()
    
    def test_get_tasks(self, client, mock_orchestrator):
        """Test /api/orchestrators/{id}/tasks endpoint."""
        response = client.get('/api/orchestrators/test-orch-123/tasks')
        assert response.status_code == 200
        
        data = response.json()
        assert 'queue' in data
        assert 'current' in data
        assert 'completed' in data
        assert len(data['queue']) == 2
        assert data['current'] == 'Current task'
    
    def test_metrics_endpoint(self, client):
        """Test /api/metrics endpoint."""
        response = client.get('/api/metrics')
        assert response.status_code == 200
        
        data = response.json()
        assert 'cpu_percent' in data
        assert 'memory_percent' in data
        assert 'active_processes' in data
    
    def test_history_endpoint(self, client):
        """Test /api/history endpoint."""
        response = client.get('/api/history')
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_prompt_endpoints(self, client, mock_orchestrator):
        """Test prompt get and update endpoints."""
        # Mock prompt file operations
        mock_orchestrator.prompt_file = '/tmp/test_prompt.md'
        
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = 'Test prompt content'
            
            # Test GET prompt
            response = client.get('/api/orchestrators/test-orch-123/prompt')
            assert response.status_code == 200
            data = response.json()
            assert data['content'] == 'Test prompt content'
            assert data['file_path'] == '/tmp/test_prompt.md'
    
    def test_authentication_required(self):
        """Test that authentication is enforced when enabled."""
        temp_dir = tempfile.mkdtemp()
        app.state.monitor = OrchestratorMonitor(data_dir=temp_dir, enable_auth=True)
        
        with TestClient(app) as client:
            # Test without token
            response = client.get('/api/orchestrators')
            assert response.status_code == 401
            
            # Test with invalid token
            client.headers['Authorization'] = 'Bearer invalid-token'
            response = client.get('/api/orchestrators')
            assert response.status_code == 401
        
        shutil.rmtree(temp_dir)
    
    def test_auth_login(self, client):
        """Test authentication login endpoint."""
        # Setup auth
        app.state.monitor.auth_manager = AuthManager()
        app.state.monitor.auth_manager.create_user('testuser', 'testpass')
        
        # Test successful login
        response = client.post('/api/auth/login', json={
            'username': 'testuser',
            'password': 'testpass'
        })
        assert response.status_code == 200
        assert 'token' in response.json()
        
        # Test failed login
        response = client.post('/api/auth/login', json={
            'username': 'testuser',
            'password': 'wrongpass'
        })
        assert response.status_code == 401
    
    def test_auth_verify(self, auth_client):
        """Test token verification endpoint."""
        response = auth_client.get('/api/auth/verify')
        assert response.status_code == 200
        assert response.json()['valid'] is True
    
    def test_change_password(self, auth_client):
        """Test password change endpoint."""
        response = auth_client.post('/api/auth/change-password', json={
            'old_password': 'testpass',
            'new_password': 'newpass123'
        })
        assert response.status_code == 200
        assert response.json()['success'] is True
    
    def test_static_files(self, client):
        """Test static file serving."""
        # Test index.html
        response = client.get('/')
        assert response.status_code in [200, 404]  # Depends on file existence
        
        # Test login.html
        response = client.get('/login')
        assert response.status_code in [200, 404]


class TestWebSocket:
    """Test suite for WebSocket functionality."""
    
    @pytest.fixture
    def client(self):
        """Create a test client for WebSocket testing."""
        app.state.monitor = OrchestratorMonitor(enable_auth=False)
        return TestClient(app)
    
    def test_websocket_connection(self, client):
        """Test WebSocket connection and basic messaging."""
        with client.websocket_connect('/ws') as websocket:
            # Should receive initial connection message
            data = websocket.receive_json()
            assert data['type'] == 'connection'
            assert data['status'] == 'connected'
    
    def test_websocket_orchestrator_updates(self, client):
        """Test WebSocket orchestrator state updates."""
        with client.websocket_connect('/ws') as websocket:
            # Receive initial connection message
            websocket.receive_json()
            
            # Register an orchestrator
            mock = MagicMock()
            mock.id = 'ws-test-orch'
            mock.get_orchestrator_state.return_value = {'id': 'ws-test-orch'}
            app.state.monitor.register_orchestrator(mock)
            
            # Should receive update about new orchestrator
            # (This would require implementing broadcast in the actual server)
    
    def test_websocket_with_auth(self):
        """Test WebSocket with authentication enabled."""
        temp_dir = tempfile.mkdtemp()
        app.state.monitor = OrchestratorMonitor(data_dir=temp_dir, enable_auth=True)
        app.state.monitor.auth_manager.create_user('wsuser', 'wspass')
        
        with TestClient(app) as client:
            # Get token
            response = client.post('/api/auth/login', json={
                'username': 'wsuser',
                'password': 'wspass'
            })
            token = response.json()['token']
            
            # Connect with token
            with client.websocket_connect(f'/ws?token={token}') as websocket:
                data = websocket.receive_json()
                assert data['type'] == 'connection'
            
            # Test without token (should fail)
            with pytest.raises(WebSocketDisconnect):
                with client.websocket_connect('/ws') as websocket:
                    pass
        
        shutil.rmtree(temp_dir)


class TestIntegration:
    """Integration tests for the complete web monitoring system."""
    
    @pytest.fixture
    def setup(self):
        """Setup complete monitoring environment."""
        temp_dir = tempfile.mkdtemp()
        monitor = OrchestratorMonitor(data_dir=temp_dir, enable_auth=True)
        app.state.monitor = monitor
        
        # Create test user
        monitor.auth_manager.create_user('integuser', 'integpass')
        
        yield {
            'temp_dir': temp_dir,
            'monitor': monitor,
            'client': TestClient(app)
        }
        
        shutil.rmtree(temp_dir)
    
    def test_complete_orchestrator_lifecycle(self, setup):
        """Test complete orchestrator lifecycle through web interface."""
        client = setup['client']
        monitor = setup['monitor']
        
        # Login
        response = client.post('/api/auth/login', json={
            'username': 'integuser',
            'password': 'integpass'
        })
        token = response.json()['token']
        headers = {'Authorization': f'Bearer {token}'}
        
        # Check initial status
        response = client.get('/api/status', headers=headers)
        assert response.json()['active_orchestrators'] == 0
        
        # Register orchestrator
        mock = MagicMock()
        mock.id = 'integ-orch'
        mock.prompt_file = '/integ/prompt.md'
        mock.get_orchestrator_state.return_value = {
            'id': 'integ-orch',
            'status': 'running'
        }
        mock.get_task_status.return_value = {
            'queue': [],
            'current': None,
            'completed': []
        }
        monitor.register_orchestrator(mock)
        
        # Verify orchestrator appears
        response = client.get('/api/orchestrators', headers=headers)
        assert len(response.json()) == 1
        
        # Pause orchestrator
        mock.pause = MagicMock()
        response = client.post('/api/orchestrators/integ-orch/pause', headers=headers)
        assert response.json()['success']
        
        # Resume orchestrator
        mock.resume = MagicMock()
        response = client.post('/api/orchestrators/integ-orch/resume', headers=headers)
        assert response.json()['success']
        
        # Unregister orchestrator
        monitor.unregister_orchestrator('integ-orch')
        
        # Verify orchestrator is gone
        response = client.get('/api/orchestrators', headers=headers)
        assert len(response.json()) == 0
    
    def test_database_integration(self, setup):
        """Test database integration with web server."""
        client = setup['client']
        monitor = setup['monitor']
        
        # Login
        response = client.post('/api/auth/login', json={
            'username': 'integuser',
            'password': 'integpass'
        })
        token = response.json()['token']
        headers = {'Authorization': f'Bearer {token}'}
        
        # Create a run in the database
        db = monitor.database
        run_id = db.create_run('test-orch', '/test/prompt.md')
        db.add_iteration(run_id, 1, 'Test output')
        db.update_run_status(run_id, 'completed')
        
        # Retrieve history through API
        response = client.get('/api/history', headers=headers)
        assert response.status_code == 200
        history = response.json()
        assert len(history) > 0
        
        # Get statistics
        response = client.get('/api/statistics', headers=headers)
        assert response.status_code == 200
        stats = response.json()
        assert stats['total_runs'] > 0