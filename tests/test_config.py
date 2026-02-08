"""Test configuration module."""

import pytest
import yaml

from snapshotter.config import Config
from snapshotter.exceptions import ConfigError


def test_config_loads_valid_file(sample_config_file):
    """Test that valid configuration file loads successfully."""
    config = Config(sample_config_file)
    assert config.data is not None
    assert "backups" in config.data


def test_config_raises_error_for_missing_file(temp_dir):
    """Test that ConfigError is raised for missing file."""
    missing_file = temp_dir / "nonexistent.yaml"
    with pytest.raises(ConfigError):
        Config(missing_file)


def test_config_raises_error_for_invalid_yaml(temp_dir):
    """Test that ConfigError is raised for invalid YAML."""
    invalid_file = temp_dir / "invalid.yaml"
    invalid_file.write_text("invalid: yaml: content:")
    with pytest.raises(ConfigError):
        Config(invalid_file)


def test_config_get_with_dot_notation(sample_config):
    """Test configuration value retrieval with dot notation."""
    level = sample_config.get("logging.level")
    assert level == "INFO"


def test_config_get_with_default(sample_config):
    """Test configuration value retrieval with default."""
    value = sample_config.get("nonexistent.key", "default_value")
    assert value == "default_value"


def test_config_get_backups(sample_config):
    """Test getting backup configurations."""
    backups = sample_config.get_backups()
    assert len(backups) > 0
    assert all("type" in backup for backup in backups)


def test_config_get_notifications(sample_config):
    """Test getting notification configuration."""
    notifications = sample_config.get_notifications()
    assert notifications is not None
    assert "webhook" in notifications


def test_config_get_retention(sample_config):
    """Test getting retention configuration."""
    retention = sample_config.get_retention()
    assert retention is not None
    assert "database" in retention


def test_config_get_logging(sample_config):
    """Test getting logging configuration."""
    logging = sample_config.get_logging()
    assert logging["level"] == "INFO"
    assert "file" in logging


def test_config_environment_variable_substitution(temp_dir):
    """Test that environment variables are substituted."""
    import os

    os.environ["TEST_BACKUP_DIR"] = "/test/backup"

    config_data = {
        "backup_dir": "${TEST_BACKUP_DIR}",
        "backups": [{"type": "database", "name": "test", "container": "postgres"}],
    }

    config_file = temp_dir / "config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    config = Config(config_file)
    assert config.get("backup_dir") == "/test/backup"


def test_config_validates_missing_backups(temp_dir):
    """Test that validation fails when backups section is missing."""
    config_data = {"backup_dir": "/backups"}

    config_file = temp_dir / "invalid_config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    with pytest.raises(ConfigError):
        Config(config_file)


def test_config_validates_empty_backups(temp_dir):
    """Test that validation fails when backups list is empty."""
    config_data = {
        "backup_dir": "/backups",
        "backups": [],
    }

    config_file = temp_dir / "invalid_config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    with pytest.raises(ConfigError):
        Config(config_file)


def test_config_validates_invalid_backup_type(temp_dir):
    """Test that validation fails for invalid backup type."""
    config_data = {
        "backup_dir": "/backups",
        "backups": [{"type": "invalid_type", "name": "test"}],
    }

    config_file = temp_dir / "invalid_config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    with pytest.raises(ConfigError):
        Config(config_file)
