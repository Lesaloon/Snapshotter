"""Webhook notifier implementation."""

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

            # Build webhook payload
            payload = {
                "event": event,
                "data": data,
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
