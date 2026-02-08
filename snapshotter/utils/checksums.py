"""Checksum utilities for Snapshotter."""

import hashlib
from pathlib import Path
from typing import Tuple


def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file.

    Args:
        file_path: Path to file

    Returns:
        SHA256 hash as hex string
    """
    sha256_hash = hashlib.sha256()

    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)

    return sha256_hash.hexdigest()


def write_checksum(file_path: Path, checksum: str) -> None:
    """Write checksum to .sha256 file.

    Args:
        file_path: Path to backup file
        checksum: SHA256 checksum value
    """
    checksum_file = Path(str(file_path) + ".sha256")

    with open(checksum_file, "w") as f:
        f.write(f"{checksum}  {file_path.name}\n")


def verify_checksum(file_path: Path) -> Tuple[bool, str]:
    """Verify checksum of a file.

    Args:
        file_path: Path to backup file

    Returns:
        Tuple of (is_valid, message)
    """
    checksum_file = Path(str(file_path) + ".sha256")

    if not checksum_file.exists():
        return False, f"Checksum file not found: {checksum_file}"

    with open(checksum_file, "r") as f:
        stored_checksum = f.read().split()[0]

    calculated_checksum = calculate_sha256(file_path)

    if stored_checksum == calculated_checksum:
        return True, "Checksum verified"

    return False, f"Checksum mismatch: expected {stored_checksum}, got {calculated_checksum}"
