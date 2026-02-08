"""Logger for Snapshotter."""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional


class SnapshatterLogger:
    """Logger for Snapshotter with file, console, and optional syslog output."""

    def __init__(
        self,
        name: str,
        log_file: Optional[Path] = None,
        level: int = logging.INFO,
        use_syslog: bool = False,
    ):
        """Initialize logger.

        Args:
            name: Logger name
            log_file: Path to log file (if None, only console logging)
            level: Logging level (default: INFO)
            use_syslog: Whether to enable syslog output
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logger.handlers = []

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_format = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)

        # File handler (if log_file provided)
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.handlers.RotatingFileHandler(
                log_file, maxBytes=10 * 1024 * 1024, backupCount=5
            )
            file_handler.setLevel(level)
            file_format = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            file_handler.setFormatter(file_format)
            self.logger.addHandler(file_handler)

        # Syslog handler (if enabled)
        if use_syslog:
            try:
                syslog_handler = logging.handlers.SysLogHandler(address="/dev/log")
                syslog_handler.setLevel(level)
                syslog_format = logging.Formatter(
                    "snapshotter[%(process)d]: %(levelname)s - %(message)s"
                )
                syslog_handler.setFormatter(syslog_format)
                self.logger.addHandler(syslog_handler)
            except Exception as e:
                self.logger.warning(f"Could not setup syslog handler: {e}")

    def debug(self, msg: str) -> None:
        """Log debug message."""
        self.logger.debug(msg)

    def info(self, msg: str) -> None:
        """Log info message."""
        self.logger.info(msg)

    def warning(self, msg: str) -> None:
        """Log warning message."""
        self.logger.warning(msg)

    def error(self, msg: str) -> None:
        """Log error message."""
        self.logger.error(msg)

    def critical(self, msg: str) -> None:
        """Log critical message."""
        self.logger.critical(msg)
