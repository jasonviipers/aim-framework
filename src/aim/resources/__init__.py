"""
Resource management module for the AIM Framework.

This module contains components for managing system resources,
including adaptive scaling and performance monitoring.
"""

from .scaler import AdaptiveResourceScaler
from .monitor import PerformanceMonitor

__all__ = [
    "AdaptiveResourceScaler",
    "PerformanceMonitor",
]

