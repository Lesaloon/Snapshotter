"""Snapshotter - Unified backup orchestration service."""

__version__ = "1.0.0"
__author__ = "Lesaloon"
__email__ = "contact@example.com"
__license__ = "MIT"

from snapshotter.backups import BackupResult, BackupTarget
from snapshotter.config import Config
from snapshotter.exceptions import SnapshatterError
from snapshotter.logger import SnapshatterLogger
from snapshotter.main import BackupOrchestrator
from snapshotter.notifiers import BaseNotifier, NotificationResult

__all__ = [
    "BackupOrchestrator",
    "BackupResult",
    "BackupTarget",
    "BaseNotifier",
    "Config",
    "NotificationResult",
    "SnapshatterError",
    "SnapshatterLogger",
    "__version__",
]
