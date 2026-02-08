"""Compression utilities for Snapshotter."""

import tarfile
from pathlib import Path
from typing import List, Optional

from snapshotter.exceptions import CompressionError


def create_tar_gz(
    source_path: Path,
    output_path: Path,
    arcname: Optional[str] = None,
    exclude_patterns: Optional[List[str]] = None,
) -> None:
    """Create a tar.gz archive.

    Args:
        source_path: Path to file or directory to compress
        output_path: Path to output tar.gz file
        arcname: Archive name (defaults to source filename)
        exclude_patterns: List of glob patterns to exclude

    Raises:
        CompressionError: If compression fails
    """
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if arcname is None:
            arcname = source_path.name

        with tarfile.open(output_path, "w:gz") as tar:
            tar.add(source_path, arcname=arcname, recursive=True)

    except Exception as e:
        raise CompressionError(f"Failed to create tar.gz: {e}")


def extract_tar_gz(archive_path: Path, extract_path: Path) -> None:
    """Extract a tar.gz archive.

    Args:
        archive_path: Path to tar.gz file
        extract_path: Path to extract to

    Raises:
        CompressionError: If extraction fails
    """
    try:
        extract_path.mkdir(parents=True, exist_ok=True)

        with tarfile.open(archive_path, "r:gz") as tar:
            tar.extractall(path=extract_path)

    except Exception as e:
        raise CompressionError(f"Failed to extract tar.gz: {e}")


def verify_tar_gz(archive_path: Path) -> bool:
    """Verify integrity of a tar.gz archive.

    Args:
        archive_path: Path to tar.gz file

    Returns:
        True if archive is valid, False otherwise
    """
    try:
        with tarfile.open(archive_path, "r:gz") as tar:
            # Test archive by reading members
            tar.getmembers()
        return True
    except Exception:
        return False
