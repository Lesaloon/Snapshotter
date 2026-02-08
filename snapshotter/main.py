"""Main backup orchestrator."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from snapshotter.backups import (
    BackupResult,
    DatabaseBackup,
    FilesystemBackup,
    PrometheusBackup,
)
from snapshotter.config import Config
from snapshotter.exceptions import SnapshatterError
from snapshotter.logger import SnapshatterLogger
from snapshotter.notifiers import WebhookNotifier
from snapshotter.utils import cleanup_old_backups


class BackupOrchestrator:
    """Main orchestrator for coordinating backups."""

    def __init__(self, config: Config, logger: SnapshatterLogger, dry_run: bool = False):
        """Initialize orchestrator.

        Args:
            config: Configuration object
            logger: Logger instance
            dry_run: If True, preview without performing backups
        """
        self.config = config
        self.logger = logger
        self.dry_run = dry_run
        self.results: List[BackupResult] = []
        self.backup_start_time = datetime.now()

    def run(self) -> bool:
        """Execute backup orchestration.

        Returns:
            True if all backups succeeded, False if any failed
        """
        try:
            self.logger.info(f"Starting backup orchestration (dry_run={self.dry_run})")

            if self.dry_run:
                self.logger.info("DRY RUN MODE - No backups will be performed")

            # Get backup configuration
            backup_configs = self.config.get_backups()
            if not backup_configs:
                self.logger.error("No backup targets configured")
                return False

            backup_dir = Path(self.config.get("backup_dir", "/srv/backups"))

            # Execute each backup
            for backup_config in backup_configs:
                self._execute_backup(backup_config, backup_dir)

            # Execute retention cleanup
            self._execute_retention(backup_dir)

            # Send notifications
            self._send_notifications()

            # Log summary
            self._log_summary()

            # Return success status
            return self._is_all_success()

        except Exception as e:
            self.logger.error(f"Orchestration failed: {e}")
            return False

    def _execute_backup(self, backup_config: Dict[str, Any], backup_dir: Path) -> None:
        """Execute a single backup target.

        Args:
            backup_config: Backup configuration dictionary
            backup_dir: Base backup directory
        """
        backup_type: Optional[str] = backup_config.get("type")
        backup_name: Optional[str] = backup_config.get("name", backup_type)

        # Ensure we have string values
        backup_type_str = backup_type or "unknown"
        backup_name_str = backup_name or "unnamed"

        self.logger.info(f"Executing backup: {backup_name_str} (type: {backup_type_str})")

        try:
            if self.dry_run:
                # In dry-run mode, just log what would happen
                self.logger.info(f"[DRY RUN] Would backup {backup_name_str}")
                result = BackupResult(
                    target_name=backup_name_str,
                    target_type=backup_type_str,
                    success=True,
                    start_time=datetime.now(),
                    end_time=datetime.now(),
                    metadata={"dry_run": True},
                )
                self.results.append(result)
                return

            # Create backup target instance
            if backup_type == "database":
                target = DatabaseBackup(backup_name_str, backup_config)
            elif backup_type == "prometheus":
                target = PrometheusBackup(backup_name_str, backup_config)
            elif backup_type == "filesystem":
                target = FilesystemBackup(backup_name_str, backup_config)
            else:
                self.logger.error(f"Unknown backup type: {backup_type_str}")
                result = BackupResult(
                    target_name=backup_name_str,
                    target_type=backup_type_str,
                    success=False,
                    start_time=datetime.now(),
                    end_time=datetime.now(),
                    error_message=f"Unknown backup type: {backup_type_str}",
                )
                self.results.append(result)
                return

            # Validate configuration
            if not target.validate_config():
                self.logger.error(f"Invalid configuration for {backup_name_str}")
                result = BackupResult(
                    target_name=backup_name_str,
                    target_type=backup_type_str,
                    success=False,
                    start_time=datetime.now(),
                    end_time=datetime.now(),
                    error_message="Invalid configuration",
                )
                self.results.append(result)
                return

            # Create type-specific backup directory
            type_backup_dir = backup_dir / backup_type_str
            type_backup_dir.mkdir(parents=True, exist_ok=True)

            # Execute backup
            result = target.backup(type_backup_dir)
            self.results.append(result)

            if result.success:
                self.logger.info(
                    f"Backup successful: {backup_name_str} ({result.size_mb:.2f} MB)"
                )
            else:
                self.logger.error(f"Backup failed: {backup_name_str} - {result.error_message}")

        except Exception as e:
            self.logger.error(f"Backup execution error for {backup_name_str}: {e}")
            result = BackupResult(
                target_name=backup_name_str,
                target_type=backup_type_str,
                success=False,
                start_time=datetime.now(),
                end_time=datetime.now(),
                error_message=f"Execution error: {str(e)}",
            )
            self.results.append(result)

    def _execute_retention(self, backup_dir: Path) -> None:
        """Execute retention cleanup.

        Args:
            backup_dir: Base backup directory
        """
        if self.dry_run:
            self.logger.info("[DRY RUN] Would clean up old backups")
            return

        retention_config = self.config.get_retention()
        if not retention_config:
            self.logger.info("No retention policy configured")
            return

        self.logger.info("Executing retention cleanup")

        for backup_type, days_to_keep in retention_config.items():
            try:
                type_backup_dir = backup_dir / backup_type
                if not type_backup_dir.exists():
                    continue

                cleanup_result = cleanup_old_backups(
                    type_backup_dir, "*.tar.gz", days_to_keep
                )

                self.logger.info(
                    f"Retention cleanup ({backup_type}): "
                    f"deleted {cleanup_result['deleted_count']} files, "
                    f"freed {cleanup_result['freed_space_bytes'] / (1024*1024):.2f} MB"
                )

            except Exception as e:
                self.logger.error(f"Retention cleanup failed for {backup_type}: {e}")

    def _send_notifications(self) -> None:
        """Send notifications about backup results."""
        notifications_config = self.config.get_notifications()
        if not notifications_config:
            return

        self.logger.info("Sending notifications")

        # Prepare notification data
        notification_data = {
            "timestamp": datetime.now().isoformat(),
            "dry_run": self.dry_run,
            "backups": [
                {
                    "name": r.target_name,
                    "type": r.target_type,
                    "success": r.success,
                    "duration_seconds": int(r.duration_seconds),
                    "size_mb": r.size_mb,
                    "error": r.error_message,
                }
                for r in self.results
            ],
        }

        # Determine event type
        if self._is_all_success():
            event_type = "backup_success"
        elif any(r.success for r in self.results):
            event_type = "backup_partial_failure"
        else:
            event_type = "backup_critical_failure"

        # Send to all configured notifiers
        if "webhook" in notifications_config:
            webhook_config = notifications_config["webhook"]
            if isinstance(webhook_config, dict):
                notifier = WebhookNotifier(webhook_config)
                if notifier.validate_config():
                    result = notifier.notify(event_type, notification_data)
                    if result.success:
                        self.logger.info("Notification sent successfully")
                    else:
                        self.logger.warning(
                            f"Notification failed: {result.error_message}"
                        )

    def _log_summary(self) -> None:
        """Log backup summary."""
        total_backups = len(self.results)
        successful_backups = sum(1 for r in self.results if r.success)
        failed_backups = total_backups - successful_backups
        total_size_mb = sum(r.size_mb for r in self.results)

        total_duration = datetime.now() - self.backup_start_time

        self.logger.info("=" * 60)
        self.logger.info("BACKUP SUMMARY")
        self.logger.info("=" * 60)
        self.logger.info(f"Total backups: {total_backups}")
        self.logger.info(f"Successful: {successful_backups}")
        self.logger.info(f"Failed: {failed_backups}")
        self.logger.info(f"Total size: {total_size_mb:.2f} MB")
        self.logger.info(f"Total duration: {total_duration.total_seconds():.2f} seconds")
        self.logger.info("=" * 60)

    def _is_all_success(self) -> bool:
        """Check if all backups succeeded.

        Returns:
            True if all backups succeeded
        """
        return all(r.success for r in self.results) and len(self.results) > 0
