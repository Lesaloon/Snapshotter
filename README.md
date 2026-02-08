# Snapshotter

**Unified backup orchestration service for multi-target infrastructure**

Snapshotter is a production-ready Python application that orchestrates backups across multiple targets (PostgreSQL databases, Prometheus metrics, and filesystem configurations) with zero-downtime snapshots, automatic retention policies, and webhook notifications.

## Features

✨ **Multi-Target Orchestration**
- Backup PostgreSQL databases via `docker exec pg_dumpall`
- Snapshot Prometheus metrics via zero-downtime API method
- Back up application configuration files
- Coordinate all backups in a single operation

🎯 **Smart Automation**
- Automatic backup retention policies per target type
- Configurable cleanup of old backups
- Webhook notifications for backup events (n8n integration)
- Dry-run mode for safe preview execution

🔒 **Data Integrity**
- SHA256 checksum verification
- tar.gz compression with integrity validation
- Docker-safe backup execution
- Error handling and graceful degradation

📊 **Monitoring & Logging**
- Comprehensive logging with file rotation
- Optional syslog integration
- Backup execution summaries
- Webhook event notifications (backup_success, backup_failure, etc.)

⚙️ **Developer Friendly**
- Type-safe Python 3.10+ code with full type hints
- 48+ test cases with comprehensive coverage
- YAML-based configuration with environment variable support
- CLI interface with multiple options

## Quick Start

### Installation

```bash
# Clone the repository
git clone git@github.com:Lesaloon/Snapshotter.git
cd Snapshotter

# Run installation script
bash scripts/install.sh
```

### Configure

Edit `/srv/backups/snapshotter-config.yaml`:

```yaml
backup_dir: /srv/backups

backups:
  - type: database
    name: postgres-main
    container: postgres
    
  - type: prometheus
    name: prometheus-metrics
    url: http://localhost:9090
    data_dir: /srv/prometheus-data
    
  - type: filesystem
    name: app-config
    paths:
      - /etc/nginx
      - /srv/app/config

retention:
  database: 30
  prometheus: 14
  filesystem: 7

notifications:
  webhook:
    url: http://localhost:5678/webhook/snapshotter
```

### Test

```bash
source venv/bin/activate
python -m snapshotter --config /srv/backups/snapshotter-config.yaml --dry-run
```

### Run Backup

```bash
source venv/bin/activate
python -m snapshotter --config /srv/backups/snapshotter-config.yaml
```

### Schedule with Cron

```bash
bash scripts/setup-cron.sh
```

## Documentation

- **[Installation Guide](docs/INSTALLATION.md)** - Step-by-step setup instructions
- **[Configuration Reference](docs/CONFIGURATION.md)** - Complete config schema
- **[Usage Guide](docs/USAGE.md)** - How to run and monitor backups
- **[Restore Procedures](docs/RESTORE.md)** - How to restore from backups
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions
- **[Architecture](docs/ARCHITECTURE.md)** - System design and extensibility

## CLI Options

```bash
usage: snapshotter [-h] [--config CONFIG] [--dry-run]
                   [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                   [--version]

Snapshotter - Unified backup orchestration service

options:
  -h, --help                      show help message
  --config CONFIG                 Path to YAML configuration (default: ./snapshotter-config.yaml)
  --dry-run                       Preview mode - no backups performed
  --log-level {DEBUG,INFO,...}    Logging level (default: INFO)
  --version                       Show version
```

### Examples

```bash
# Preview backups
snapshotter --config config.yaml --dry-run

# Run with debug logging
snapshotter --config config.yaml --log-level DEBUG

# Use custom config path
snapshotter --config /etc/snapshotter/config.yaml

# Show version
snapshotter --version
```

## Backup Methods

### PostgreSQL Database
- Uses `docker exec <container> pg_dumpall -U postgres`
- Exports complete database dump to compressed SQL file
- Verifies archive integrity
- Calculates SHA256 checksum

### Prometheus Metrics
- Uses `/api/v1/admin/tsdb/snapshot` API endpoint
- Zero downtime - Prometheus continues serving during backup
- Polls filesystem for snapshot completion
- Compresses snapshot directory to tar.gz
- No service interruption required

### Filesystem Configuration
- Backs up application configuration files
- Supports multiple paths
- Warns on missing paths but continues
- Creates compressed tar.gz archive
- Validates backup integrity

## Features

| Feature | Status | Details |
|---------|--------|---------|
| Multi-target orchestration | ✅ | Database, Prometheus, filesystem |
| Zero-downtime backups | ✅ | Prometheus API snapshot method |
| Retention policies | ✅ | Configurable per backup type |
| Notifications | ✅ | Webhook integration (n8n) |
| Dry-run mode | ✅ | Safe preview before execution |
| Logging | ✅ | File, console, syslog |
| Type safety | ✅ | Full type hints (Python 3.10+) |
| Testing | ✅ | 48+ test cases |
| Error handling | ✅ | Graceful degradation |
| Cron integration | ✅ | Automated scheduling |

## Project Status

- **Version**: 1.0.0
- **Status**: Production Ready
- **Completion**: 100%
- **Test Coverage**: 48+ test cases
- **Python**: 3.10+

## Architecture

Snapshotter follows a modular, extensible architecture:

- **snapshotter/** - Main package
- **snapshotter/backups/** - Backup target implementations
- **snapshotter/notifiers/** - Notification system
- **snapshotter/utils/** - Utility functions
- **tests/** - Comprehensive test suite
- **scripts/** - Helper scripts for setup and testing

See [Architecture Documentation](docs/ARCHITECTURE.md) for design details.

## Development

### Install Development Dependencies

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Run Tests

```bash
pytest tests/ -v --cov=snapshotter
```

### Code Quality Checks

```bash
bash scripts/lint.sh
```

### Format Code

```bash
black snapshotter/ tests/
```

## Support

For issues, questions, or contributions:
- Check [Troubleshooting Guide](docs/TROUBLESHOOTING.md)
- Review [Configuration Reference](docs/CONFIGURATION.md)
- See [Architecture Documentation](docs/ARCHITECTURE.md)

## License

MIT License - See LICENSE file for details

## Author

Lesaloon - [GitHub Profile](https://github.com/Lesaloon)

---

**Ready to backup? Follow the [Quick Start Guide](#quick-start) above!**
