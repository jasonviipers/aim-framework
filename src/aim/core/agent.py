"""
Agent module for the AIM Framework.

This module defines the base Agent class and related components for
creating and managing AI agents within the mesh network.
"""

import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union

from .exceptions import AIMException, ValidationError
from .request import Request, Response


class AgentStatus(Enum):
    """Enumeration of possible agent states."""
    INITIALIZING = "initializing"
    ACTIVE = "active"
    IDLE = "idle"
    BUSY = "busy"
    HIBERNATING = "hibernating"
    DEACTIVATED = "deactivated"
    ERROR = "error"


class AgentCapability(Enum):
    """Enumeration of agent capabilities."""
    CODE_GENERATION = "code_generation"
    SECURITY_REVIEW = "security_review"
    DOCUMENTATION = "documentation"
    DATA_ANALYSIS = "data_analysis"
    DESIGN = "design"
    RESEARCH = "research"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"
    OPTIMIZATION = "optimization"
    TRANSLATION = "translation"
    SUMMARIZATION = "summarization"
    QUESTION_ANSWERING = "question_answering"
    IMAGE_PROCESSING = "image_processing"
    AUDIO_PROCESSING = "audio_processing"
    VIDEO_PROCESSING = "video_processing"
    NATURAL_LANGUAGE_PROCESSING = "natural_language_processing"
    MACHINE_LEARNING = "machine_learning"
    DEEP_LEARNING = "deep_learning"
    COMPUTER_VISION = "computer_vision"
    ROBOTICS = "robotics"


@dataclass
class AgentMetrics:
    """Metrics for tracking agent performance."""
    total_requests_processed: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_processing_time: float = 0.0
    average_confidence: float = 0.0
    last_active_time: float = field(default_factory=time.time)
    uptime: float = 0.0
    memory_usage: float = 0.0
    cpu_usage: float = 0.0
    
    @property
    def success_rate(self) -> float:
        """Calculate the success rate of processed requests."""
        if self.total_requests_processed == 0:
            return 0.0
        return self.successful_requests / self.total_requests_processed
    
    @property
    def error_rate(self) -> float:
        """Calculate the error rate of processed requests."""
        if self.total_requests_processed == 0:
            return 0.0
        return self.failed_requests / self.total_requests_processed


class Agent(ABC):
    """
    Base class for all agents in the AIM Framework.
    
    This abstract class defines the interface that all agents must implement
    to participate in the mesh network. Agents are specialized components
    that handle specific types of requests based on their capabilities.
    
    Attributes:
        agent_id (str): Unique identifier for the agent
        capabilities (Set[AgentCapability]): Set of capabilities this agent provides
        status (AgentStatus): Current status of the agent
        description (str): Human-readable description of the agent
        version (str): Version of the agent implementation
        created_at (float): Timestamp when the agent was created
        metrics (AgentMetrics): Performance metrics for the agent
    """
    
    def __init__(
        self,
        agent_id: Optional[str] = None,
        capabilities: Optional[Set[AgentCapability]] = None,
        description: str = "",
        version: str = "1.0.0",
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a new agent.
        
        Args:
            agent_id: Unique identifier for the agent. If None, a UUID will be generated.
            capabilities: Set of capabilities this agent provides
            description: Human-readable description of the agent
            version: Version of the agent implementation
            config: Configuration parameters for the agent
        """
        self.agent_id = agent_id or str(uuid.uuid4())
        self.capabilities = capabilities or set()
        self.status = AgentStatus.INITIALIZING
        self.description = description
        self.version = version
        self.created_at = time.time()
        self.config = config or {}
        self.metrics = AgentMetrics()
        
        # Validate agent configuration
        self._validate_configuration()
        
        # Initialize the agent
        self._initialize()
    
    def _validate_configuration(self) -> None:
        """Validate the agent configuration."""
        if not self.agent_id:
            raise ValidationError("agent_id", self.agent_id, "Agent ID cannot be empty")
        
        if not self.capabilities:
            raise ValidationError("capabilities", self.capabilities, "Agent must have at least one capability")
        
        # Validate capability types
        for capability in self.capabilities:
            if not isinstance(capability, AgentCapability):
                raise ValidationError("capabilities", capability, "All capabilities must be AgentCapability instances")
    
    def _initialize(self) -> None:
        """Initialize the agent. Override in subclasses for custom initialization."""
        self.status = AgentStatus.ACTIVE
    
    @abstractmethod
    async def process_request(self, request: Request) -> Response:
        """
        Process a request and return a response.
        
        This is the main method that agents must implement to handle requests.
        The method should be asynchronous to allow for concurrent processing.
        
        Args:
            request: The request to process
            
        Returns:
            Response: The response to the request
            
        Raises:
            AIMException: If the request cannot be processed
        """
        pass
    
    def can_handle_request(self, request: Request) -> bool:
        """
        Check if this agent can handle the given request.
        
        Args:
            request: The request to check
            
        Returns:
            bool: True if the agent can handle the request, False otherwise
        """
        # Check if the agent has the required capability
        if hasattr(request, 'required_capability'):
            return request.required_capability in self.capabilities
        
        # Check if the agent can handle the task type
        if hasattr(request, 'task_type'):
            try:
                required_capability = AgentCapability(request.task_type)
                return required_capability in self.capabilities
            except ValueError:
                return False
        
        return False
    
    def get_confidence_score(self, request: Request) -> float:
        """
        Calculate a confidence score for handling the given request.
        
        The confidence score is a value between 0.0 and 1.0 indicating
        how confident the agent is in its ability to handle the request.
        
        Args:
            request: The request to evaluate
            
        Returns:
            float: Confidence score between 0.0 and 1.0
        """
        if not self.can_handle_request(request):
            return 0.0
        
        # Base confidence based on capability match
        base_confidence = 0.7
        
        # Adjust based on agent performance metrics
        performance_factor = self.metrics.success_rate * 0.2
        
        # Adjust based on current load
        load_factor = 0.1 if self.status == AgentStatus.IDLE else 0.0
        
        return min(1.0, base_confidence + performance_factor + load_factor)
    
    def update_metrics(self, processing_time: float, success: bool, confidence: float) -> None:
        """
        Update agent performance metrics.
        
        Args:
            processing_time: Time taken to process the request
            success: Whether the request was processed successfully
            confidence: Confidence score for the processed request
        """
        self.metrics.total_requests_processed += 1
        
        if success:
            self.metrics.successful_requests += 1
        else:
            self.metrics.failed_requests += 1
        
        # Update average processing time
        total_time = self.metrics.average_processing_time * (self.metrics.total_requests_processed - 1)
        self.metrics.average_processing_time = (total_time + processing_time) / self.metrics.total_requests_processed
        
        # Update average confidence
        total_confidence = self.metrics.average_confidence * (self.metrics.total_requests_processed - 1)
        self.metrics.average_confidence = (total_confidence + confidence) / self.metrics.total_requests_processed
        
        self.metrics.last_active_time = time.time()
    
    def set_status(self, status: AgentStatus) -> None:
        """
        Set the agent status.
        
        Args:
            status: The new status for the agent
        """
        self.status = status
    
    def hibernate(self) -> None:
        """Put the agent into hibernation mode to save resources."""
        self.status = AgentStatus.HIBERNATING
    
    def activate(self) -> None:
        """Activate the agent from hibernation mode."""
        if self.status == AgentStatus.HIBERNATING:
            self.status = AgentStatus.ACTIVE
    
    def deactivate(self) -> None:
        """Deactivate the agent permanently."""
        self.status = AgentStatus.DEACTIVATED
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get information about the agent.
        
        Returns:
            Dict[str, Any]: Dictionary containing agent information
        """
        return {
            "agent_id": self.agent_id,
            "capabilities": [cap.value for cap in self.capabilities],
            "status": self.status.value,
            "description": self.description,
            "version": self.version,
            "created_at": self.created_at,
            "metrics": {
                "total_requests_processed": self.metrics.total_requests_processed,
                "successful_requests": self.metrics.successful_requests,
                "failed_requests": self.metrics.failed_requests,
                "success_rate": self.metrics.success_rate,
                "error_rate": self.metrics.error_rate,
                "average_processing_time": self.metrics.average_processing_time,
                "average_confidence": self.metrics.average_confidence,
                "last_active_time": self.metrics.last_active_time,
                "uptime": time.time() - self.created_at,
            }
        }
    
    def __str__(self) -> str:
        """String representation of the agent."""
        capabilities_str = ", ".join(cap.value for cap in self.capabilities)
        return f"Agent(id={self.agent_id}, capabilities=[{capabilities_str}], status={self.status.value})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the agent."""
        return (
            f"Agent(agent_id='{self.agent_id}', "
            f"capabilities={self.capabilities}, "
            f"status={self.status}, "
            f"description='{self.description}', "
            f"version='{self.version}')"
        )

