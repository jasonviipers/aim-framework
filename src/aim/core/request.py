"""
Request and Response module for the AIM Framework.

This module defines the Request and Response classes used for communication
between components in the AIM Framework.
"""

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from .exceptions import ValidationError


class RequestStatus(Enum):
    """Enumeration of possible request states."""
    PENDING = "pending"
    ROUTING = "routing"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class Priority(Enum):
    """Enumeration of request priorities."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class Request:
    """
    Represents a request in the AIM Framework.
    
    A request encapsulates all the information needed to process a user's
    query or task, including the content, metadata, and routing information.
    
    Attributes:
        request_id (str): Unique identifier for the request
        user_id (str): Identifier of the user making the request
        content (str): The actual request content
        task_type (str): Type of task being requested
        priority (Priority): Priority level of the request
        timeout (float): Maximum time to wait for completion (seconds)
        context_thread_id (Optional[str]): ID of the context thread
        metadata (Dict[str, Any]): Additional metadata
        created_at (float): Timestamp when the request was created
        status (RequestStatus): Current status of the request
        agent_path (List[str]): List of agents that have processed this request
    """
    
    user_id: str
    content: str
    task_type: str
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    priority: Priority = Priority.NORMAL
    timeout: float = 30.0
    context_thread_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    status: RequestStatus = RequestStatus.PENDING
    agent_path: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate the request after initialization."""
        self._validate()
    
    def _validate(self) -> None:
        """Validate the request parameters."""
        if not self.user_id:
            raise ValidationError("user_id", self.user_id, "User ID cannot be empty")
        
        if not self.content:
            raise ValidationError("content", self.content, "Request content cannot be empty")
        
        if not self.task_type:
            raise ValidationError("task_type", self.task_type, "Task type cannot be empty")
        
        if self.timeout <= 0:
            raise ValidationError("timeout", self.timeout, "Timeout must be positive")
        
        if not isinstance(self.priority, Priority):
            raise ValidationError("priority", self.priority, "Priority must be a Priority enum value")
    
    def add_to_agent_path(self, agent_id: str) -> None:
        """
        Add an agent to the processing path.
        
        Args:
            agent_id: ID of the agent to add to the path
        """
        if agent_id not in self.agent_path:
            self.agent_path.append(agent_id)
    
    def set_status(self, status: RequestStatus) -> None:
        """
        Set the request status.
        
        Args:
            status: The new status for the request
        """
        self.status = status
    
    def is_expired(self) -> bool:
        """
        Check if the request has expired based on its timeout.
        
        Returns:
            bool: True if the request has expired, False otherwise
        """
        return time.time() - self.created_at > self.timeout
    
    def get_age(self) -> float:
        """
        Get the age of the request in seconds.
        
        Returns:
            float: Age of the request in seconds
        """
        return time.time() - self.created_at
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the request to a dictionary for serialization.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the request
        """
        return {
            "request_id": self.request_id,
            "user_id": self.user_id,
            "content": self.content,
            "task_type": self.task_type,
            "priority": self.priority.value,
            "timeout": self.timeout,
            "context_thread_id": self.context_thread_id,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "status": self.status.value,
            "agent_path": self.agent_path,
            "age": self.get_age(),
            "expired": self.is_expired(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Request":
        """
        Create a Request instance from a dictionary.
        
        Args:
            data: Dictionary containing request data
            
        Returns:
            Request: New Request instance
        """
        # Convert string enums back to enum instances
        if "priority" in data and isinstance(data["priority"], str):
            data["priority"] = Priority(data["priority"])
        
        if "status" in data and isinstance(data["status"], str):
            data["status"] = RequestStatus(data["status"])
        
        # Remove computed fields
        data.pop("age", None)
        data.pop("expired", None)
        
        return cls(**data)


@dataclass
class Response:
    """
    Represents a response in the AIM Framework.
    
    A response contains the result of processing a request, along with
    metadata about the processing.
    
    Attributes:
        request_id (str): ID of the request this response is for
        agent_id (str): ID of the agent that generated this response
        content (str): The response content
        confidence (float): Confidence score for the response (0.0 to 1.0)
        processing_time (float): Time taken to process the request (seconds)
        success (bool): Whether the request was processed successfully
        error_message (Optional[str]): Error message if processing failed
        metadata (Dict[str, Any]): Additional metadata
        created_at (float): Timestamp when the response was created
        context_updates (Dict[str, Any]): Updates to the context thread
    """
    
    request_id: str
    agent_id: str
    content: str
    confidence: float = 0.0
    processing_time: float = 0.0
    success: bool = True
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    context_updates: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate the response after initialization."""
        self._validate()
    
    def _validate(self) -> None:
        """Validate the response parameters."""
        if not self.request_id:
            raise ValidationError("request_id", self.request_id, "Request ID cannot be empty")
        
        if not self.agent_id:
            raise ValidationError("agent_id", self.agent_id, "Agent ID cannot be empty")
        
        if self.confidence < 0.0 or self.confidence > 1.0:
            raise ValidationError("confidence", self.confidence, "Confidence must be between 0.0 and 1.0")
        
        if self.processing_time < 0.0:
            raise ValidationError("processing_time", self.processing_time, "Processing time cannot be negative")
        
        if not self.success and not self.error_message:
            raise ValidationError("error_message", self.error_message, "Error message required when success is False")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the response to a dictionary for serialization.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the response
        """
        return {
            "request_id": self.request_id,
            "agent_id": self.agent_id,
            "content": self.content,
            "confidence": self.confidence,
            "processing_time": self.processing_time,
            "success": self.success,
            "error_message": self.error_message,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "context_updates": self.context_updates,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Response":
        """
        Create a Response instance from a dictionary.
        
        Args:
            data: Dictionary containing response data
            
        Returns:
            Response: New Response instance
        """
        return cls(**data)
    
    @classmethod
    def create_error_response(
        cls,
        request_id: str,
        agent_id: str,
        error_message: str,
        processing_time: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "Response":
        """
        Create an error response.
        
        Args:
            request_id: ID of the request
            agent_id: ID of the agent
            error_message: Error message
            processing_time: Time taken before the error occurred
            metadata: Additional metadata
            
        Returns:
            Response: Error response instance
        """
        return cls(
            request_id=request_id,
            agent_id=agent_id,
            content="",
            confidence=0.0,
            processing_time=processing_time,
            success=False,
            error_message=error_message,
            metadata=metadata or {},
        )

