"""
Logging utilities for the AIM Framework.

This module provides centralized logging configuration and utilities
for the AIM Framework, supporting multiple output formats and levels.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    level: str = "INFO",
    format_string: Optional[str] = None,
    log_file: Optional[str] = None,
    max_file_size: int = 10485760,  # 10MB
    backup_count: int = 5,
) -> None:
    """
    Set up logging configuration for the AIM Framework.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_string: Custom format string for log messages
        log_file: Path to log file (if None, logs to console only)
        max_file_size: Maximum size of log file before rotation
        backup_count: Number of backup files to keep
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Default format string
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Create formatter
    formatter = logging.Formatter(format_string)

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=max_file_size, backupCount=backup_count
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Set specific logger levels for third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the specified name.

    Args:
        name: Name of the logger (typically __name__)

    Returns:
        logging.Logger: Logger instance
    """
    return logging.getLogger(name)


class AIMLogger:
    """
    Custom logger wrapper for the AIM Framework.

    This class provides additional functionality on top of the standard
    Python logging module, including structured logging and context
    information.
    """

    def __init__(self, name: str):
        """
        Initialize the AIM logger.

        Args:
            name: Name of the logger
        """
        self.logger = logging.getLogger(name)
        self.context = {}

    def set_context(self, **kwargs) -> None:
        """
        Set context information for all log messages.

        Args:
            **kwargs: Context key-value pairs
        """
        self.context.update(kwargs)

    def clear_context(self) -> None:
        """Clear all context information."""
        self.context.clear()

    def _format_message(self, message: str) -> str:
        """
        Format message with context information.

        Args:
            message: Original message

        Returns:
            str: Formatted message with context
        """
        if not self.context:
            return message

        context_str = " | ".join(f"{k}={v}" for k, v in self.context.items())
        return f"{message} [{context_str}]"

    def debug(self, message: str, **kwargs) -> None:
        """Log a debug message."""
        self.logger.debug(self._format_message(message), **kwargs)

    def info(self, message: str, **kwargs) -> None:
        """Log an info message."""
        self.logger.info(self._format_message(message), **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Log a warning message."""
        self.logger.warning(self._format_message(message), **kwargs)

    def error(self, message: str, **kwargs) -> None:
        """Log an error message."""
        self.logger.error(self._format_message(message), **kwargs)

    def critical(self, message: str, **kwargs) -> None:
        """Log a critical message."""
        self.logger.critical(self._format_message(message), **kwargs)

    def exception(self, message: str, **kwargs) -> None:
        """Log an exception message with traceback."""
        self.logger.exception(self._format_message(message), **kwargs)


def get_aim_logger(name: str) -> AIMLogger:
    """
    Get an AIM logger instance for the specified name.

    Args:
        name: Name of the logger (typically __name__)

    Returns:
        AIMLogger: AIM logger instance
    """
    return AIMLogger(name)
