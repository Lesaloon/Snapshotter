"""Test filesystem backup module."""

from pathlib import Path
from unittest.mock import patch

import pytest

from snapshotter.backups import FilesystemBackup


def test_filesystem_backup_validates_config(temp_dir):
    """Test that FilesystemBackup validates configuration."""
    # Create a test file
    test_file = temp_dir / "test.txt"
    test_file.write_text("test content")

    backup = FilesystemBackup(
        "test",
        {"paths": [str(test_file)]},
    )
    assert backup.validate_config()


def test_filesystem_backup_rejects_invalid_config():
    """Test that FilesystemBackup rejects invalid configuration."""
    backup = FilesystemBackup("test", {})
    assert not backup.validate_config()


def test_filesystem_backup_requires_paths(temp_dir):
    """Test that FilesystemBackup requires paths in config."""
    backup_dir = temp_dir / "backups"
    backup_dir.mkdir()

    backup = FilesystemBackup("test", {})
    result = backup.backup(backup_dir)

    assert not result.success
    assert "paths" in result.error_message.lower()


def test_filesystem_backup_no_valid_paths(temp_dir):
    """Test that FilesystemBackup fails when no paths exist."""
    backup_dir = temp_dir / "backups"
    backup_dir.mkdir()

    backup = FilesystemBackup(
        "test",
        {"paths": ["/nonexistent/path"]},
    )
    result = backup.backup(backup_dir)

    assert not result.success


def test_filesystem_backup_success(temp_dir):
    """Test successful filesystem backup."""
    backup_dir = temp_dir / "backups"
    backup_dir.mkdir()

    # Create test files
    test_dir = temp_dir / "config"
    test_dir.mkdir()
    (test_dir / "app.conf").write_text("test config")

    with patch("snapshotter.backups.filesystem.calculate_sha256", return_value="abc123"):
        backup = FilesystemBackup(
            "test-config",
            {"paths": [str(test_dir)]},
        )

        result = backup.backup(backup_dir)

        assert result.success
        assert result.target_name == "test-config"
        assert result.target_type == "filesystem"
        assert result.backup_file is not None


def test_filesystem_backup_multiple_paths(temp_dir):
    """Test filesystem backup with multiple paths."""
    backup_dir = temp_dir / "backups"
    backup_dir.mkdir()

    # Create multiple test directories
    dir1 = temp_dir / "config1"
    dir1.mkdir()
    (dir1 / "file1.conf").write_text("config1")

    dir2 = temp_dir / "config2"
    dir2.mkdir()
    (dir2 / "file2.conf").write_text("config2")

    with patch("snapshotter.backups.filesystem.calculate_sha256", return_value="abc123"):
        backup = FilesystemBackup(
            "test",
            {"paths": [str(dir1), str(dir2)]},
        )

        result = backup.backup(backup_dir)

        assert result.success
        assert result.metadata["paths_backed_up"] == 2
