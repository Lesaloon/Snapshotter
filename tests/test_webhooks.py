"""Test webhook notifications."""

from unittest.mock import MagicMock, patch

import pytest

from snapshotter.notifiers import WebhookNotifier


def test_webhook_notifier_validates_config():
    """Test that WebhookNotifier validates configuration."""
    notifier = WebhookNotifier({"url": "http://localhost:5678/webhook"})
    assert notifier.validate_config()


def test_webhook_notifier_rejects_invalid_config():
    """Test that WebhookNotifier rejects invalid configuration."""
    notifier = WebhookNotifier({})
    assert not notifier.validate_config()


def test_webhook_notifier_missing_url():
    """Test that WebhookNotifier fails when URL is missing."""
    notifier = WebhookNotifier({})
    result = notifier.notify("test_event", {"test": "data"})

    assert not result.success
    assert "url" in result.error_message.lower()


def test_webhook_notifier_success(mock_webhook):
    """Test successful webhook notification."""
    notifier = WebhookNotifier({"url": "http://localhost:5678/webhook"})
    result = notifier.notify("backup_success", {"status": "ok"})

    assert result.success
    assert result.notifier_type == "webhook"


def test_webhook_notifier_failed_request():
    """Test webhook notification with failed request."""
    with patch("requests.post") as mock_post:
        mock_post.side_effect = Exception("Connection failed")

        notifier = WebhookNotifier({"url": "http://localhost:5678/webhook"})
        result = notifier.notify("backup_failure", {"error": "test"})

        assert not result.success
        assert "connection" in result.error_message.lower()


def test_webhook_notifier_http_error():
    """Test webhook notification with HTTP error."""
    with patch("requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        notifier = WebhookNotifier({"url": "http://localhost:5678/webhook"})
        result = notifier.notify("backup_error", {})

        assert not result.success
        assert "500" in result.error_message


def test_webhook_notifier_sends_correct_payload(mock_webhook):
    """Test that webhook sends correct payload."""
    notifier = WebhookNotifier({"url": "http://localhost:5678/webhook"})

    test_data = {
        "timestamp": "2024-01-01T12:00:00",
        "dry_run": False,
        "backups": [{"name": "test", "success": True, "size_mb": 10.5, "duration_seconds": 100}],
    }

    notifier.notify("backup_success", test_data)

    # Verify 3 calls were made: summary, per-target, and remote sync
    assert mock_webhook.call_count == 3
    
    # Check first call (summary)
    summary_payload = mock_webhook.call_args_list[0][1]["json"]
    assert summary_payload["event"] == "backup_success"
    assert summary_payload["status"] == "success"
    assert summary_payload["started_at"] == "2024-01-01T12:00:00"
    assert "Backup completed successfully" in summary_payload["message"]
    
    # Check second call (per-target)
    target_payload = mock_webhook.call_args_list[1][1]["json"]
    assert target_payload["event"] == "backup_target_completed"
    assert target_payload["status"] == "success"
    assert "test" in target_payload["message"]
    
    # Check third call (remote sync)
    remote_payload = mock_webhook.call_args_list[2][1]["json"]
    assert remote_payload["event"] == "remote_sync_completed"
    assert remote_payload["status"] == "success"
    assert "Remote sync completed" in remote_payload["message"]
