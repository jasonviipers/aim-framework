"""
Core module for the AIM Framework.

This module contains the fundamental components of the AIM Framework:
- Framework: Main orchestrator class
- Agent: Base agent implementation
- Context: Context management and threading
- Request/Response: Communication primitives
- Exceptions: Framework-specific exceptions
"""

from .framework import AIMFramework
from .agent import Agent, AgentCapability, AgentStatus
from .context import ContextThread, ContextManager
from .request import Request, Response, RequestStatus
from .exceptions import (
    AIMException,
    AgentNotFoundError,
    CapabilityNotAvailableError,
    ContextNotFoundError,
    ConfigurationError,
)

__all__ = [
    "AIMFramework",
    "Agent",
    "AgentCapability",
    "AgentStatus",
    "ContextThread",
    "ContextManager",
    "Request",
    "Response",
    "RequestStatus",
    "AIMException",
    "AgentNotFoundError",
    "CapabilityNotAvailableError",
    "ContextNotFoundError",
    "ConfigurationError",
]

