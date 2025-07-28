"""
Resource management module for the AIM Framework.

This module contains components for managing system resources,
including adaptive scaling and performance monitoring.
"""

from .monitor import PerformanceMonitor
from .scaler import AdaptiveResourceScaler

__all__ = [
    "AdaptiveResourceScaler",
    "PerformanceMonitor",
]
