"""Base backup target class."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class BackupResult:
    """Result of a backup operation."""

    target_name: str
    target_type: str
    backup_file: Optional[Path] = None
    success: bool = False
    error_message: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    size_bytes: int = 0
    checksum: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration_seconds(self) -> float:
        """Get backup duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    @property
    def size_mb(self) -> float:
        """Get backup size in MB."""
        return self.size_bytes / (1024 * 1024) if self.size_bytes > 0 else 0.0


class BackupTarget(ABC):
    """Abstract base class for backup targets."""

    def __init__(self, name: str, config: Dict[str, Any]):
        """Initialize backup target.

        Args:
            name: Name of the backup target
            config: Configuration dictionary for the target
        """
        self.name = name
        self.config = config

    @abstractmethod
    def backup(self, backup_dir: Path) -> BackupResult:
        """Perform backup operation.

        Args:
            backup_dir: Directory to store backup files

        Returns:
            BackupResult with operation details
        """
        pass

    @abstractmethod
    def validate_config(self) -> bool:
        """Validate target configuration.

        Returns:
            True if configuration is valid
        """
        pass
