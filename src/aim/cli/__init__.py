"""
Command-line interface for the AIM Framework.

This package provides command-line tools for managing and interacting
with the AIM Framework, including server management, benchmarking,
and framework initialization.
"""

from .main import main, start_server, run_benchmark, init_framework

__all__ = [
    "main",
    "start_server", 
    "run_benchmark",
    "init_framework",
]

