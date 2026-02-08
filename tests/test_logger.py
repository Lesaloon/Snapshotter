"""Test logger module."""

from pathlib import Path

from snapshotter.logger import SnapshatterLogger


def test_logger_creates_log_file(temp_dir):
    """Test that logger creates log file."""
    log_file = temp_dir / "test.log"
    logger = SnapshatterLogger(
        name="test",
        log_file=log_file,
        level=10,  # DEBUG
        use_syslog=False,
    )

    logger.info("Test message")

    assert log_file.exists()
    assert "Test message" in log_file.read_text()


def test_logger_logs_at_different_levels(temp_dir):
    """Test that logger respects log levels."""
    log_file = temp_dir / "test.log"
    logger = SnapshatterLogger(
        name="test",
        log_file=log_file,
        level=20,  # INFO
        use_syslog=False,
    )

    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")

    content = log_file.read_text()
    assert "Debug message" not in content  # DEBUG below INFO level
    assert "Info message" in content
    assert "Warning message" in content
    assert "Error message" in content


def test_logger_without_file(mock_logger):
    """Test that logger can work without file output."""
    # Logger should not raise errors when file is None
    mock_logger.info("Test message without file")
    # No assertion needed - just checking it doesn't raise


def test_logger_name_is_set(mock_logger):
    """Test that logger name is properly set."""
    assert mock_logger.logger.name == "test_logger"
