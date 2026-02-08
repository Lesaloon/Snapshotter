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
        "backups": [{"name": "test", "success": True}],
    }

    notifier.notify("backup_complete", test_data)

    # Verify the call was made with correct data
    mock_webhook.assert_called_once()
    call_args = mock_webhook.call_args

    # Check that JSON payload was sent
    assert call_args[1]["json"]["event"] == "backup_complete"
    assert call_args[1]["json"]["data"] == test_data
