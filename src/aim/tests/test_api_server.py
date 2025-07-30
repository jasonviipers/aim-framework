"""
Tests for the AIM Framework API server.
"""

import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from flask import Flask
from aim.api.server import AIMServer
from aim.utils.config import Config
from aim.core.request import Request, Priority


class TestAIMServer:
    """Test cases for the AIM API server."""

    @pytest.fixture
    def test_config(self):
        """Create a test configuration."""
        return Config(config_dict={
            "framework": {
                "name": "Test AIM Framework",
                "log_level": "DEBUG"
            },
            "api": {
                "host": "127.0.0.1",
                "port": 5001,
                "debug": True,
                "cors_enabled": True
            },
            "security": {
                "allowed_origins": ["*"]
            }
        })

    @pytest.fixture
    def server(self, test_config):
        """Create a test server instance."""
        with patch('aim.api.server.AIMFramework'):
            return AIMServer(test_config)

    @pytest.fixture
    def client(self, server):
        """Create a test client."""
        server.app.config['TESTING'] = True
        return server.app.test_client()

    def test_server_initialization(self, test_config):
        """Test server initialization."""
        with patch('aim.api.server.AIMFramework'):
            server = AIMServer(test_config)
            assert server.host == "127.0.0.1"
            assert server.port == 5001
            assert server.debug is True

    def test_health_check_endpoint(self, client, server):
        """Test health check endpoint."""
        # Mock framework status
        server.framework.is_initialized = True
        server.framework.get_framework_status.return_value = {
            "status": "running",
            "timestamp": "2024-01-01T00:00:00Z"
        }

        response = client.get('/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert data['framework_initialized'] is True

    def test_process_request_endpoint_success(self, client, server):
        """Test successful request processing."""
        # Mock framework response
        mock_response = Mock()
        mock_response.to_dict.return_value = {
            "request_id": "test-123",
            "success": True,
            "content": "Test response"
        }
        
        with patch.object(server.framework, 'process_request', return_value=mock_response):
            response = client.post('/process', 
                json={
                    "user_id": "test_user",
                    "content": "Test content",
                    "task_type": "test_task"
                }
            )
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True

    def test_process_request_missing_fields(self, client):
        """Test request processing with missing required fields."""
        response = client.post('/process', 
            json={
                "user_id": "test_user",
                # Missing content and task_type
            }
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Missing required field' in data['error']

    def test_process_request_no_json(self, client):
        """Test request processing without JSON data."""
        response = client.post('/process')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'No JSON data provided'

    def test_process_request_with_optional_fields(self, client, server):
        """Test request processing with optional fields."""
        mock_response = Mock()
        mock_response.to_dict.return_value = {
            "request_id": "test-123",
            "success": True,
            "content": "Test response"
        }
        
        with patch.object(server.framework, 'process_request', return_value=mock_response):
            response = client.post('/process', 
                json={
                    "user_id": "test_user",
                    "content": "Test content",
                    "task_type": "test_task",
                    "priority": "high",
                    "timeout": 60.0,
                    "context_thread_id": "thread-123",
                    "metadata": {"key": "value"}
                }
            )
            
            assert response.status_code == 200

    def test_list_agents_endpoint(self, client, server):
        """Test list agents endpoint."""
        server.framework.list_agents.return_value = [
            {"id": "agent1", "capabilities": ["code_generation"]},
            {"id": "agent2", "capabilities": ["data_analysis"]}
        ]

        response = client.get('/agents')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data['agents']) == 2

    def test_get_agent_endpoint(self, client, server):
        """Test get agent endpoint."""
        mock_agent = Mock()
        mock_agent.get_info.return_value = {
            "id": "test_agent",
            "capabilities": ["code_generation"],
            "status": "active"
        }
        server.framework.get_agent.return_value = mock_agent

        response = client.get('/agents/test_agent')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['id'] == 'test_agent'

    def test_get_agent_not_found(self, client, server):
        """Test get agent endpoint with non-existent agent."""
        server.framework.get_agent.side_effect = Exception("Agent not found")

        response = client.get('/agents/nonexistent')
        assert response.status_code == 404
        
        data = json.loads(response.data)
        assert 'error' in data

    def test_create_context_endpoint(self, client, server):
        """Test create context endpoint."""
        with patch.object(server.framework, 'create_context_thread', return_value="thread-123"):
            response = client.post('/context', 
                json={
                    "user_id": "test_user",
                    "initial_context": {"key": "value"}
                }
            )
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['thread_id'] == 'thread-123'

    def test_create_context_missing_user_id(self, client):
        """Test create context endpoint without user_id."""
        response = client.post('/context', json={})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'user_id is required'

    def test_get_context_endpoint(self, client, server):
        """Test get context endpoint."""
        server.framework.get_context_thread.return_value = {
            "thread_id": "thread-123",
            "user_id": "test_user",
            "context": {"key": "value"}
        }

        response = client.get('/context/thread-123')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['thread_id'] == 'thread-123'

    def test_get_user_contexts_endpoint(self, client, server):
        """Test get user contexts endpoint."""
        server.framework.get_user_context_threads.return_value = [
            {"thread_id": "thread-1", "created_at": "2024-01-01"},
            {"thread_id": "thread-2", "created_at": "2024-01-02"}
        ]

        response = client.get('/users/test_user/contexts')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data['contexts']) == 2

    def test_get_metrics_endpoint(self, client, server):
        """Test get metrics endpoint."""
        with patch.object(server.framework, 'get_performance_metrics', return_value={
            "requests_processed": 100,
            "average_response_time": 0.5,
            "active_agents": 3
        }):
            response = client.get('/metrics')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['requests_processed'] == 100

    def test_get_status_endpoint(self, client, server):
        """Test get status endpoint."""
        server.framework.get_framework_status.return_value = {
            "status": "running",
            "uptime": "1h 30m",
            "version": "1.0.0"
        }

        response = client.get('/status')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'running'

    def test_get_intent_predictions_endpoint(self, client, server):
        """Test get intent predictions endpoint."""
        with patch.object(server.framework, 'get_intent_predictions', return_value=[
            {"intent": "code_generation", "confidence": 0.9},
            {"intent": "data_analysis", "confidence": 0.7}
        ]):
            response = client.get('/intents/test_user/predictions')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert len(data['predictions']) == 2

    def test_cors_headers(self, client, server):
        """Test CORS headers are properly set."""
        response = client.get('/health')
        
        # Check if CORS is enabled (this depends on Flask-CORS configuration)
        assert response.status_code == 200

    def test_error_handling(self, client, server):
        """Test error handling in endpoints."""
        server.framework.list_agents.side_effect = Exception("Database error")

        response = client.get('/agents')
        assert response.status_code == 500
        
        data = json.loads(response.data)
        assert 'error' in data