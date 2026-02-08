"""Database backup implementation."""

import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from snapshotter.backups.base import BackupResult, BackupTarget
from snapshotter.exceptions import DatabaseBackupError
from snapshotter.utils import calculate_sha256, create_tar_gz, verify_tar_gz, write_checksum


class DatabaseBackup(BackupTarget):
    """PostgreSQL database backup using docker exec."""

    def backup(self, backup_dir: Path) -> BackupResult:
        """Perform PostgreSQL backup.

        Args:
            backup_dir: Directory to store backup files

        Returns:
            BackupResult with operation details
        """
        start_time = datetime.now()

        try:
            # Get container name from config
            container_name = self.config.get("container")
            if not container_name:
                raise DatabaseBackupError("'container' not specified in config")

            backup_dir.mkdir(parents=True, exist_ok=True)

            # Create temporary file for SQL dump
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".sql", delete=False
            ) as tmp_file:
                tmp_path = Path(tmp_file.name)

            try:
                # Execute pg_dumpall inside container
                cmd = [
                    "docker",
                    "exec",
                    container_name,
                    "pg_dumpall",
                    "-U",
                    "postgres",
                ]

                with open(tmp_path, "w") as f:
                    result = subprocess.run(
                        cmd, stdout=f, stderr=subprocess.PIPE, text=True, timeout=3600
                    )

                if result.returncode != 0:
                    raise DatabaseBackupError(
                        f"pg_dumpall failed: {result.stderr}"
                    )

                # Create tar.gz from SQL dump
                backup_filename = f"database-backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}.tar.gz"
                backup_path = backup_dir / backup_filename

                create_tar_gz(tmp_path, backup_path, arcname="database.sql")

                # Verify archive
                if not verify_tar_gz(backup_path):
                    raise DatabaseBackupError("Archive verification failed")

                # Calculate checksum
                checksum = calculate_sha256(backup_path)
                write_checksum(backup_path, checksum)

                end_time = datetime.now()

                return BackupResult(
                    target_name=self.name,
                    target_type="database",
                    success=True,
                    start_time=start_time,
                    end_time=end_time,
                    backup_file=backup_path,
                    checksum=checksum,
                    size_bytes=backup_path.stat().st_size,
                    metadata={
                        "container": container_name,
                        "database_type": "postgresql",
                    },
                )

            finally:
                # Clean up temporary file
                tmp_path.unlink(missing_ok=True)

        except DatabaseBackupError as e:
            end_time = datetime.now()
            return BackupResult(
                target_name=self.name,
                target_type="database",
                success=False,
                start_time=start_time,
                end_time=end_time,
                error_message=str(e),
            )
        except Exception as e:
            end_time = datetime.now()
            return BackupResult(
                target_name=self.name,
                target_type="database",
                success=False,
                start_time=start_time,
                end_time=end_time,
                error_message=f"Unexpected error: {str(e)}",
            )

    def validate_config(self) -> bool:
        """Validate database backup configuration.

        Returns:
            True if configuration is valid
        """
        return bool(self.config.get("container"))
