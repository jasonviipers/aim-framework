"""
Example agent for the AIM Framework project.
"""

from aim import Agent, AgentCapability, Request, Response

class ExampleAgent(Agent):
    """Example agent implementation."""
    
    def __init__(self):
        super().__init__(
            capabilities={AgentCapability.CODE_GENERATION},
            description="Example agent for demonstration purposes",
            version="1.0.0"
        )
    
    async def process_request(self, request: Request) -> Response:
        """Process a request and return a response."""
        # Simple echo response
        content = f"Echo: {request.content}"
        
        return Response(
            request_id=request.request_id,
            agent_id=self.agent_id,
            content=content,
            confidence=0.9,
            success=True
        )
