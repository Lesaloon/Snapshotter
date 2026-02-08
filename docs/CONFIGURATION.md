# Configuration Reference

Complete reference for Snapshotter configuration file.

## Overview

Snapshotter uses YAML configuration files to define backup targets, retention policies, notifications, and logging settings. Configuration files support environment variable substitution using `${VARIABLE_NAME}` syntax.

## File Location

Default location: `/srv/backups/snapshotter-config.yaml`

Custom location: Specify with `--config` flag
```bash
python -m snapshotter --config /custom/path/config.yaml
```

## Configuration Structure

```yaml
backup_dir: /srv/backups              # Base directory for backups
logging: {...}                         # Logging configuration
backups: [...]                         # List of backup targets
retention: {...}                       # Retention policies
notifications: {...}                  # Notification settings
```

## Top-Level Options

### backup_dir

Where to store all backups.

```yaml
backup_dir: /srv/backups
```

- **Type**: String (file path)
- **Required**: Yes
- **Default**: None
- **Note**: Directory will be created if it doesn't exist

## Logging Configuration

```yaml
logging:
  level: INFO                          # DEBUG, INFO, WARNING, ERROR, CRITICAL
  file: /srv/backups/logs/snapshotter.log
  use_syslog: false                    # Enable syslog output
```

### logging.level

Set logging verbosity.

| Level | Use Case |
|-------|----------|
| DEBUG | Detailed troubleshooting |
| INFO | Normal operation (default) |
| WARNING | Important issues |
| ERROR | Critical problems |
| CRITICAL | System failure |

### logging.file

Path to log file. Supports:
- Absolute paths: `/var/log/snapshotter.log`
- Relative paths: `./logs/snapshotter.log`
- Environment variables: `${LOG_DIR}/snapshotter.log`

**Log Rotation**: Automatic after 10MB, keeps 5 backups

### logging.use_syslog

Enable syslog output (in addition to file and console).

```yaml
logging:
  use_syslog: true    # Send logs to /dev/log
```

## Backups Configuration

Define backup targets to execute.

```yaml
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
```

### Database Backups

PostgreSQL backup via Docker.

```yaml
- type: database
  name: postgres-main           # Unique backup name
  container: postgres           # Docker container name
```

**Options**:
- `type`: `database` (required)
- `name`: Unique identifier (required)
- `container`: Docker container name (required)

**Example**:
```yaml
- type: database
  name: production-db
  container: postgres_prod

- type: database
  name: staging-db
  container: postgres_staging
```

### Prometheus Backups

Prometheus snapshot via API (zero-downtime).

```yaml
- type: prometheus
  name: prometheus-metrics
  url: http://localhost:9090
  data_dir: /srv/prometheus-data
```

**Options**:
- `type`: `prometheus` (required)
- `name`: Unique identifier (required)
- `url`: Prometheus URL (required)
  - Format: `http://host:port` (no trailing slash)
  - Examples: `http://localhost:9090`, `http://prometheus.example.com:9090`
- `data_dir`: Prometheus data directory on host (required)
  - Must exist on the host system
  - Snapshots stored in `data_dir/snapshots/`

**Example**:
```yaml
- type: prometheus
  name: metrics-primary
  url: http://prometheus.internal:9090
  data_dir: /data/prometheus

- type: prometheus
  name: metrics-secondary
  url: http://prometheus-backup.internal:9090
  data_dir: /data/prometheus-backup
```

### Filesystem Backups

Back up configuration and application files.

```yaml
- type: filesystem
  name: app-config
  paths:
    - /etc/nginx
    - /etc/docker
    - /srv/app/config
```

**Options**:
- `type`: `filesystem` (required)
- `name`: Unique identifier (required)
- `paths`: List of paths to back up (required)
  - Can be files or directories
  - Warns if path doesn't exist but continues
  - Supports absolute paths only

**Example**:
```yaml
- type: filesystem
  name: nginx-config
  paths:
    - /etc/nginx

- type: filesystem
  name: app-data
  paths:
    - /srv/app/config
    - /srv/app/templates
    - /etc/systemd/system/app.service
```

## Retention Configuration

Define how long to keep backups.

```yaml
retention:
  database: 30      # Keep database backups 30 days
  prometheus: 14    # Keep Prometheus backups 14 days
  filesystem: 7     # Keep config backups 7 days
```

**Options**:
- `database`: Days to keep database backups
- `prometheus`: Days to keep Prometheus backups
- `filesystem`: Days to keep filesystem backups

**Behavior**:
- Backups older than specified days are automatically deleted
- Deletion happens after successful backup execution
- Associated `.sha256` checksum files are also deleted
- Runs only in normal mode (not in dry-run)

**Examples**:
```yaml
# Short retention (test environment)
retention:
  database: 7
  prometheus: 3
  filesystem: 1

# Long retention (production)
retention:
  database: 90
  prometheus: 30
  filesystem: 14
```

## Notifications Configuration

Send backup notifications via webhooks.

```yaml
notifications:
  webhook:
    url: http://localhost:5678/webhook/snapshotter
```

### Webhook Configuration

```yaml
notifications:
  webhook:
    url: ${WEBHOOK_URL}    # Environment variable support
```

**Options**:
- `url`: Webhook URL to send events to (required)
  - Must be absolute URL with protocol
  - Examples:
    - `http://localhost:5678/webhook`
    - `https://n8n.example.com/webhook/snapshotter`
    - `https://zapier.example.com/hook/...`

**Webhook Events**:

Snapshotter sends events with structure:
```json
{
  "event": "backup_success",
  "data": {
    "timestamp": "2024-01-01T12:00:00",
    "dry_run": false,
    "backups": [
      {
        "name": "postgres-main",
        "type": "database",
        "success": true,
        "duration_seconds": 45,
        "size_mb": 124.5,
        "error": null
      }
    ]
  }
}
```

**Event Types**:
- `backup_success` - All backups succeeded
- `backup_partial_failure` - Some backups failed
- `backup_critical_failure` - All backups failed

**Example** (n8n integration):
```yaml
notifications:
  webhook:
    url: http://n8n:5678/webhook/snapshotter-notifications
```

## Environment Variable Substitution

Use environment variables in configuration:

```yaml
backup_dir: ${BACKUP_DIR}
logging:
  file: ${LOG_DIR}/snapshotter.log
notifications:
  webhook:
    url: ${WEBHOOK_URL}
```

Set environment variables before running:

```bash
export BACKUP_DIR=/mnt/backups
export LOG_DIR=/var/log/snapshotter
export WEBHOOK_URL=http://n8n:5678/webhook
python -m snapshotter --config config.yaml
```

## Complete Configuration Example

```yaml
# Production configuration
backup_dir: /mnt/backups

logging:
  level: INFO
  file: /var/log/snapshotter/snapshotter.log
  use_syslog: true

backups:
  # PostgreSQL database
  - type: database
    name: postgres-prod
    container: postgres_production
  
  # Prometheus metrics
  - type: prometheus
    name: prometheus-primary
    url: http://prometheus.internal:9090
    data_dir: /data/prometheus
  
  # Application configs
  - type: filesystem
    name: app-configs
    paths:
      - /etc/nginx
      - /etc/docker
      - /srv/app/config
      - /root/.ssh

retention:
  database: 30
  prometheus: 14
  filesystem: 7

notifications:
  webhook:
    url: http://n8n.internal:5678/webhook/snapshotter
```

## Configuration Validation

Snapshotter validates configuration on startup:

**Required fields**:
- `backup_dir` must exist or be creatable
- `backups` list must not be empty
- Each backup must have `type` field
- Valid types: `database`, `prometheus`, `filesystem`

**Errors**:
```
ConfigError: Configuration file not found: /etc/snapshotter.yaml
ConfigError: Invalid YAML configuration: ...
ConfigError: Configuration must contain 'backups' section
ConfigError: Backup 0 must have 'type' field
ConfigError: Backup 0 has invalid type: invalid_type
```

## Testing Configuration

Test configuration with dry-run:

```bash
python -m snapshotter --config config.yaml --dry-run --log-level DEBUG
```

Expected output:
```
INFO - Starting backup orchestration (dry_run=True)
INFO - DRY RUN MODE - No backups will be performed
INFO - Executing backup: postgres-prod (type: database)
INFO - [DRY RUN] Would backup postgres-prod
```

## Common Configuration Mistakes

### Missing Required Fields

**Problem**: 
```yaml
backups:
  - type: database
    # Missing: name and container
```

**Solution**: Add required fields
```yaml
backups:
  - type: database
    name: my-db
    container: postgres
```

### Wrong Container Name

**Problem**: 
```yaml
- type: database
  container: my_postgres  # Container doesn't exist
```

**Solution**: Get correct container name
```bash
docker ps | grep postgres
```

### Path Doesn't Exist

**Problem**:
```yaml
- type: filesystem
  paths:
    - /nonexistent/path
```

**Solution**: Create path or use existing one
```bash
mkdir -p /srv/app/config
```

### Invalid Retention Value

**Problem**:
```yaml
retention:
  database: -30  # Negative days not allowed
```

**Solution**: Use positive integer
```yaml
retention:
  database: 30
```

---

**Next**: See [Usage Guide](USAGE.md) to run backups with this configuration.
