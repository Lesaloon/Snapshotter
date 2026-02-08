"""Test remote upload (rsync) functionality."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from snapshotter.utils.remote import RemoteUploadResult, upload_via_rsync


@pytest.fixture
def temp_backup_file(tmp_path):
    """Create a temporary backup file for testing."""
    backup_file = tmp_path / "test-backup.tar.gz"
    backup_file.write_text("test backup content")
    return backup_file


def test_upload_via_rsync_file_not_found():
    """Test rsync upload fails when file doesn't exist."""
    result = upload_via_rsync(
        file_path="/nonexistent/file.tar.gz",
        host="test.local",
        port=873,
        username="testuser",
        password="testpass",
        remote_path="backups",
    )

    assert not result.success
    assert "not found" in result.error_message.lower()


def test_upload_via_rsync_success(temp_backup_file):
    """Test successful rsync upload."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="total transferred file size: 1,024 bytes\n",
            stderr="",
        )

        result = upload_via_rsync(
            file_path=str(temp_backup_file),
            host="test.local",
            port=873,
            username="testuser",
            password="testpass",
            remote_path="backups",
        )

        assert result.success
        assert result.filename == "test-backup.tar.gz"
        assert result.bytes_transferred == 1024
        mock_run.assert_called_once()


def test_upload_via_rsync_command_not_found(temp_backup_file):
    """Test rsync upload fails when rsync command is not found."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError("rsync not found")

        result = upload_via_rsync(
            file_path=str(temp_backup_file),
            host="test.local",
            port=873,
            username="testuser",
            password="testpass",
            remote_path="backups",
        )

        assert not result.success
        assert "not found" in result.error_message.lower()


def test_upload_via_rsync_timeout(temp_backup_file):
    """Test rsync upload timeout."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired("rsync", 60)

        result = upload_via_rsync(
            file_path=str(temp_backup_file),
            host="test.local",
            port=873,
            username="testuser",
            password="testpass",
            remote_path="backups",
            timeout=60,
        )

        assert not result.success
        assert "timeout" in result.error_message.lower()


def test_upload_via_rsync_error(temp_backup_file):
    """Test rsync upload with non-zero exit code."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Permission denied",
        )

        result = upload_via_rsync(
            file_path=str(temp_backup_file),
            host="test.local",
            port=873,
            username="testuser",
            password="testpass",
            remote_path="backups",
        )

        assert not result.success
        assert "Permission denied" in result.error_message


def test_upload_via_rsync_uses_password_env(temp_backup_file):
    """Test that rsync upload sets RSYNC_PASSWORD environment variable."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        upload_via_rsync(
            file_path=str(temp_backup_file),
            host="test.local",
            port=873,
            username="testuser",
            password="secretpass",
            remote_path="backups",
        )

        # Verify the call
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        env = call_args[1]["env"]
        assert env["RSYNC_PASSWORD"] == "secretpass"


def test_upload_via_rsync_command_format(temp_backup_file):
    """Test that rsync upload uses correct command format."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        upload_via_rsync(
            file_path=str(temp_backup_file),
            host="test.local",
            port=873,
            username="testuser",
            password="testpass",
            remote_path="backups",
            timeout=120,
        )

        # Verify the command
        call_args = mock_run.call_args
        cmd = call_args[0][0]
        assert cmd[0] == "rsync"
        assert "--timeout" in cmd
        assert "-av" in cmd
        assert "--no-R" in cmd
        assert str(temp_backup_file) in cmd
        assert "rsync://testuser@test.local:873/backups/" in cmd


def test_remote_upload_result_dataclass():
    """Test RemoteUploadResult dataclass."""
    result = RemoteUploadResult(
        success=True,
        filename="backup.tar.gz",
        bytes_transferred=1024,
    )

    assert result.success
    assert result.filename == "backup.tar.gz"
    assert result.bytes_transferred == 1024
    assert result.error_message == ""


# Import subprocess for timeout test
import subprocess
