"""Base notifier class."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class NotificationResult:
    """Result of a notification operation."""

    notifier_type: str
    success: bool
    message: Optional[str] = None
    error_message: Optional[str] = None


class BaseNotifier(ABC):
    """Abstract base class for notifiers."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize notifier.

        Args:
            config: Configuration dictionary for the notifier
        """
        self.config = config

    @abstractmethod
    def notify(self, event: str, data: Dict[str, Any]) -> NotificationResult:
        """Send notification.

        Args:
            event: Event type (e.g., 'backup_start', 'backup_success')
            data: Event data dictionary

        Returns:
            NotificationResult with operation details
        """
        pass

    @abstractmethod
    def validate_config(self) -> bool:
        """Validate notifier configuration.

        Returns:
            True if configuration is valid
        """
        pass
