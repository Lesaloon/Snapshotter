#!/bin/bash
# Test Snapshotter with dry-run

set -e

INSTALL_DIR="/srv/Snapshotter"
CONFIG_FILE="${1:=/srv/backups/snapshotter-config.yaml}"

if [ ! -d "${INSTALL_DIR}" ]; then
    echo "Error: Snapshotter not found at ${INSTALL_DIR}"
    exit 1
fi

if [ ! -f "${CONFIG_FILE}" ]; then
    echo "Error: Configuration file not found at ${CONFIG_FILE}"
    exit 1
fi

echo "Testing Snapshotter with dry-run..."
echo "Configuration: ${CONFIG_FILE}"
echo ""

source "${INSTALL_DIR}/venv/bin/activate"
python -m snapshotter --config "${CONFIG_FILE}" --dry-run --log-level INFO

echo ""
echo "Dry-run test complete!"
