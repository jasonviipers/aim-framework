"""
AIM Framework: Adaptive Intelligence Mesh

A distributed coordination system for AI deployment and interaction.

The AIM Framework creates a mesh network of AI agents that can:
- Route queries to specialized micro-agents based on context and expertise
- Maintain persistent context across sessions and agents
- Automatically scale resources based on demand patterns
- Share knowledge across the mesh without centralized retraining
- Enable confidence-based collaboration between agents

Key Components:
- Dynamic Capability Routing
- Persistent Context Weaving
- Adaptive Resource Scaling
- Cross-Agent Learning Propagation
- Intent Graph for predictive resource allocation

Example usage:
    >>> from aim import AIMFramework
    >>> framework = AIMFramework()
    >>> framework.initialize()
    >>> response = framework.process_request(
    ...     user_id="user_123",
    ...     request="Create a Python function to calculate prime numbers",
    ...     task_type="code_generation"
    ... )
    >>> print(response.content)
"""

__version__ = "1.0.0"
__author__ = "jasonviipers"
__email__ = "support@jasonviipers"
__license__ = "MIT"

from .api.client import AIMClient

# API imports
from .api.server import AIMServer
from .coordination.collaborator import ConfidenceBasedCollaborator

# Coordination imports
from .coordination.router import CapabilityRouter
from .core.agent import Agent, AgentCapability
from .core.context import ContextManager, ContextThread

# Exception imports
from .core.exceptions import (
    AgentNotFoundError,
    AIMException,
    CapabilityNotAvailableError,
    ConfigurationError,
    ContextNotFoundError,
)

# Core imports
from .core.framework import AIMFramework
from .core.request import Request, Response

# Knowledge management imports
from .knowledge.capsule import KnowledgeCapsule
from .knowledge.intent_graph import IntentGraph
from .knowledge.propagator import LearningPropagator
from .resources.monitor import PerformanceMonitor

# Resource management imports
from .resources.scaler import AdaptiveResourceScaler

# Utility imports
from .utils.config import Config
from .utils.logger import get_logger

__all__ = [
    # Core classes
    "AIMFramework",
    "Agent",
    "AgentCapability",
    "ContextThread",
    "ContextManager",
    "Request",
    "Response",
    # Coordination classes
    "CapabilityRouter",
    "ConfidenceBasedCollaborator",
    # Resource management classes
    "AdaptiveResourceScaler",
    "PerformanceMonitor",
    # Knowledge management classes
    "KnowledgeCapsule",
    "LearningPropagator",
    "IntentGraph",
    # API classes
    "AIMServer",
    "AIMClient",
    # Utility classes
    "Config",
    "get_logger",
    # Exceptions
    "AIMException",
    "AgentNotFoundError",
    "CapabilityNotAvailableError",
    "ContextNotFoundError",
    "ConfigurationError",
]

# Package metadata
__package_info__ = {
    "name": "aim-framework",
    "version": __version__,
    "description": "Adaptive Intelligence Mesh - A distributed coordination system for AI deployment and interaction",
    "author": __author__,
    "author_email": __email__,
    "license": __license__,
    "url": "https://github.com/jasonviipers/aim-framework",
    "keywords": [
        "ai",
        "artificial-intelligence",
        "distributed-systems",
        "mesh-network",
        "coordination",
        "agents",
    ],
}
