"""
API module for the AIM Framework.

This module provides REST API and client interfaces for
interacting with the AIM Framework.
"""

from .client import AIMClient
from .server import AIMServer

__all__ = [
    "AIMServer",
    "AIMClient",
]
