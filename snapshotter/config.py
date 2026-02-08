"""Configuration management for Snapshotter."""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from snapshotter.exceptions import ConfigError


class Config:
    """Load and manage configuration from YAML file."""

    def __init__(self, config_file: Path):
        """Initialize configuration.

        Args:
            config_file: Path to YAML configuration file

        Raises:
            ConfigError: If config file is invalid or missing
        """
        if not config_file.exists():
            raise ConfigError(f"Configuration file not found: {config_file}")

        try:
            with open(config_file, "r") as f:
                self.data = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise ConfigError(f"Invalid YAML configuration: {e}")
        except Exception as e:
            raise ConfigError(f"Failed to load configuration: {e}")

        self._substitute_env_vars()
        self._validate()

    def _substitute_env_vars(self) -> None:
        """Recursively substitute environment variables in config."""

        def substitute(obj: Any) -> Any:
            if isinstance(obj, str):
                # Replace ${VAR_NAME} with environment variable value
                import re

                def replace_var(match):
                    var_name = match.group(1)
                    return os.getenv(var_name, match.group(0))

                return re.sub(r"\$\{([^}]+)\}", replace_var, obj)
            elif isinstance(obj, dict):
                return {k: substitute(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [substitute(item) for item in obj]
            return obj

        self.data = substitute(self.data)

    def _validate(self) -> None:
        """Validate configuration structure."""
        if not isinstance(self.data, dict):
            raise ConfigError("Configuration must be a dictionary")

        # Validate backup targets
        if "backups" not in self.data:
            raise ConfigError("Configuration must contain 'backups' section")

        backups = self.data.get("backups")
        if not isinstance(backups, list):
            raise ConfigError("'backups' must be a list")

        if not backups:
            raise ConfigError("'backups' list cannot be empty")

        for idx, backup in enumerate(backups):
            if not isinstance(backup, dict):
                raise ConfigError(f"Backup {idx} must be a dictionary")

            if "type" not in backup:
                raise ConfigError(f"Backup {idx} must have 'type' field")

            backup_type = backup.get("type")
            if backup_type not in ["database", "prometheus", "filesystem"]:
                raise ConfigError(
                    f"Backup {idx} has invalid type: {backup_type}. "
                    "Must be 'database', 'prometheus', or 'filesystem'"
                )

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value.

        Args:
            key: Configuration key (supports dot notation for nested keys)
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        keys = key.split(".")
        value = self.data

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value if value is not None else default

    def get_backups(self) -> list:
        """Get list of backup configurations.

        Returns:
            List of backup target dictionaries
        """
        return self.data.get("backups", [])

    def get_notifications(self) -> Optional[Dict[str, Any]]:
        """Get notification configuration.

        Returns:
            Notification configuration dictionary or None
        """
        return self.data.get("notifications")

    def get_retention(self) -> Optional[Dict[str, Any]]:
        """Get retention configuration.

        Returns:
            Retention configuration dictionary or None
        """
        return self.data.get("retention", {})

    def get_logging(self) -> Dict[str, Any]:
        """Get logging configuration.

        Returns:
            Logging configuration dictionary with defaults
        """
        logging_config = self.data.get("logging", {})
        return {
            "level": logging_config.get("level", "INFO"),
            "file": logging_config.get("file", "/srv/backups/logs/snapshotter.log"),
            "use_syslog": logging_config.get("use_syslog", False),
        }

    def get_remote_upload(self) -> Optional[Dict[str, Any]]:
        """Get remote upload (rsync) configuration.

        Returns:
            Remote upload configuration dictionary or None
        """
        return self.data.get("remote_upload")
