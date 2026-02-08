"""Test Prometheus backup module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from snapshotter.backups import PrometheusBackup


def test_prometheus_backup_validates_config():
    """Test that PrometheusBackup validates configuration."""
    backup = PrometheusBackup(
        "test",
        {"url": "http://localhost:9090", "data_dir": "/srv/prometheus"},
    )
    assert backup.validate_config()


def test_prometheus_backup_rejects_invalid_config():
    """Test that PrometheusBackup rejects invalid configuration."""
    backup = PrometheusBackup("test", {})
    assert not backup.validate_config()


def test_prometheus_backup_requires_url(temp_dir):
    """Test that PrometheusBackup requires URL in config."""
    backup_dir = temp_dir / "backups"
    backup_dir.mkdir()

    backup = PrometheusBackup("test", {"data_dir": "/srv/prometheus"})
    result = backup.backup(backup_dir)

    assert not result.success
    assert "url" in result.error_message.lower()


def test_prometheus_backup_requires_data_dir(temp_dir):
    """Test that PrometheusBackup requires data_dir in config."""
    backup_dir = temp_dir / "backups"
    backup_dir.mkdir()

    backup = PrometheusBackup("test", {"url": "http://localhost:9090"})
    result = backup.backup(backup_dir)

    assert not result.success
    assert "data_dir" in result.error_message.lower()


def test_prometheus_backup_success(temp_dir, mock_prometheus_api):
    """Test successful Prometheus backup."""
    backup_dir = temp_dir / "backups"
    backup_dir.mkdir()

    # Create prometheus data directory structure
    prom_data = temp_dir / "prometheus-data"
    snapshots_dir = prom_data / "snapshots"
    snapshot_dir = snapshots_dir / "20240101T120000Z-1234567890abcdef"
    snapshot_dir.mkdir(parents=True)

    with patch("snapshotter.backups.prometheus.calculate_sha256", return_value="abc123"):
        backup = PrometheusBackup(
            "test-prometheus",
            {"url": "http://localhost:9090", "data_dir": str(prom_data)},
        )

        result = backup.backup(backup_dir)

        assert result.success
        assert result.target_name == "test-prometheus"
        assert result.target_type == "prometheus"


def test_prometheus_backup_api_error(temp_dir):
    """Test Prometheus backup handles API errors."""
    backup_dir = temp_dir / "backups"
    backup_dir.mkdir()

    prom_data = temp_dir / "prometheus-data"
    prom_data.mkdir()

    with patch("requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        backup = PrometheusBackup(
            "test",
            {"url": "http://localhost:9090", "data_dir": str(prom_data)},
        )

        result = backup.backup(backup_dir)

        assert not result.success
        assert result.error_message is not None
