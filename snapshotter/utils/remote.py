"""Remote backup upload utilities (rsync)."""

import os
import subprocess
from dataclasses import dataclass


@dataclass
class RemoteUploadResult:
    """Result of a remote upload operation."""

    success: bool
    filename: str = ""
    error_message: str = ""
    bytes_transferred: int = 0


def upload_via_rsync(
    file_path: str,
    host: str,
    port: int,
    username: str,
    password: str,
    remote_path: str,
    timeout: int = 60,
) -> RemoteUploadResult:
    """Upload backup file to remote server via rsync.

    Args:
        file_path: Path to local backup file
        host: Remote rsync server hostname
        port: Remote rsync server port
        username: Rsync username
        password: Rsync password
        remote_path: Remote directory path (e.g., 'public/backup-lddm')
        timeout: Upload timeout in seconds

    Returns:
        RemoteUploadResult with success status and details
    """
    try:
        # Validate input
        if not os.path.isfile(file_path):
            return RemoteUploadResult(
                success=False,
                filename=os.path.basename(file_path),
                error_message=f"Backup file not found: {file_path}",
            )

        filename = os.path.basename(file_path)

        # Build rsync URL
        remote_url = f"rsync://{username}@{host}:{port}/{remote_path}/"

        # Prepare environment with password
        env = os.environ.copy()
        env["RSYNC_PASSWORD"] = password

        # Build rsync command
        cmd = [
            "rsync",
            "--timeout",
            str(timeout),
            "-av",
            "--no-R",
            file_path,
            remote_url,
        ]

        # Execute rsync with timeout
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout + 10,  # Add 10s buffer to subprocess timeout
        )

        if result.returncode == 0:
            # Try to extract bytes transferred from rsync output
            bytes_transferred = _parse_rsync_output(result.stdout)
            return RemoteUploadResult(
                success=True,
                filename=filename,
                bytes_transferred=bytes_transferred,
            )
        else:
            error_msg = result.stderr or result.stdout or "Unknown rsync error"
            return RemoteUploadResult(
                success=False,
                filename=filename,
                error_message=f"Rsync failed with code {result.returncode}: {error_msg}",
            )

    except subprocess.TimeoutExpired:
        return RemoteUploadResult(
            success=False,
            filename=os.path.basename(file_path),
            error_message=f"Rsync upload timeout after {timeout} seconds",
        )
    except FileNotFoundError:
        return RemoteUploadResult(
            success=False,
            filename=os.path.basename(file_path),
            error_message="rsync command not found - is rsync installed?",
        )
    except Exception as e:
        return RemoteUploadResult(
            success=False,
            filename=os.path.basename(file_path),
            error_message=f"Unexpected error during upload: {str(e)}",
        )


def _parse_rsync_output(output: str) -> int:
    """Parse rsync output to extract bytes transferred.

    Args:
        output: Rsync stdout output

    Returns:
        Bytes transferred (0 if not found)
    """
    try:
        for line in output.split("\n"):
            if "total transferred file size:" in line.lower():
                # Extract number from line like "total transferred file size: 123,456 bytes"
                parts = line.split()
                for i, part in enumerate(parts):
                    try:
                        # Remove commas and convert to int
                        return int(part.replace(",", ""))
                    except ValueError:
                        continue
    except Exception:
        pass
    return 0
