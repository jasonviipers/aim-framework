"""
Coordination module for the AIM Framework.

This module contains components responsible for coordinating interactions
between agents, including routing, collaboration, and decision-making.
"""

from .router import CapabilityRouter
from .collaborator import ConfidenceBasedCollaborator

__all__ = [
    "CapabilityRouter",
    "ConfidenceBasedCollaborator",
]

