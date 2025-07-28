"""
API module for the AIM Framework.

This module provides REST API and client interfaces for
interacting with the AIM Framework.
"""

from .server import AIMServer
from .client import AIMClient

__all__ = [
    "AIMServer",
    "AIMClient",
]

