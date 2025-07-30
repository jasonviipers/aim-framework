"""
Test configuration for the AIM Framework test suite.
"""

import pytest
import asyncio
from typing import Generator
from aim import AIMFramework, Config
from aim.core.agent import Agent, AgentCapability
from aim.core.request import Request, Response


class MockAgent(Agent):
    """Mock agent for testing purposes."""
    
    def __init__(self, agent_id: str = "test_agent"):
        super().__init__(
            agent_id=agent_id,
            capabilities={AgentCapability.CODE_GENERATION},
            description="Mock agent for testing",
            version="1.0.0"
        )
    
    async def process_request(self, request: Request) -> Response:
        """Process a test request."""
        return Response(
            request_id=request.request_id,
            agent_id=self.agent_id,
            content=f"Mock response to: {request.content}",
            success=True,
            metadata={"test": True}
        )


@pytest.fixture
def test_config() -> Config:
    """Create a test configuration."""
    return Config(config_dict={
        "framework": {
            "name": "Test AIM Framework",
            "log_level": "DEBUG"
        },
        "api": {
            "host": "127.0.0.1",
            "port": 5001,
            "debug": True
        },
        "agents": {
            "max_concurrent_requests": 10,
            "request_timeout": 30.0
        }
    })


@pytest.fixture
def mock_agent() -> MockAgent:
    """Create a mock agent for testing."""
    return MockAgent()


@pytest.fixture
async def framework(test_config: Config) -> Generator[AIMFramework, None, None]:
    """Create and initialize a test framework instance."""
    framework = AIMFramework(test_config)
    await framework.initialize()
    yield framework
    await framework.shutdown()


@pytest.fixture
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_request() -> Request:
    """Create a sample request for testing."""
    return Request(
        user_id="test_user",
        content="Test request content",
        task_type="test_task"
    )