"""Prometheus backup implementation."""

import shutil
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import requests

from snapshotter.backups.base import BackupResult, BackupTarget
from snapshotter.exceptions import PrometheusBackupError
from snapshotter.utils import calculate_sha256, create_tar_gz, write_checksum


class PrometheusBackup(BackupTarget):
    """Prometheus backup using API snapshot method (zero downtime)."""

    def backup(self, backup_dir: Path) -> BackupResult:
        """Perform Prometheus backup via API snapshot.

        Args:
            backup_dir: Directory to store backup files

        Returns:
            BackupResult with operation details
        """
        start_time = datetime.now()

        try:
            # Get Prometheus URL and data directory from config
            url = self.config.get("url")
            data_dir = self.config.get("data_dir")

            if not url:
                raise PrometheusBackupError("'url' not specified in config")

            if not data_dir:
                raise PrometheusBackupError("'data_dir' not specified in config")

            data_path = Path(data_dir)
            if not data_path.exists():
                raise PrometheusBackupError(
                    f"Data directory does not exist: {data_dir}"
                )

            backup_dir.mkdir(parents=True, exist_ok=True)

            # Request snapshot via API
            snapshot_url = f"{url.rstrip('/')}/api/v1/admin/tsdb/snapshot"

            try:
                response = requests.post(snapshot_url, timeout=30)
                response.raise_for_status()
            except requests.RequestException as e:
                raise PrometheusBackupError(f"Failed to create snapshot: {e}")

            # Extract snapshot directory name
            snapshot_data = response.json()
            if snapshot_data.get("status") != "success":
                raise PrometheusBackupError(
                    f"Snapshot creation failed: {snapshot_data.get('error')}"
                )

            snapshot_dir = snapshot_data.get("data", {}).get("name")
            if not snapshot_dir:
                raise PrometheusBackupError("No snapshot directory name in response")

            # Wait for snapshot to be available
            snapshot_path = data_path / "snapshots" / snapshot_dir
            max_retries = 30
            retry_count = 0

            while retry_count < max_retries:
                if snapshot_path.exists():
                    break

                time.sleep(1)
                retry_count += 1

            if not snapshot_path.exists():
                raise PrometheusBackupError(
                    f"Snapshot directory not found after {max_retries} retries: {snapshot_path}"
                )

            # Create tar.gz from snapshot
            backup_filename = f"prometheus-backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}.tar.gz"
            backup_path = backup_dir / backup_filename

            create_tar_gz(snapshot_path, backup_path)

            # Calculate checksum
            checksum = calculate_sha256(backup_path)
            write_checksum(backup_path, checksum)

            end_time = datetime.now()

            return BackupResult(
                target_name=self.name,
                target_type="prometheus",
                success=True,
                start_time=start_time,
                end_time=end_time,
                backup_file=backup_path,
                checksum=checksum,
                size_bytes=backup_path.stat().st_size,
                metadata={
                    "url": url,
                    "snapshot_dir": snapshot_dir,
                },
            )

        except PrometheusBackupError as e:
            end_time = datetime.now()
            return BackupResult(
                target_name=self.name,
                target_type="prometheus",
                success=False,
                start_time=start_time,
                end_time=end_time,
                error_message=str(e),
            )
        except Exception as e:
            end_time = datetime.now()
            return BackupResult(
                target_name=self.name,
                target_type="prometheus",
                success=False,
                start_time=start_time,
                end_time=end_time,
                error_message=f"Unexpected error: {str(e)}",
            )

    def validate_config(self) -> bool:
        """Validate Prometheus backup configuration.

        Returns:
            True if configuration is valid
        """
        return bool(self.config.get("url")) and bool(self.config.get("data_dir"))
