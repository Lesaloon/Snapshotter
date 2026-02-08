# Installation Guide

Complete step-by-step instructions for installing and configuring Snapshotter.

## Prerequisites

- Python 3.10 or higher
- pip and venv (usually included with Python)
- Docker (for PostgreSQL database backups)
- Git (for cloning the repository)
- Sudo access (for system-level configuration)

### System Requirements

- **OS**: Linux (tested on Debian/Ubuntu)
- **Disk Space**: 2GB minimum for logs and temporary files
- **RAM**: 256MB minimum (most operations run in under 100MB)
- **Python**: 3.10, 3.11, or 3.12

## Installation Steps

### 1. Clone Repository

```bash
cd /srv
sudo git clone git@github.com:Lesaloon/Snapshotter.git
cd Snapshotter
```

### 2. Run Installation Script

The installation script automates the setup process:

```bash
sudo bash scripts/install.sh
```

This will:
- Create backup directories (`/srv/backups`)
- Create Python virtual environment
- Install Python dependencies
- Create sample configuration file
- Set proper permissions

### 3. Manual Setup (Alternative)

If you prefer manual setup:

```bash
# Create directories
sudo mkdir -p /srv/backups/logs
sudo mkdir -p /srv/backups/database
sudo mkdir -p /srv/backups/prometheus
sudo mkdir -p /srv/backups/filesystem

# Create virtual environment
cd /srv/Snapshotter
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Copy configuration template
sudo cp config/snapshotter-config.yaml /srv/backups/snapshotter-config.yaml
```

### 4. Configure Snapshotter

Edit the configuration file:

```bash
sudo nano /srv/backups/snapshotter-config.yaml
```

Required configuration:
- `backup_dir` - Where to store backups
- `backups` - List of backup targets
- `retention` - Days to keep backups per type

See [Configuration Reference](CONFIGURATION.md) for detailed options.

### 5. Set Permissions

```bash
# Make scripts executable
sudo chmod +x /srv/Snapshotter/scripts/*.sh

# Set backup directory permissions
sudo chown -R root:root /srv/backups
sudo chmod 700 /srv/backups
```

### 6. Test Installation

Run a dry-run to verify everything works:

```bash
cd /srv/Snapshotter
source venv/bin/activate
python -m snapshotter --config /srv/backups/snapshotter-config.yaml --dry-run
```

Expected output:
```
INFO - Starting backup orchestration (dry_run=True)
INFO - DRY RUN MODE - No backups will be performed
INFO - Executing backup: [backup name] (type: [type])
INFO - [DRY RUN] Would backup [backup name]
INFO - BACKUP SUMMARY
```

### 7. Setup Cron Job (Optional)

Automate daily backups:

```bash
sudo /srv/Snapshotter/scripts/setup-cron.sh
```

This will:
- Create a daily cron job (default: 2:05 AM)
- Schedule backup execution
- Redirect output to log file

Verify installation:

```bash
sudo crontab -l
```

## Troubleshooting Installation

### Virtual Environment Issues

**Problem**: `python3: command not found`

**Solution**: Install Python 3
```bash
sudo apt-get update
sudo apt-get install python3 python3-pip python3-venv
```

### Permission Denied

**Problem**: `Permission denied: '/srv/backups'`

**Solution**: Set proper ownership
```bash
sudo chown -R $(whoami) /srv/Snapshotter
sudo mkdir -p /srv/backups && sudo chown -R $(whoami) /srv/backups
```

### Docker Connection Issues

**Problem**: Cannot connect to Docker daemon

**Solution**: 
```bash
# Add user to docker group
sudo usermod -aG docker $USER
# Log out and log back in, or:
newgrp docker
```

### Module Import Errors

**Problem**: `ModuleNotFoundError: No module named 'yaml'`

**Solution**: Reinstall dependencies
```bash
source /srv/Snapshotter/venv/bin/activate
pip install --force-reinstall -r /srv/Snapshotter/requirements.txt
```

### Permission Error on Logs

**Problem**: Cannot write to log file

**Solution**: Create log directory with correct permissions
```bash
sudo mkdir -p /srv/backups/logs
sudo chmod 755 /srv/backups/logs
```

## Verifying Installation

Run the verification script:

```bash
cd /srv/Snapshotter
source venv/bin/activate

# Test imports
python -c "from snapshotter import __version__; print(f'Snapshotter {__version__}')"

# Test configuration loading
python -c "from snapshotter.config import Config; c = Config('config/snapshotter-config.yaml'); print(f'{len(c.get_backups())} backups configured')"

# Run dry-run test
python -m snapshotter --config /srv/backups/snapshotter-config.yaml --dry-run
```

## Post-Installation

### Create Backup Directories

```bash
# Database backups
sudo mkdir -p /srv/backups/database

# Prometheus snapshots
sudo mkdir -p /srv/backups/prometheus

# Filesystem configs
sudo mkdir -p /srv/backups/filesystem

# Logs
sudo mkdir -p /srv/backups/logs
```

### Configure Docker Access

For PostgreSQL backups via Docker:

```bash
# Add root to docker group (if running as root)
sudo usermod -aG docker root

# Verify Docker access
docker ps
```

### Set Up Monitoring

Monitor backup logs:

```bash
# Watch logs in real-time
tail -f /srv/backups/logs/snapshotter.log

# Check last backup
ls -lh /srv/backups/database/ | tail -1
```

## Running Snapshotter

### Manual Execution

```bash
cd /srv/Snapshotter
source venv/bin/activate
python -m snapshotter --config /srv/backups/snapshotter-config.yaml
```

### Dry-Run Mode

Preview without executing:

```bash
python -m snapshotter --config /srv/backups/snapshotter-config.yaml --dry-run
```

### Debug Logging

Run with verbose output:

```bash
python -m snapshotter --config /srv/backups/snapshotter-config.yaml --log-level DEBUG
```

## Uninstallation

To remove Snapshotter:

```bash
# Remove application
sudo rm -rf /srv/Snapshotter

# Keep backups (optional, remove if needed)
sudo rm -rf /srv/backups

# Remove cron job
sudo crontab -e
# Remove the snapshotter line manually
```

## Next Steps

1. Review [Configuration Reference](CONFIGURATION.md) for detailed options
2. See [Usage Guide](USAGE.md) for running backups
3. Check [Troubleshooting](TROUBLESHOOTING.md) for common issues
4. Read [Restore Procedures](RESTORE.md) for data recovery

## Support

For installation issues:
- Check [Troubleshooting Guide](TROUBLESHOOTING.md)
- Review [Configuration Reference](CONFIGURATION.md)
- Check application logs: `/srv/backups/logs/snapshotter.log`

---

**Installation complete! Proceed to [Configuration Reference](CONFIGURATION.md) to set up your backups.**
