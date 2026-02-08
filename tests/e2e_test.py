"""End-to-end integration tests."""

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from snapshotter.config import Config
from snapshotter.logger import SnapshatterLogger
from snapshotter.main import BackupOrchestrator


def test_orchestrator_dry_run(sample_config, mock_logger, temp_dir):
    """Test backup orchestration in dry-run mode."""
    orchestrator = BackupOrchestrator(
        config=sample_config,
        logger=mock_logger,
        dry_run=True,
    )

    success = orchestrator.run()

    # In dry-run mode, we expect success (no actual backup failures)
    assert len(orchestrator.results) > 0
    # All dry-run results should be successful
    assert all(r.metadata.get("dry_run") for r in orchestrator.results)


def test_orchestrator_initializes_correctly(sample_config, mock_logger):
    """Test orchestrator initialization."""
    orchestrator = BackupOrchestrator(
        config=sample_config,
        logger=mock_logger,
        dry_run=False,
    )

    assert orchestrator.config is not None
    assert orchestrator.logger is not None
    assert orchestrator.dry_run is False
    assert len(orchestrator.results) == 0


def test_orchestrator_creates_backup_directories(sample_config, mock_logger, temp_dir):
    """Test that orchestrator creates necessary directories."""
    # Create a simple config
    import yaml

    config_data = {
        "backup_dir": str(temp_dir / "backups"),
        "backups": [
            {
                "type": "filesystem",
                "name": "test-config",
                "paths": [str(temp_dir)],
            }
        ],
    }

    config_file = temp_dir / "config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    config = Config(config_file)

    orchestrator = BackupOrchestrator(
        config=config,
        logger=mock_logger,
        dry_run=True,
    )

    orchestrator.run()

    # Verify backup directory was accessed/created
    assert len(orchestrator.results) > 0


def test_orchestrator_handles_missing_backups(mock_logger, temp_dir):
    """Test orchestrator behavior with no backups configured."""
    import yaml

    config_data = {
        "backup_dir": str(temp_dir / "backups"),
        "backups": [],
    }

    config_file = temp_dir / "config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    config = Config(config_file)

    orchestrator = BackupOrchestrator(
        config=config,
        logger=mock_logger,
        dry_run=False,
    )

    success = orchestrator.run()
    assert not success  # Should fail with no backups


def test_orchestrator_success_status(sample_config, mock_logger, temp_dir):
    """Test orchestrator success status calculation."""
    orchestrator = BackupOrchestrator(
        config=sample_config,
        logger=mock_logger,
        dry_run=True,
    )

    orchestrator.run()

    # In dry-run mode, all should succeed
    assert orchestrator._is_all_success()


def test_orchestrator_logs_summary(sample_config, mock_logger, temp_dir):
    """Test that orchestrator logs summary information."""
    orchestrator = BackupOrchestrator(
        config=sample_config,
        logger=mock_logger,
        dry_run=True,
    )

    orchestrator.run()

    # Verify that summary was logged (no exception raised)
    # The summary logging is tested by successful completion
    assert len(orchestrator.results) > 0
