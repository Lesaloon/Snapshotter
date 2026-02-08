#!/bin/bash
# Setup cron job for Snapshotter

set -e

INSTALL_DIR="/srv/Snapshotter"
CONFIG_FILE="${1:=/srv/backups/snapshotter-config.yaml}"
CRON_USER="${2:-root}"
CRON_SCHEDULE="${3:-5 2 * * *}"  # 2:05 AM daily

if [ ! -d "${INSTALL_DIR}" ]; then
    echo "Error: Snapshotter not found at ${INSTALL_DIR}"
    exit 1
fi

if [ ! -f "${CONFIG_FILE}" ]; then
    echo "Error: Configuration file not found at ${CONFIG_FILE}"
    exit 1
fi

echo "Setting up cron job for Snapshotter..."
echo "User: ${CRON_USER}"
echo "Schedule: ${CRON_SCHEDULE} ($(man 5 crontab 2>/dev/null | grep -A 5 'CRON' || echo 'minute hour day month weekday'))"
echo "Config: ${CONFIG_FILE}"
echo ""

CRON_CMD="${INSTALL_DIR}/venv/bin/python -m snapshotter --config ${CONFIG_FILE}"

# Create temporary cron file
TEMP_CRON="/tmp/snapshotter.cron"
crontab -u "${CRON_USER}" -l > "${TEMP_CRON}" 2>/dev/null || echo "" > "${TEMP_CRON}"

# Check if job already exists
if grep -q "snapshotter" "${TEMP_CRON}"; then
    echo "Cron job already exists"
    grep "snapshotter" "${TEMP_CRON}"
    rm "${TEMP_CRON}"
    exit 0
fi

# Add new cron job
echo "${CRON_SCHEDULE} ${CRON_CMD} >> /srv/backups/logs/cron.log 2>&1" >> "${TEMP_CRON}"

# Install cron job
crontab -u "${CRON_USER}" "${TEMP_CRON}"
rm "${TEMP_CRON}"

echo "Cron job installed successfully!"
echo "You can verify with: crontab -l"
