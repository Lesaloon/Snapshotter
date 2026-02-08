"""Pytest configuration and fixtures."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
import yaml

from snapshotter.config import Config
from snapshotter.logger import SnapshatterLogger


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_logger(temp_dir):
    """Create a mock logger for testing."""
    log_file = temp_dir / "test.log"
    return SnapshatterLogger(
        name="test_logger",
        log_file=log_file,
        level=10,  # DEBUG
        use_syslog=False,
    )


@pytest.fixture
def sample_config(temp_dir):
    """Create a sample configuration file for testing."""
    config_data = {
        "backup_dir": str(temp_dir / "backups"),
        "logging": {
            "level": "INFO",
            "file": str(temp_dir / "snapshotter.log"),
            "use_syslog": False,
        },
        "backups": [
            {
                "type": "database",
                "name": "test-postgres",
                "container": "test-postgres-container",
            },
            {
                "type": "prometheus",
                "name": "test-prometheus",
                "url": "http://localhost:9090",
                "data_dir": str(temp_dir / "prometheus-data"),
            },
            {
                "type": "filesystem",
                "name": "test-config",
                "paths": [str(temp_dir / "config")],
            },
        ],
        "retention": {
            "database": 30,
            "prometheus": 14,
            "filesystem": 7,
        },
        "notifications": {
            "webhook": {
                "url": "http://localhost:5678/webhook",
            }
        },
    }

    config_file = temp_dir / "snapshotter-config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    return Config(config_file)


@pytest.fixture
def sample_config_file(temp_dir):
    """Create and return path to a sample configuration file."""
    config_data = {
        "backup_dir": str(temp_dir / "backups"),
        "backups": [
            {
                "type": "database",
                "name": "test-postgres",
                "container": "postgres",
            },
        ],
        "retention": {"database": 30},
    }

    config_file = temp_dir / "snapshotter-config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    return config_file


@pytest.fixture
def mock_docker():
    """Mock docker subprocess calls."""
    with patch("subprocess.run") as mock_run:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        yield mock_run


@pytest.fixture
def mock_prometheus_api():
    """Mock Prometheus API calls."""
    with patch("requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "data": {"name": "20240101T120000Z-1234567890abcdef"},
        }
        mock_post.return_value = mock_response
        yield mock_post


@pytest.fixture
def mock_webhook():
    """Mock webhook requests."""
    with patch("requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        yield mock_post


@pytest.fixture
def sample_backup_dir(temp_dir):
    """Create a sample backup directory structure."""
    backup_dir = temp_dir / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    # Create subdirectories for each backup type
    (backup_dir / "database").mkdir()
    (backup_dir / "prometheus").mkdir()
    (backup_dir / "filesystem").mkdir()

    return backup_dir


@pytest.fixture
def sample_backup_files(sample_backup_dir):
    """Create sample backup files."""
    files = {}

    # Database backup
    db_file = sample_backup_dir / "database" / "backup-20240101-120000.tar.gz"
    db_file.write_text("fake database backup content")
    files["database"] = db_file

    # Prometheus backup
    prom_file = sample_backup_dir / "prometheus" / "backup-20240101-120000.tar.gz"
    prom_file.write_text("fake prometheus backup content")
    files["prometheus"] = prom_file

    # Filesystem backup
    fs_file = sample_backup_dir / "filesystem" / "backup-20240101-120000.tar.gz"
    fs_file.write_text("fake filesystem backup content")
    files["filesystem"] = fs_file

    return files
