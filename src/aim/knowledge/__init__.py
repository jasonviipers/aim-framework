"""
Knowledge management module for the AIM Framework.

This module contains components for managing knowledge sharing,
learning propagation, and intent prediction across the agent mesh.
"""

from .capsule import KnowledgeCapsule
from .intent_graph import IntentGraph
from .propagator import LearningPropagator

__all__ = [
    "KnowledgeCapsule",
    "LearningPropagator",
    "IntentGraph",
]
