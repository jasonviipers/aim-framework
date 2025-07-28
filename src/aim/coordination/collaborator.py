"""
Confidence-based collaboration module for the AIM Framework.

This module implements confidence-based collaboration between agents,
allowing agents to work together when individual confidence is low.
"""

import asyncio
import time
from typing import Any, Dict, List, Optional

from ..core.agent import Agent
from ..core.request import Request, Response
from ..core.exceptions import AIMException
from ..utils.config import Config
from ..utils.logger import get_logger


class ConfidenceBasedCollaborator:
    """
    Manages confidence-based collaboration between agents.
    
    When an agent's confidence is below a threshold, this component
    can orchestrate collaboration with other agents to improve
    the quality and confidence of responses.
    """
    
    def __init__(self, config: Config):
        """
        Initialize the collaborator.
        
        Args:
            config: Framework configuration
        """
        self.config = config
        self.logger = get_logger(__name__)
        self.confidence_threshold = config.get("collaboration.confidence_threshold", 0.7)
        self.max_collaborating_agents = config.get("collaboration.max_collaborating_agents", 3)
        self.collaboration_timeout = config.get("collaboration.collaboration_timeout", 60.0)
        self.enable_consensus = config.get("collaboration.enable_consensus", True)
        
    async def initialize(self) -> None:
        """Initialize the collaborator."""
        self.logger.info("Confidence-based collaborator initialized")
    
    async def process_with_collaboration(
        self,
        request: Request,
        agent_path: List[str]
    ) -> Response:
        """
        Process a request with potential collaboration.
        
        Args:
            request: Request to process
            agent_path: List of agent IDs to process the request
            
        Returns:
            Response: Final response from processing
            
        Raises:
            AIMException: If processing fails
        """
        if not agent_path:
            raise AIMException("No agents provided for processing")
        
        # Start with the primary agent
        primary_agent_id = agent_path[0]
        
        try:
            # Get the primary agent (this would come from the framework)
            # For now, we'll simulate the response
            primary_response = await self._simulate_agent_response(
                primary_agent_id, request
            )
            
            # Check if collaboration is needed
            if primary_response.confidence >= self.confidence_threshold:
                self.logger.info(f"Primary agent {primary_agent_id} has sufficient confidence")
                return primary_response
            
            self.logger.info(f"Primary agent confidence {primary_response.confidence} below threshold, initiating collaboration")
            
            # Initiate collaboration
            collaborative_response = await self._collaborate_on_request(
                request, primary_response, agent_path[1:] if len(agent_path) > 1 else []
            )
            
            return collaborative_response
            
        except Exception as e:
            self.logger.error(f"Error in collaborative processing: {e}")
            raise AIMException(f"Collaborative processing failed: {e}")
    
    async def _collaborate_on_request(
        self,
        request: Request,
        primary_response: Response,
        additional_agents: List[str]
    ) -> Response:
        """
        Orchestrate collaboration between multiple agents.
        
        Args:
            request: Original request
            primary_response: Response from primary agent
            additional_agents: List of additional agent IDs
            
        Returns:
            Response: Collaborative response
        """
        responses = [primary_response]
        
        # Limit the number of collaborating agents
        collaborating_agents = additional_agents[:self.max_collaborating_agents - 1]
        
        # Get responses from additional agents
        tasks = []
        for agent_id in collaborating_agents:
            task = self._simulate_agent_response(agent_id, request)
            tasks.append(task)
        
        if tasks:
            try:
                additional_responses = await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=self.collaboration_timeout
                )
                
                # Filter out exceptions and add valid responses
                for response in additional_responses:
                    if isinstance(response, Response):
                        responses.append(response)
                    else:
                        self.logger.warning(f"Agent response failed: {response}")
                        
            except asyncio.TimeoutError:
                self.logger.warning("Collaboration timeout reached")
        
        # Synthesize final response
        if self.enable_consensus:
            return await self._create_consensus_response(request, responses)
        else:
            return await self._create_best_response(request, responses)
    
    async def _create_consensus_response(
        self,
        request: Request,
        responses: List[Response]
    ) -> Response:
        """
        Create a consensus response from multiple agent responses.
        
        Args:
            request: Original request
            responses: List of responses from different agents
            
        Returns:
            Response: Consensus response
        """
        if not responses:
            raise AIMException("No responses to create consensus from")
        
        if len(responses) == 1:
            return responses[0]
        
        # Simple consensus: combine content and average confidence
        combined_content = self._combine_response_content(responses)
        average_confidence = sum(r.confidence for r in responses) / len(responses)
        
        # Use the agent with highest confidence as the primary
        best_response = max(responses, key=lambda r: r.confidence)
        
        return Response(
            request_id=request.request_id,
            agent_id=f"collaborative_{best_response.agent_id}",
            content=combined_content,
            confidence=min(average_confidence + 0.1, 1.0),  # Boost for collaboration
            processing_time=sum(r.processing_time for r in responses),
            success=True,
            metadata={
                "collaboration_type": "consensus",
                "participating_agents": [r.agent_id for r in responses],
                "individual_confidences": [r.confidence for r in responses],
            }
        )
    
    async def _create_best_response(
        self,
        request: Request,
        responses: List[Response]
    ) -> Response:
        """
        Select the best response from multiple agent responses.
        
        Args:
            request: Original request
            responses: List of responses from different agents
            
        Returns:
            Response: Best response
        """
        if not responses:
            raise AIMException("No responses to select from")
        
        # Select response with highest confidence
        best_response = max(responses, key=lambda r: r.confidence)
        
        # Add collaboration metadata
        best_response.metadata.update({
            "collaboration_type": "best_selection",
            "participating_agents": [r.agent_id for r in responses],
            "selected_agent": best_response.agent_id,
            "confidence_scores": [r.confidence for r in responses],
        })
        
        return best_response
    
    def _combine_response_content(self, responses: List[Response]) -> str:
        """
        Combine content from multiple responses.
        
        Args:
            responses: List of responses to combine
            
        Returns:
            str: Combined content
        """
        if not responses:
            return ""
        
        if len(responses) == 1:
            return responses[0].content
        
        # Simple combination strategy
        combined_parts = []
        for i, response in enumerate(responses):
            if response.content.strip():
                combined_parts.append(f"Agent {i+1} ({response.agent_id}):\n{response.content}")
        
        if not combined_parts:
            return "No content generated from collaboration"
        
        return "\n\n---\n\n".join(combined_parts)
    
    async def _simulate_agent_response(self, agent_id: str, request: Request) -> Response:
        """
        Simulate an agent response (placeholder for actual agent processing).
        
        Args:
            agent_id: ID of the agent
            request: Request to process
            
        Returns:
            Response: Simulated response
        """
        # Simulate processing time
        await asyncio.sleep(0.1)
        
        # Simulate different confidence levels and responses
        import random
        confidence = random.uniform(0.4, 0.9)
        
        content = f"Response from {agent_id} for task: {request.task_type}"
        
        return Response(
            request_id=request.request_id,
            agent_id=agent_id,
            content=content,
            confidence=confidence,
            processing_time=0.1,
            success=True,
            metadata={"simulated": True}
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get collaboration statistics.
        
        Returns:
            Dict[str, Any]: Collaboration statistics
        """
        return {
            "confidence_threshold": self.confidence_threshold,
            "max_collaborating_agents": self.max_collaborating_agents,
            "collaboration_timeout": self.collaboration_timeout,
            "enable_consensus": self.enable_consensus,
        }

