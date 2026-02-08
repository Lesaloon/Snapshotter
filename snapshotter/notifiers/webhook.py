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

            # Build webhook payload - match old backup script format for n8n/Discord compatibility
            backups = data.get("backups", [])
            successful = sum(1 for b in backups if b.get("success"))
            total = len(backups)
            total_size_mb = sum(b.get("size_mb", 0) for b in backups)
            
            # Get hostname like old script does
            try:
                hostname = socket.gethostname().split('.')[0]  # Get short hostname
            except Exception:
                hostname = "unknown-host"
            
            # Map event to status like old script does
            if event == "backup_success":
                status = "success"
            elif event == "backup_critical_failure":
                status = "error"
            else:
                status = "partial"
            
            payload = {
                "event": event,
                "status": status,
                "host": hostname,
                "started_at": data.get("timestamp", ""),
                "finished_at": data.get("timestamp", ""),
                "duration_seconds": sum(int(b.get("duration_seconds", 0)) for b in backups),
                "backup_size_human": f"{total_size_mb:.2f} MB",
                "backup_size_bytes": int(total_size_mb * 1024 * 1024),
                "total_backups": total,
                "successful_backups": successful,
                "failed_backups": total - successful,
                "message": self._build_message(event, backups, total_size_mb),
                "backups": backups,
            }

            # Send webhook request
            response = requests.post(
                url,
                json=payload,
                timeout=30,
            )

            if response.status_code in (200, 201, 202, 204):
                return NotificationResult(
                    notifier_type="webhook",
                    success=True,
                    message=f"Webhook sent successfully to {url}",
                )
            else:
                return NotificationResult(
                    notifier_type="webhook",
                    success=False,
                    error_message=f"Webhook returned status {response.status_code}",
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

    def validate_config(self) -> bool:
        """Validate webhook notifier configuration.

        Returns:
            True if configuration is valid
        """
        return bool(self.config.get("url"))

    def _build_message(self, event: str, backups: list, total_size_mb: float) -> str:
        """Build a human-readable message for the webhook.

        Args:
            event: Event type
            backups: List of backup results
            total_size_mb: Total backup size in MB

        Returns:
            Human-readable message string
        """
        successful = sum(1 for b in backups if b.get("success"))
        total = len(backups)
        
        if event == "backup_success":
            return f"✓ Backup completed successfully ({successful}/{total} targets, {total_size_mb:.2f} MB)"
        elif event == "backup_critical_failure":
            return f"✗ Backup failed ({successful}/{total} targets succeeded, {total_size_mb:.2f} MB)"
        else:
            return f"⚠ Backup partially completed ({successful}/{total} targets, {total_size_mb:.2f} MB)"
