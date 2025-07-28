"""
Coordination module for the AIM Framework.

This module contains components responsible for coordinating interactions
between agents, including routing, collaboration, and decision-making.
"""

from .collaborator import ConfidenceBasedCollaborator
from .router import CapabilityRouter

__all__ = [
    "CapabilityRouter",
    "ConfidenceBasedCollaborator",
]
