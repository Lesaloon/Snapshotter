"""Test database backup module."""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from snapshotter.backups import DatabaseBackup, BackupResult


def test_database_backup_validates_config():
    """Test that DatabaseBackup validates configuration."""
    backup = DatabaseBackup("test", {"container": "postgres"})
    assert backup.validate_config()


def test_database_backup_rejects_invalid_config():
    """Test that DatabaseBackup rejects invalid configuration."""
    backup = DatabaseBackup("test", {})
    assert not backup.validate_config()


def test_database_backup_requires_container(mock_docker):
    """Test that DatabaseBackup requires container in config."""
    backup = DatabaseBackup("test", {})
    result = backup.backup(Path("/tmp/backups"))

    assert not result.success
    assert "container" in result.error_message.lower()


def test_database_backup_success(temp_dir, mock_docker):
    """Test successful database backup."""
    backup_dir = temp_dir / "backups"
    backup_dir.mkdir()

    with patch("snapshotter.backups.database.verify_tar_gz", return_value=True):
        with patch("snapshotter.backups.database.calculate_sha256", return_value="abc123"):
            backup = DatabaseBackup(
                "test-postgres",
                {"container": "postgres"},
            )

            result = backup.backup(backup_dir)

            assert result.success
            assert result.target_name == "test-postgres"
            assert result.target_type == "database"
            assert result.backup_file is not None


def test_database_backup_handles_docker_error(temp_dir):
    """Test database backup handles docker errors."""
    backup_dir = temp_dir / "backups"
    backup_dir.mkdir()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stderr="Connection refused")

        backup = DatabaseBackup("test", {"container": "postgres"})
        result = backup.backup(backup_dir)

        assert not result.success
        assert "pg_dumpall" in result.error_message.lower()


def test_database_backup_result_properties(temp_dir):
    """Test BackupResult properties."""
    start = datetime(2024, 1, 1, 12, 0, 0)
    end = datetime(2024, 1, 1, 12, 5, 30)

    result = BackupResult(
        target_name="test",
        target_type="database",
        success=True,
        start_time=start,
        end_time=end,
        size_bytes=1024 * 1024 * 100,  # 100 MB
    )

    assert result.duration_seconds == 330
    assert result.size_mb == 100.0
