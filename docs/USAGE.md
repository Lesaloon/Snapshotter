# Usage Guide

How to run, monitor, and manage Snapshotter backups.

## Running Backups

### Basic Usage

```bash
cd /srv/Snapshotter
source venv/bin/activate
python -m snapshotter --config /srv/backups/snapshotter-config.yaml
```

### Available Options

```
--config FILE                    Path to configuration file (required)
--dry-run                        Preview mode - don't execute backups
--log-level {DEBUG,INFO,...}    Logging verbosity (default: INFO)
--version                        Show version number
--help                           Show help message
```

### Examples

#### Test Before Running

```bash
# Preview backups without executing
python -m snapshotter --config config.yaml --dry-run
```

Output:
```
INFO - Starting backup orchestration (dry_run=True)
INFO - DRY RUN MODE - No backups will be performed
INFO - Executing backup: postgres-main (type: database)
INFO - [DRY RUN] Would backup postgres-main
INFO - BACKUP SUMMARY
INFO - Total backups: 1
INFO - Successful: 1
INFO - Failed: 0
```

#### Run with Debug Logging

```bash
# Verbose output for troubleshooting
python -m snapshotter --config config.yaml --log-level DEBUG
```

#### Use Custom Config

```bash
python -m snapshotter --config /custom/path/config.yaml
```

#### Check Version

```bash
python -m snapshotter --version
```

Output: `Snapshotter 1.0.0`

## Monitoring Backups

### View Logs

Real-time log monitoring:

```bash
# Watch logs as they're written
tail -f /srv/backups/logs/snapshotter.log

# Last 100 lines
tail -100 /srv/backups/logs/snapshotter.log

# Search for errors
grep ERROR /srv/backups/logs/snapshotter.log
```

### Check Backup Files

```bash
# List all backups
ls -lh /srv/backups/

# Database backups
ls -lh /srv/backups/database/

# Prometheus backups
ls -lh /srv/backups/prometheus/

# Filesystem backups
ls -lh /srv/backups/filesystem/

# Show latest backup with size
ls -lh /srv/backups/database/ | tail -1
```

### Verify Backup Integrity

```bash
# Check checksums
cat /srv/backups/database/backup-20240101-120000.tar.gz.sha256

# Verify specific backup
sha256sum -c /srv/backups/database/backup-20240101-120000.tar.gz.sha256
```

Expected output:
```
/srv/backups/database/backup-20240101-120000.tar.gz: OK
```

### View Backup Summary

Latest lines of log file show summary:

```bash
tail -15 /srv/backups/logs/snapshotter.log
```

Output:
```
============================================================
BACKUP SUMMARY
============================================================
Total backups: 3
Successful: 3
Failed: 0
Total size: 245.67 MB
Total duration: 123.45 seconds
============================================================
```

## Automatic Scheduling

### Setup Cron Job

```bash
bash /srv/Snapshotter/scripts/setup-cron.sh
```

This configures a daily backup at 2:05 AM.

### Custom Schedule

Edit crontab manually:

```bash
sudo crontab -e
```

Add line for different schedule:

```bash
# Daily at 2:05 AM
5 2 * * * /srv/Snapshotter/venv/bin/python -m snapshotter --config /srv/backups/snapshotter-config.yaml >> /srv/backups/logs/cron.log 2>&1

# Every 6 hours
0 */6 * * * /srv/Snapshotter/venv/bin/python -m snapshotter --config /srv/backups/snapshotter-config.yaml >> /srv/backups/logs/cron.log 2>&1

# Weekly on Sunday at 3 AM
0 3 * * 0 /srv/Snapshotter/venv/bin/python -m snapshotter --config /srv/backups/snapshotter-config.yaml >> /srv/backups/logs/cron.log 2>&1
```

### Verify Cron Job

```bash
# List scheduled jobs
sudo crontab -l

# Check cron execution log
tail -f /srv/backups/logs/cron.log
```

## Backup Output

### Log File Location

Default: `/srv/backups/logs/snapshotter.log`

Log format:
```
TIMESTAMP - snapshotter - LEVEL - MESSAGE
2024-01-01 12:00:00,123 - snapshotter - INFO - Starting backup orchestration (dry_run=False)
```

### Log Levels

| Level | Purpose | Example |
|-------|---------|---------|
| DEBUG | Detailed troubleshooting | "Opening connection to docker.sock" |
| INFO | Normal operation | "Backup successful: postgres-main" |
| WARNING | Important issues | "Could not connect to webhook" |
| ERROR | Failed operations | "Backup failed: database error" |
| CRITICAL | System failure | "Configuration error" |

### Backup File Locations

```
/srv/backups/
├── database/
│   ├── database-backup-20240101-120000.tar.gz
│   └── database-backup-20240101-120000.tar.gz.sha256
├── prometheus/
│   ├── prometheus-backup-20240101-120000.tar.gz
│   └── prometheus-backup-20240101-120000.tar.gz.sha256
├── filesystem/
│   ├── filesystem-backup-20240101-120000.tar.gz
│   └── filesystem-backup-20240101-120000.tar.gz.sha256
└── logs/
    ├── snapshotter.log
    ├── snapshotter.log.1
    └── cron.log
```

### Retention & Cleanup

Snapshotter automatically:
1. Deletes backups older than retention period
2. Removes associated `.sha256` files
3. Logs cleanup summary

Example log:
```
INFO - Retention cleanup (database): deleted 2 files, freed 234.56 MB
```

## Webhook Notifications

### Testing Webhooks

Enable debug logging to see webhook requests:

```bash
python -m snapshotter --config config.yaml --log-level DEBUG
```

Look for:
```
INFO - Sending notifications
INFO - Notification sent successfully
```

### Webhook Payload

Example payload sent to webhook:

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

### Event Types

- **backup_success** - All backups succeeded
- **backup_partial_failure** - Some backups failed
- **backup_critical_failure** - All backups failed

## Handling Backup Results

### Successful Backup

Log output:
```
INFO - Backup successful: postgres-main (124.50 MB)
INFO - Total backups: 3
INFO - Successful: 3
INFO - Failed: 0
```

Webhook event: `backup_success`

### Failed Backup

Log output:
```
ERROR - Backup failed: postgres-main - Docker error: connection refused
INFO - Total backups: 3
INFO - Successful: 2
INFO - Failed: 1
```

Webhook event: `backup_partial_failure` or `backup_critical_failure`

### Partial Failure

If some backups fail but others succeed:

```
ERROR - Backup failed: prometheus-metrics - API error
INFO - Backup successful: postgres-main (124.50 MB)
INFO - Total backups: 3
INFO - Successful: 2
INFO - Failed: 1
```

Webhook event: `backup_partial_failure`

## Performance & Optimization

### Monitoring Backup Time

Check duration in log:

```bash
grep "BACKUP SUMMARY" -A 5 /srv/backups/logs/snapshotter.log
```

Output:
```
Total duration: 123.45 seconds
```

### Database Backup Performance

- PostgreSQL dump speed: ~10-50 MB/s depending on data
- Compression: ~2-5x compression ratio

### Prometheus Backup Performance

- API snapshot creation: ~1-5 seconds
- Compression: ~3-8x compression ratio
- Zero downtime (API method)

### Filesystem Backup Performance

- Speed: ~50-200 MB/s depending on disk
- Depends on number of files and total size

### Disk Usage Monitoring

```bash
# Check total backup size
du -sh /srv/backups/

# Check size per type
du -sh /srv/backups/database/
du -sh /srv/backups/prometheus/
du -sh /srv/backups/filesystem/

# Show oldest backups (marked for deletion)
find /srv/backups -type f -name "*.tar.gz" -mtime +30 -exec ls -lh {} \;
```

## Common Tasks

### Restart Failed Backup

If backup fails, check error log and try again:

```bash
python -m snapshotter --config config.yaml --log-level DEBUG
```

### Change Backup Schedule

Edit crontab:

```bash
sudo crontab -e
```

Modify the snapshotter line or use `--at` option.

### Disable Specific Backup

Edit configuration file and remove or comment out backup:

```yaml
backups:
  # - type: database       # Disabled
  #   name: postgres-main
  #   container: postgres
  
  - type: prometheus     # Still active
    name: prometheus-metrics
    url: http://localhost:9090
    data_dir: /srv/prometheus-data
```

### Increase Retention Period

Edit configuration:

```yaml
retention:
  database: 60          # Changed from 30 to 60 days
  prometheus: 28        # Changed from 14 to 28 days
```

### Disable Notifications

Remove or comment out webhook configuration:

```yaml
# notifications:
#   webhook:
#     url: http://localhost:5678/webhook
```

## Troubleshooting

See [Troubleshooting Guide](TROUBLESHOOTING.md) for:
- Common error messages
- Diagnosis steps
- Solutions for each issue

## Next Steps

- [Installation Guide](INSTALLATION.md) - Setup instructions
- [Configuration Reference](CONFIGURATION.md) - Config options
- [Restore Procedures](RESTORE.md) - How to restore from backups
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues

---

**All backups running? Check out [Restore Procedures](RESTORE.md) to prepare for recovery!**
