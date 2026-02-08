#!/bin/bash
# Install and setup Snapshotter

set -e

INSTALL_DIR="/srv/Snapshotter"
BACKUP_DIR="/srv/backups"
CONFIG_DIR="${BACKUP_DIR}"
LOG_DIR="${BACKUP_DIR}/logs"

echo "Installing Snapshotter..."
echo "Target directory: ${INSTALL_DIR}"
echo "Config directory: ${CONFIG_DIR}"
echo "Log directory: ${LOG_DIR}"

# Create directories
mkdir -p "${INSTALL_DIR}"
mkdir -p "${BACKUP_DIR}"
mkdir -p "${LOG_DIR}"

# Create Python virtual environment
if [ ! -d "${INSTALL_DIR}/venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv "${INSTALL_DIR}/venv"
else
    echo "Virtual environment already exists"
fi

# Activate virtual environment
source "${INSTALL_DIR}/venv/bin/activate"

# Install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r "${INSTALL_DIR}/requirements.txt"

# Create config from template if not exists
if [ ! -f "${CONFIG_DIR}/snapshotter-config.yaml" ]; then
    echo "Creating configuration file..."
    cp "${INSTALL_DIR}/config/snapshotter-config.yaml" "${CONFIG_DIR}/"
    echo "Configuration created at: ${CONFIG_DIR}/snapshotter-config.yaml"
    echo "Please edit this file with your backup targets!"
else
    echo "Configuration file already exists at: ${CONFIG_DIR}/snapshotter-config.yaml"
fi

# Set permissions
chmod 755 "${INSTALL_DIR}/scripts"/*.sh || true
chmod 700 "${BACKUP_DIR}"
chmod 755 "${LOG_DIR}"

echo ""
echo "Installation complete!"
echo ""
echo "Next steps:"
echo "1. Edit configuration: ${CONFIG_DIR}/snapshotter-config.yaml"
echo "2. Test with dry-run: ${INSTALL_DIR}/scripts/test.sh"
echo "3. Run backup: source ${INSTALL_DIR}/venv/bin/activate && python -m snapshotter --config ${CONFIG_DIR}/snapshotter-config.yaml"
echo "4. Setup cron: ${INSTALL_DIR}/scripts/setup-cron.sh"
