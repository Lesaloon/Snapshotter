"""Test retention module."""

from pathlib import Path
from datetime import datetime, timedelta

import pytest

from snapshotter.utils import cleanup_old_backups, find_old_backups


def test_find_old_backups_empty_dir(temp_dir):
    """Test finding old backups in empty directory."""
    backup_dir = temp_dir / "backups"
    backup_dir.mkdir()

    old_backups = find_old_backups(backup_dir, "*.tar.gz", days_to_keep=7)
    assert len(old_backups) == 0


def test_find_old_backups_with_old_files(temp_dir):
    """Test finding old backup files."""
    backup_dir = temp_dir / "backups"
    backup_dir.mkdir()

    # Create old backup file
    old_file = backup_dir / "old-backup.tar.gz"
    old_file.write_text("old content")

    # Set modification time to 30 days ago
    import time

    old_mtime = time.time() - (30 * 24 * 60 * 60)
    Path(old_file).touch()
    import os

    os.utime(old_file, (old_mtime, old_mtime))

    old_backups = find_old_backups(backup_dir, "*.tar.gz", days_to_keep=7)
    assert len(old_backups) == 1
    assert old_backups[0].name == "old-backup.tar.gz"


def test_find_old_backups_with_recent_files(temp_dir):
    """Test that recent files are not returned."""
    backup_dir = temp_dir / "backups"
    backup_dir.mkdir()

    # Create recent backup file
    recent_file = backup_dir / "recent-backup.tar.gz"
    recent_file.write_text("recent content")

    old_backups = find_old_backups(backup_dir, "*.tar.gz", days_to_keep=7)
    assert len(old_backups) == 0


def test_find_old_backups_nonexistent_dir(temp_dir):
    """Test finding old backups in non-existent directory."""
    backup_dir = temp_dir / "nonexistent"

    old_backups = find_old_backups(backup_dir, "*.tar.gz", days_to_keep=7)
    assert len(old_backups) == 0


def test_cleanup_old_backups_success(temp_dir):
    """Test successful cleanup of old backups."""
    backup_dir = temp_dir / "backups"
    backup_dir.mkdir()

    # Create old backup file
    old_file = backup_dir / "old-backup.tar.gz"
    old_file.write_text("old content")

    # Set modification time to 30 days ago
    import time
    import os

    old_mtime = time.time() - (30 * 24 * 60 * 60)
    os.utime(old_file, (old_mtime, old_mtime))

    # Also create checksum file
    checksum_file = backup_dir / "old-backup.tar.gz.sha256"
    checksum_file.write_text("abc123  old-backup.tar.gz")

    result = cleanup_old_backups(backup_dir, "*.tar.gz", days_to_keep=7)

    assert result["deleted_count"] == 1
    assert not old_file.exists()
    assert not checksum_file.exists()


def test_cleanup_old_backups_preserves_recent(temp_dir):
    """Test that cleanup preserves recent backups."""
    backup_dir = temp_dir / "backups"
    backup_dir.mkdir()

    # Create recent backup file
    recent_file = backup_dir / "recent-backup.tar.gz"
    recent_file.write_text("recent content")

    result = cleanup_old_backups(backup_dir, "*.tar.gz", days_to_keep=7)

    assert result["deleted_count"] == 0
    assert recent_file.exists()
