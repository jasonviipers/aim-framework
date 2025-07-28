"""
Configuration management for the AIM Framework.

This module provides configuration loading and management capabilities
for the AIM Framework, supporting multiple configuration sources and
environment-based overrides.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class Config:
    """
    Configuration manager for the AIM Framework.

    The Config class provides a centralized way to manage configuration
    settings for the framework, supporting JSON files, environment variables,
    and programmatic configuration.

    Attributes:
        _config (Dict[str, Any]): Internal configuration dictionary
        _config_file (Optional[str]): Path to the configuration file
    """

    def __init__(
        self,
        config_file: Optional[str] = None,
        config_dict: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the configuration manager.

        Args:
            config_file: Path to a JSON configuration file
            config_dict: Dictionary of configuration values
        """
        self._config: Dict[str, Any] = {}
        self._config_file = config_file

        # Load default configuration
        self._load_defaults()

        # Load from file if provided
        if config_file:
            self.load_from_file(config_file)

        # Override with provided dictionary
        if config_dict:
            self.update(config_dict)

        # Apply environment variable overrides
        self._apply_env_overrides()

    def _load_defaults(self) -> None:
        """Load default configuration values."""
        self._config = {
            "framework": {
                "name": "AIM Framework",
                "version": "1.0.0",
                "log_level": "INFO",
                "cleanup_interval": 300.0,
                "start_time": None,
            },
            "agents": {
                "min_agents_per_type": 1,
                "max_agents_per_type": 5,
                "default_timeout": 30.0,
                "heartbeat_interval": 60.0,
                "default_agent_types": [
                    "code_generation",
                    "security_review",
                    "documentation",
                    "data_analysis",
                    "design",
                    "research",
                ],
            },
            "context": {
                "max_threads_per_user": 10,
                "cleanup_interval": 3600.0,
                "default_ttl": 86400.0,
                "max_interactions_per_thread": 100,
            },
            "routing": {
                "default_strategy": "confidence_based",
                "max_routing_depth": 5,
                "routing_timeout": 10.0,
                "enable_caching": True,
                "cache_ttl": 300.0,
            },
            "collaboration": {
                "confidence_threshold": 0.7,
                "max_collaborating_agents": 3,
                "collaboration_timeout": 60.0,
                "enable_consensus": True,
            },
            "scaling": {
                "evaluation_interval": 30.0,
                "scale_up_threshold": 0.8,
                "scale_down_threshold": 0.3,
                "min_idle_time": 300.0,
                "max_scale_factor": 2.0,
            },
            "monitoring": {
                "collection_interval": 60.0,
                "metrics_retention": 86400.0,
                "enable_detailed_metrics": True,
                "alert_thresholds": {
                    "error_rate": 0.1,
                    "response_time": 5.0,
                    "memory_usage": 0.9,
                    "cpu_usage": 0.9,
                },
            },
            "knowledge": {
                "propagation_enabled": True,
                "relevance_threshold": 0.6,
                "max_knowledge_age": 604800.0,  # 7 days
                "cleanup_interval": 3600.0,
            },
            "intent_graph": {
                "max_nodes_per_user": 1000,
                "edge_weight_decay": 0.95,
                "prediction_depth": 3,
                "cleanup_interval": 3600.0,
            },
            "api": {
                "host": "0.0.0.0",
                "port": 5000,
                "debug": False,
                "cors_enabled": True,
                "rate_limiting": {
                    "enabled": True,
                    "requests_per_minute": 60,
                    "burst_size": 10,
                },
            },
            "security": {
                "enable_authentication": False,
                "api_key_required": False,
                "allowed_origins": ["*"],
                "max_request_size": 1048576,  # 1MB
            },
            "performance": {
                "cache_size": 10000,
                "cache_ttl": 3600,
                "load_balancing_strategy": "predictive",
                "enable_compression": True,
                "max_concurrent_requests": 100,
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": None,
                "max_file_size": 10485760,  # 10MB
                "backup_count": 5,
            },
        }

    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides to configuration."""
        # Define environment variable mappings
        env_mappings = {
            "AIM_LOG_LEVEL": "framework.log_level",
            "AIM_API_HOST": "api.host",
            "AIM_API_PORT": "api.port",
            "AIM_API_DEBUG": "api.debug",
            "AIM_CACHE_SIZE": "performance.cache_size",
            "AIM_MAX_AGENTS": "agents.max_agents_per_type",
            "AIM_ENABLE_AUTH": "security.enable_authentication",
        }

        for env_var, config_path in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                self.set(config_path, self._convert_env_value(value))

    def _convert_env_value(self, value: str) -> Union[str, int, float, bool]:
        """
        Convert environment variable string to appropriate type.

        Args:
            value: String value from environment variable

        Returns:
            Union[str, int, float, bool]: Converted value
        """
        # Try boolean conversion
        if value.lower() in ("true", "false"):
            return value.lower() == "true"

        # Try integer conversion
        try:
            return int(value)
        except ValueError:
            pass

        # Try float conversion
        try:
            return float(value)
        except ValueError:
            pass

        # Return as string
        return value

    def load_from_file(self, file_path: str) -> None:
        """
        Load configuration from a JSON file.

        Args:
            file_path: Path to the JSON configuration file

        Raises:
            FileNotFoundError: If the configuration file doesn't exist
            json.JSONDecodeError: If the file contains invalid JSON
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")

        with open(path, "r", encoding="utf-8") as f:
            file_config = json.load(f)

        self._merge_config(file_config)
        self._config_file = file_path

    def save_to_file(self, file_path: Optional[str] = None) -> None:
        """
        Save configuration to a JSON file.

        Args:
            file_path: Path to save the configuration. If None, uses the original file path.

        Raises:
            ValueError: If no file path is provided and no original file path exists
        """
        if file_path is None:
            if self._config_file is None:
                raise ValueError(
                    "No file path provided and no original file path exists"
                )
            file_path = self._config_file

        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(self._config, f, indent=2, sort_keys=True)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.

        Args:
            key: Configuration key in dot notation (e.g., "api.host")
            default: Default value if key is not found

        Returns:
            Any: Configuration value or default
        """
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value using dot notation.

        Args:
            key: Configuration key in dot notation (e.g., "api.host")
            value: Value to set
        """
        keys = key.split(".")
        config = self._config

        # Navigate to the parent dictionary
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        # Set the value
        config[keys[-1]] = value

    def update(self, config_dict: Dict[str, Any]) -> None:
        """
        Update configuration with values from a dictionary.

        Args:
            config_dict: Dictionary of configuration values
        """
        self._merge_config(config_dict)

    def _merge_config(
        self, new_config: Dict[str, Any], target: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Recursively merge configuration dictionaries.

        Args:
            new_config: New configuration to merge
            target: Target dictionary to merge into (defaults to self._config)
        """
        if target is None:
            target = self._config

        for key, value in new_config.items():
            if (
                key in target
                and isinstance(target[key], dict)
                and isinstance(value, dict)
            ):
                self._merge_config(value, target[key])
            else:
                target[key] = value

    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get an entire configuration section.

        Args:
            section: Section name

        Returns:
            Dict[str, Any]: Configuration section
        """
        return self.get(section, {})

    def has(self, key: str) -> bool:
        """
        Check if a configuration key exists.

        Args:
            key: Configuration key in dot notation

        Returns:
            bool: True if key exists, False otherwise
        """
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return False

        return True

    def delete(self, key: str) -> bool:
        """
        Delete a configuration key.

        Args:
            key: Configuration key in dot notation

        Returns:
            bool: True if key was deleted, False if key didn't exist
        """
        keys = key.split(".")
        config = self._config

        # Navigate to the parent dictionary
        for k in keys[:-1]:
            if isinstance(config, dict) and k in config:
                config = config[k]
            else:
                return False

        # Delete the key if it exists
        if isinstance(config, dict) and keys[-1] in config:
            del config[keys[-1]]
            return True

        return False

    def to_dict(self) -> Dict[str, Any]:
        """
        Get the entire configuration as a dictionary.

        Returns:
            Dict[str, Any]: Complete configuration dictionary
        """
        return self._config.copy()

    def validate(self) -> List[str]:
        """
        Validate the configuration and return any errors.

        Returns:
            List[str]: List of validation errors (empty if valid)
        """
        errors = []

        # Validate required fields
        required_fields = [
            "framework.name",
            "framework.version",
            "api.host",
            "api.port",
        ]

        for field in required_fields:
            if not self.has(field):
                errors.append(f"Missing required configuration field: {field}")

        # Validate value ranges
        if self.get("api.port", 0) <= 0 or self.get("api.port", 0) > 65535:
            errors.append("API port must be between 1 and 65535")

        if self.get("agents.max_agents_per_type", 0) <= 0:
            errors.append("Max agents per type must be positive")

        if self.get("context.max_threads_per_user", 0) <= 0:
            errors.append("Max threads per user must be positive")

        return errors

    def __str__(self) -> str:
        """String representation of the configuration."""
        return f"Config(file={self._config_file}, sections={list(self._config.keys())})"

    def __repr__(self) -> str:
        """Detailed string representation of the configuration."""
        return f"Config(config_file='{self._config_file}', config={self._config})"
