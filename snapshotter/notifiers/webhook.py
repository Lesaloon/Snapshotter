"""Webhook notifier implementation."""

import socket
from typing import Any, Dict

import requests

from snapshotter.notifiers.base import BaseNotifier, NotificationResult


class WebhookNotifier(BaseNotifier):
    """Webhook notifier for sending events to n8n or other webhook services."""

    def notify(self, event: str, data: Dict[str, Any]) -> NotificationResult:
        """Send notification via webhook.

        Args:
            event: Event type (e.g., 'backup_success')
            data: Event data dictionary

        Returns:
            NotificationResult with operation details
        """
        try:
            url = self.config.get("url")
            if not url:
                return NotificationResult(
                    notifier_type="webhook",
                    success=False,
                    error_message="Webhook URL not configured",
                )

            # Get hostname
            try:
                hostname = socket.gethostname().split('.')[0]  # Get short hostname
            except Exception:
                hostname = "unknown-host"

            backups = data.get("backups", [])
            successful = sum(1 for b in backups if b.get("success"))
            total = len(backups)
            total_size_mb = sum(b.get("size_mb", 0) for b in backups)
            timestamp = data.get("timestamp", "")

            # Send initial summary message
            summary_payload = {
                "event": event,
                "status": self._event_to_status(event),
                "host": hostname,
                "started_at": timestamp,
                "message": self._build_summary_message(event, successful, total, total_size_mb),
            }
            
            response = requests.post(url, json=summary_payload, timeout=30)
            if response.status_code not in (200, 201, 202, 204):
                return NotificationResult(
                    notifier_type="webhook",
                    success=False,
                    error_message=f"Webhook returned status {response.status_code}",
                )

            # Send a message for each backup target
            for backup in backups:
                backup_payload = {
                    "event": "backup_target_completed",
                    "status": "success" if backup.get("success") else "error",
                    "host": hostname,
                    "started_at": timestamp,
                    "message": self._build_target_message(backup),
                }
                response = requests.post(url, json=backup_payload, timeout=30)
                if response.status_code not in (200, 201, 202, 204):
                    return NotificationResult(
                        notifier_type="webhook",
                        success=False,
                        error_message=f"Webhook returned status {response.status_code}",
                    )

            # Send remote sync message if all backups succeeded
            if event == "backup_success" and backups:
                remote_payload = {
                    "event": "remote_sync_completed",
                    "status": "success",
                    "host": hostname,
                    "started_at": timestamp,
                    "message": f"✓ Remote sync completed for {total} backup(s) on {hostname}",
                }
                response = requests.post(url, json=remote_payload, timeout=30)
                if response.status_code not in (200, 201, 202, 204):
                    return NotificationResult(
                        notifier_type="webhook",
                        success=False,
                        error_message=f"Webhook returned status {response.status_code}",
                    )

            return NotificationResult(
                notifier_type="webhook",
                success=True,
                message=f"Webhook sent successfully to {url}",
            )

        except requests.RequestException as e:
            return NotificationResult(
                notifier_type="webhook",
                success=False,
                error_message=f"Webhook request failed: {str(e)}",
            )
        except Exception as e:
            return NotificationResult(
                notifier_type="webhook",
                success=False,
                error_message=f"Unexpected error: {str(e)}",
            )

    def _event_to_status(self, event: str) -> str:
        """Map event to status."""
        if event == "backup_success":
            return "success"
        elif event == "backup_critical_failure":
            return "error"
        else:
            return "partial"

    def _build_summary_message(self, event: str, successful: int, total: int, total_size_mb: float) -> str:
        """Build initial summary message."""
        if event == "backup_success":
            return f"✓ Backup completed successfully ({successful}/{total} targets, {total_size_mb:.2f} MB)"
        elif event == "backup_critical_failure":
            return f"✗ Backup failed ({successful}/{total} targets succeeded, {total_size_mb:.2f} MB)"
        else:
            return f"⚠ Backup partially completed ({successful}/{total} targets, {total_size_mb:.2f} MB)"

    def _build_target_message(self, backup: Dict[str, Any]) -> str:
        """Build per-target backup message."""
        name = backup.get("name", "unknown")
        success = backup.get("success", False)
        size_mb = backup.get("size_mb", 0)
        duration = backup.get("duration_seconds", 0)
        error = backup.get("error")
        
        if success:
            # Format size intelligently: show KB for small files, MB for larger
            if size_mb < 1:
                size_kb = size_mb * 1024
                size_str = f"{size_kb:.0f} KB"
            else:
                size_str = f"{size_mb:.2f} MB"
            
            # Format duration with decimals for sub-second precision
            if duration < 1:
                duration_str = f"{duration:.1f}s"
            else:
                duration_str = f"{int(duration)}s"
            
            return f"✓ {name}: {size_str} in {duration_str}"
        else:
            return f"✗ {name}: {error or 'Failed'}"

    def validate_config(self) -> bool:
        """Validate webhook notifier configuration.

        Returns:
            True if configuration is valid
        """
        return bool(self.config.get("url"))