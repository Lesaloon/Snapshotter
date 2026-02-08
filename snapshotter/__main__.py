"""CLI entry point for Snapshotter."""

import argparse
import logging
import sys
from pathlib import Path

from snapshotter import __version__
from snapshotter.config import Config
from snapshotter.exceptions import ConfigError
from snapshotter.logger import SnapshatterLogger
from snapshotter.main import BackupOrchestrator


def main() -> int:
    """Main CLI entry point.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    parser = argparse.ArgumentParser(
        description="Snapshotter - Unified backup orchestration service",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  snapshotter --config /etc/snapshotter-config.yaml
  snapshotter --config config.yaml --dry-run
  snapshotter --config config.yaml --log-level DEBUG
        """,
    )

    parser.add_argument(
        "--config",
        type=Path,
        default=Path("./snapshotter-config.yaml"),
        help="Path to YAML configuration file (default: ./snapshotter-config.yaml)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview mode - show what would be backed up without performing backups",
    )

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Logging level (default: INFO)",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"Snapshotter {__version__}",
    )

    args = parser.parse_args()

    # Convert log level string to logging constant
    log_level = getattr(logging, args.log_level.upper(), logging.INFO)

    # Initialize logger
    logger = SnapshatterLogger(
        name="snapshotter",
        log_file=Path("/srv/backups/logs/snapshotter.log"),
        level=log_level,
        use_syslog=False,
    )

    try:
        logger.info(f"Snapshotter {__version__} starting")
        logger.info(f"Configuration file: {args.config}")

        # Load configuration
        if not args.config.exists():
            logger.error(f"Configuration file not found: {args.config}")
            return 1

        config = Config(args.config)
        logger.info("Configuration loaded successfully")

        # Create and run orchestrator
        orchestrator = BackupOrchestrator(config, logger, dry_run=args.dry_run)
        success = orchestrator.run()

        if success:
            logger.info("Backup orchestration completed successfully")
            return 0
        else:
            logger.error("Backup orchestration failed")
            return 1

    except ConfigError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
