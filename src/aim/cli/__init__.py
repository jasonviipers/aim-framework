"""
Command-line interface for the AIM Framework.

This package provides command-line tools for managing and interacting
with the AIM Framework, including server management, benchmarking,
and framework initialization.
"""

from .main import init_framework, main, run_benchmark, start_server

__all__ = [
    "main",
    "start_server",
    "run_benchmark",
    "init_framework",
]
