"""
Knowledge management module for the AIM Framework.

This module contains components for managing knowledge sharing,
learning propagation, and intent prediction across the agent mesh.
"""

from .capsule import KnowledgeCapsule
from .propagator import LearningPropagator
from .intent_graph import IntentGraph

__all__ = [
    "KnowledgeCapsule",
    "LearningPropagator", 
    "IntentGraph",
]

