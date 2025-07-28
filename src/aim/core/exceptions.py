"""
Exception classes for the AIM Framework.

This module defines custom exceptions used throughout the AIM Framework
to provide clear error handling and debugging information.
"""

from typing import Optional, Any, Dict


class AIMException(Exception):
    """
    Base exception class for all AIM Framework exceptions.
    
    This is the parent class for all custom exceptions in the AIM Framework.
    It provides additional context and error tracking capabilities.
    
    Attributes:
        message (str): The error message
        error_code (str): A unique error code for programmatic handling
        context (Dict[str, Any]): Additional context information
    """
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.context = context or {}
    
    def __str__(self) -> str:
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            return f"{self.message} (Error Code: {self.error_code}, Context: {context_str})"
        return f"{self.message} (Error Code: {self.error_code})"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the exception to a dictionary for serialization."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "context": self.context,
        }


class AgentNotFoundError(AIMException):
    """
    Raised when a requested agent cannot be found in the mesh.
    
    This exception is raised when attempting to access an agent that
    doesn't exist or has been deactivated.
    """
    
    def __init__(self, agent_id: str, context: Optional[Dict[str, Any]] = None):
        message = f"Agent with ID '{agent_id}' not found in the mesh"
        super().__init__(
            message=message,
            error_code="AGENT_NOT_FOUND",
            context={**(context or {}), "agent_id": agent_id}
        )


class CapabilityNotAvailableError(AIMException):
    """
    Raised when a required capability is not available in the mesh.
    
    This exception is raised when no agents with the required capability
    are available to handle a request.
    """
    
    def __init__(self, capability: str, context: Optional[Dict[str, Any]] = None):
        message = f"No agents available with capability '{capability}'"
        super().__init__(
            message=message,
            error_code="CAPABILITY_NOT_AVAILABLE",
            context={**(context or {}), "capability": capability}
        )


class ContextNotFoundError(AIMException):
    """
    Raised when a requested context thread cannot be found.
    
    This exception is raised when attempting to access a context thread
    that doesn't exist or has been pruned.
    """
    
    def __init__(self, context_id: str, context: Optional[Dict[str, Any]] = None):
        message = f"Context thread with ID '{context_id}' not found"
        super().__init__(
            message=message,
            error_code="CONTEXT_NOT_FOUND",
            context={**(context or {}), "context_id": context_id}
        )


class ConfigurationError(AIMException):
    """
    Raised when there is an error in the framework configuration.
    
    This exception is raised when the framework configuration is invalid
    or missing required parameters.
    """
    
    def __init__(self, config_key: str, reason: str, context: Optional[Dict[str, Any]] = None):
        message = f"Configuration error for '{config_key}': {reason}"
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            context={**(context or {}), "config_key": config_key, "reason": reason}
        )


class AgentTimeoutError(AIMException):
    """
    Raised when an agent fails to respond within the specified timeout.
    
    This exception is raised when an agent takes too long to process
    a request and exceeds the configured timeout.
    """
    
    def __init__(self, agent_id: str, timeout: float, context: Optional[Dict[str, Any]] = None):
        message = f"Agent '{agent_id}' timed out after {timeout} seconds"
        super().__init__(
            message=message,
            error_code="AGENT_TIMEOUT",
            context={**(context or {}), "agent_id": agent_id, "timeout": timeout}
        )


class ResourceExhaustionError(AIMException):
    """
    Raised when the system runs out of available resources.
    
    This exception is raised when the framework cannot allocate
    sufficient resources to handle incoming requests.
    """
    
    def __init__(self, resource_type: str, context: Optional[Dict[str, Any]] = None):
        message = f"Resource exhaustion: {resource_type}"
        super().__init__(
            message=message,
            error_code="RESOURCE_EXHAUSTION",
            context={**(context or {}), "resource_type": resource_type}
        )


class ValidationError(AIMException):
    """
    Raised when input validation fails.
    
    This exception is raised when request parameters or configuration
    values fail validation checks.
    """
    
    def __init__(self, field: str, value: Any, reason: str, context: Optional[Dict[str, Any]] = None):
        message = f"Validation error for field '{field}' with value '{value}': {reason}"
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            context={**(context or {}), "field": field, "value": value, "reason": reason}
        )


class NetworkError(AIMException):
    """
    Raised when there is a network communication error between agents.
    
    This exception is raised when agents cannot communicate with each
    other due to network issues.
    """
    
    def __init__(self, source_agent: str, target_agent: str, reason: str, context: Optional[Dict[str, Any]] = None):
        message = f"Network error between '{source_agent}' and '{target_agent}': {reason}"
        super().__init__(
            message=message,
            error_code="NETWORK_ERROR",
            context={**(context or {}), "source_agent": source_agent, "target_agent": target_agent, "reason": reason}
        )


class SecurityError(AIMException):
    """
    Raised when a security violation is detected.
    
    This exception is raised when unauthorized access attempts or
    security policy violations are detected.
    """
    
    def __init__(self, violation_type: str, details: str, context: Optional[Dict[str, Any]] = None):
        message = f"Security violation: {violation_type} - {details}"
        super().__init__(
            message=message,
            error_code="SECURITY_ERROR",
            context={**(context or {}), "violation_type": violation_type, "details": details}
        )

