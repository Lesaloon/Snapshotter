"""Filesystem backup implementation."""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from snapshotter.backups.base import BackupResult, BackupTarget
from snapshotter.exceptions import FilesystemBackupError
from snapshotter.utils import calculate_sha256, create_tar_gz, write_checksum


class FilesystemBackup(BackupTarget):
    """Filesystem backup for configuration files."""

    def backup(self, backup_dir: Path) -> BackupResult:
        """Perform filesystem backup.

        Args:
            backup_dir: Directory to store backup files

        Returns:
            BackupResult with operation details
        """
        start_time = datetime.now()

        try:
            # Get paths to backup from config
            paths = self.config.get("paths")
            if not paths:
                raise FilesystemBackupError("'paths' not specified in config")

            if not isinstance(paths, list):
                raise FilesystemBackupError("'paths' must be a list")

            backup_dir.mkdir(parents=True, exist_ok=True)

            # Validate that at least one path exists
            valid_paths = []
            for path_str in paths:
                path = Path(path_str)
                if path.exists():
                    valid_paths.append(path)
                else:
                    # Warn but don't fail
                    pass

            if not valid_paths:
                raise FilesystemBackupError(
                    f"No valid paths to backup: {paths}"
                )

            # Create tar.gz with all valid paths
            backup_filename = f"filesystem-backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}.tar.gz"
            backup_path = backup_dir / backup_filename

            # We'll create a temporary directory to hold symlinks or just compress directly
            # For simplicity, we'll compress the first valid path and add others if multiple
            if len(valid_paths) == 1:
                create_tar_gz(valid_paths[0], backup_path)
            else:
                # For multiple paths, we need to be more careful
                # Create each path with its own structure
                import tarfile

                backup_dir.mkdir(parents=True, exist_ok=True)
                with tarfile.open(backup_path, "w:gz") as tar:
                    for path in valid_paths:
                        tar.add(path, arcname=path.name, recursive=True)

            # Calculate checksum
            checksum = calculate_sha256(backup_path)
            write_checksum(backup_path, checksum)

            end_time = datetime.now()

            return BackupResult(
                target_name=self.name,
                target_type="filesystem",
                success=True,
                start_time=start_time,
                end_time=end_time,
                backup_file=backup_path,
                checksum=checksum,
                size_bytes=backup_path.stat().st_size,
                metadata={
                    "paths_backed_up": len(valid_paths),
                    "paths": [str(p) for p in valid_paths],
                },
            )

        except FilesystemBackupError as e:
            end_time = datetime.now()
            return BackupResult(
                target_name=self.name,
                target_type="filesystem",
                success=False,
                start_time=start_time,
                end_time=end_time,
                error_message=str(e),
            )
        except Exception as e:
            end_time = datetime.now()
            return BackupResult(
                target_name=self.name,
                target_type="filesystem",
                success=False,
                start_time=start_time,
                end_time=end_time,
                error_message=f"Unexpected error: {str(e)}",
            )

    def validate_config(self) -> bool:
        """Validate filesystem backup configuration.

        Returns:
            True if configuration is valid
        """
        paths = self.config.get("paths")
        if not paths or not isinstance(paths, list):
            return False

        return any(Path(path).exists() for path in paths)
