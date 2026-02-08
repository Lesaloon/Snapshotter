"""Custom exceptions for Snapshotter."""


class SnapshatterError(Exception):
    """Base exception for Snapshotter."""

    pass


class ConfigError(SnapshatterError):
    """Raised when configuration is invalid."""

    pass


class BackupError(SnapshatterError):
    """Base exception for backup operations."""

    pass


class DatabaseBackupError(BackupError):
    """Raised when database backup fails."""

    pass


class PrometheusBackupError(BackupError):
    """Raised when Prometheus backup fails."""

    pass


class FilesystemBackupError(BackupError):
    """Raised when filesystem backup fails."""

    pass


class NotificationError(SnapshatterError):
    """Raised when notification fails."""

    pass


class CompressionError(SnapshatterError):
    """Raised when compression fails."""

    pass


class RetentionError(SnapshatterError):
    """Raised when retention cleanup fails."""

    pass
