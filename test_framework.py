#!/usr/bin/env python3
"""
Simple test script for the AIM Framework.
"""

import asyncio
import sys
from aim import AIMFramework, Config, Request, Agent, AgentCapability, Response

class TestAgent(Agent):
    """Simple test agent."""
    
    def __init__(self):
        super().__init__(
            capabilities={AgentCapability.CODE_GENERATION},
            description="Test agent for demonstration",
            version="1.0.0"
        )
    
    async def process_request(self, request: Request) -> Response:
        """Process a test request."""
        content = f"Test response from {self.agent_id} for: {request.content}"
        
        return Response(
            request_id=request.request_id,
            agent_id=self.agent_id,
            content=content,
            confidence=0.9,
            success=True
        )

async def main():
    """Test the AIM Framework."""
    print("Testing AIM Framework...")
    
    # Create configuration
    config = Config(config_dict={
        "framework": {
            "name": "Test AIM Framework",
            "log_level": "INFO"
        }
    })
    
    # Create framework
    framework = AIMFramework(config)
    
    try:
        # Initialize framework
        await framework.initialize()
        print("✓ Framework initialized successfully")
        
        # Register test agent
        test_agent = TestAgent()
        framework.register_agent(test_agent)
        print("✓ Test agent registered")
        
        # Create test request
        request = Request(
            user_id="test_user",
            content="Generate a hello world function",
            task_type="code_generation"
        )
        
        # Process request
        response = await framework.process_request(request)
        print(f"✓ Request processed successfully")
        print(f"  Response: {response.content}")
        print(f"  Confidence: {response.confidence}")
        
        # Get framework status
        status = framework.get_framework_status()
        print(f"✓ Framework status: {status['total_agents']} agents, {status['active_agents']} active")
        
        print("\n🎉 AIM Framework test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)
    
    finally:
        # Shutdown framework
        await framework.shutdown()
        print("✓ Framework shutdown complete")

if __name__ == "__main__":
    asyncio.run(main())
