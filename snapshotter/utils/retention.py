"""Retention policies for Snapshotter."""

from datetime import datetime, timedelta
from pathlib import Path
from typing import List

from snapshotter.exceptions import RetentionError


def find_old_backups(
    backup_dir: Path, pattern: str, days_to_keep: int
) -> List[Path]:
    """Find backup files older than retention period.

    Args:
        backup_dir: Directory containing backups
        pattern: Glob pattern to match backup files (e.g., "*.tar.gz")
        days_to_keep: Number of days to keep backups

    Returns:
        List of Path objects for old backups
    """
    if not backup_dir.exists():
        return []

    cutoff_time = datetime.now() - timedelta(days=days_to_keep)
    old_backups = []

    for backup_file in backup_dir.glob(pattern):
        try:
            file_mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)

            if file_mtime < cutoff_time:
                old_backups.append(backup_file)
        except Exception:
            # Skip files that we can't stat
            continue

    return sorted(old_backups)


def cleanup_old_backups(
    backup_dir: Path, pattern: str, days_to_keep: int
) -> dict:
    """Delete old backup files based on retention policy.

    Args:
        backup_dir: Directory containing backups
        pattern: Glob pattern to match backup files
        days_to_keep: Number of days to keep backups

    Returns:
        Dictionary with cleanup statistics
    """
    try:
        old_backups = find_old_backups(backup_dir, pattern, days_to_keep)

        deleted_count = 0
        freed_space = 0

        for backup_file in old_backups:
            try:
                freed_space += backup_file.stat().st_size

                backup_file.unlink()
                deleted_count += 1

                # Also delete checksum file if it exists
                checksum_file = Path(str(backup_file) + ".sha256")
                if checksum_file.exists():
                    checksum_file.unlink()

            except Exception as e:
                raise RetentionError(f"Failed to delete {backup_file}: {e}")

        return {
            "deleted_count": deleted_count,
            "freed_space_bytes": freed_space,
            "deleted_files": [str(f) for f in old_backups],
        }

    except RetentionError:
        raise
    except Exception as e:
        raise RetentionError(f"Retention cleanup failed: {e}")
