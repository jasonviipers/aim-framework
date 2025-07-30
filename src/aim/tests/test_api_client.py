"""
Tests for the AIM Framework API client.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from aim.api.client import AIMClient
from aim.core.request import Request, Priority


class TestAIMClient:
    """Test cases for the AIM API client."""

    def test_client_initialization(self):
        """Test client initialization with default parameters."""
        client = AIMClient()
        assert client.base_url == "http://localhost:5000"
        assert client.timeout == 30.0
        assert client.session is None

    def test_client_initialization_with_custom_params(self):
        """Test client initialization with custom parameters."""
        client = AIMClient(
            base_url="http://example.com:8080",
            timeout=60.0
        )
        assert client.base_url == "http://example.com:8080"
        assert client.timeout == 60.0

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test successful health check."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.json.return_value = {
                "status": "healthy",
                "framework_initialized": True
            }
            mock_response.status = 200
            mock_get.return_value.__aenter__.return_value = mock_response

            client = AIMClient()
            result = await client.health_check()
            
            assert result["status"] == "healthy"
            assert result["framework_initialized"] is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """Test health check failure."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 500
            mock_get.return_value.__aenter__.return_value = mock_response

            client = AIMClient()
            result = await client.health_check()
            
            assert result is None

    @pytest.mark.asyncio
    async def test_process_request_success(self):
        """Test successful request processing."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.json.return_value = {
                "request_id": "test-123",
                "success": True,
                "content": "Test response"
            }
            mock_response.status = 200
            mock_post.return_value.__aenter__.return_value = mock_response

            client = AIMClient()
            request = Request(
                user_id="test_user",
                content="Test content",
                task_type="test_task"
            )
            
            result = await client.process_request(request)
            
            assert result["success"] is True
            assert result["content"] == "Test response"

    @pytest.mark.asyncio
    async def test_process_request_with_priority(self):
        """Test request processing with priority."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.json.return_value = {
                "request_id": "test-123",
                "success": True,
                "content": "High priority response"
            }
            mock_response.status = 200
            mock_post.return_value.__aenter__.return_value = mock_response

            client = AIMClient()
            request = Request(
                user_id="test_user",
                content="Urgent task",
                task_type="urgent_task",
                priority=Priority.HIGH
            )
            
            result = await client.process_request(request)
            
            # Verify the request was made with correct priority
            call_args = mock_post.call_args
            request_data = call_args[1]['json']
            assert request_data['priority'] == 'high'

    @pytest.mark.asyncio
    async def test_list_agents_success(self):
        """Test successful agent listing."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.json.return_value = {
                "agents": [
                    {"id": "agent1", "capabilities": ["code_generation"]},
                    {"id": "agent2", "capabilities": ["data_analysis"]}
                ]
            }
            mock_response.status = 200
            mock_get.return_value.__aenter__.return_value = mock_response

            client = AIMClient()
            result = await client.list_agents()
            
            assert len(result["agents"]) == 2
            assert result["agents"][0]["id"] == "agent1"

    @pytest.mark.asyncio
    async def test_get_agent_success(self):
        """Test successful agent retrieval."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.json.return_value = {
                "id": "test_agent",
                "capabilities": ["code_generation"],
                "status": "active"
            }
            mock_response.status = 200
            mock_get.return_value.__aenter__.return_value = mock_response

            client = AIMClient()
            result = await client.get_agent("test_agent")
            
            assert result["id"] == "test_agent"
            assert result["status"] == "active"

    @pytest.mark.asyncio
    async def test_create_context_thread_success(self):
        """Test successful context thread creation."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.json.return_value = {
                "thread_id": "thread-123"
            }
            mock_response.status = 200
            mock_post.return_value.__aenter__.return_value = mock_response

            client = AIMClient()
            result = await client.create_context_thread(
                user_id="test_user",
                initial_context={"key": "value"}
            )
            
            assert result["thread_id"] == "thread-123"

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test client as context manager."""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session

            async with AIMClient() as client:
                assert client.session is not None
                
            # Verify session was closed
            mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_method(self):
        """Test explicit client closure."""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session

            client = AIMClient()
            await client._ensure_session()
            await client.close()
            
            mock_session.close.assert_called_once()
            assert client.session is None

    @pytest.mark.asyncio
    async def test_request_timeout(self):
        """Test request timeout handling."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.side_effect = asyncio.TimeoutError()

            client = AIMClient(timeout=1.0)
            result = await client.health_check()
            
            assert result is None

    @pytest.mark.asyncio
    async def test_network_error_handling(self):
        """Test network error handling."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.side_effect = Exception("Network error")

            client = AIMClient()
            result = await client.health_check()
            
            assert result is None