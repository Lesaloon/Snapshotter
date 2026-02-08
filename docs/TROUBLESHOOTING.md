# Troubleshooting Guide

Common issues and solutions for Snapshotter.

## Installation Issues

### ModuleNotFoundError: No module named 'yaml'

**Problem**: Dependencies not installed

**Solution**:
```bash
source /srv/Snapshotter/venv/bin/activate
pip install -r /srv/Snapshotter/requirements.txt
```

### Permission denied: '/srv/backups'

**Problem**: Insufficient permissions for backup directory

**Solution**:
```bash
sudo chmod 755 /srv/backups
sudo chown -R root:root /srv/backups
```

### Python 3.10+ not found

**Problem**: System has older Python version

**Solution**:
```bash
# Check Python version
python3 --version

# Install Python 3.10+
sudo apt-get update
sudo apt-get install python3.10 python3.10-venv
```

### Virtual environment creation fails

**Problem**: venv module not available

**Solution**:
```bash
# Install venv
sudo apt-get install python3-venv python3-dev

# Create venv manually
python3 -m venv /srv/Snapshotter/venv
```

## Configuration Issues

### ConfigError: Configuration file not found

**Problem**: Config file path is incorrect

**Solution**:
```bash
# Check if file exists
ls -l /srv/backups/snapshotter-config.yaml

# Use correct path
python -m snapshotter --config /srv/backups/snapshotter-config.yaml
```

### ConfigError: Invalid YAML configuration

**Problem**: YAML syntax error in config file

**Solution**:
```bash
# Validate YAML syntax
python3 -c "import yaml; yaml.safe_load(open('/srv/backups/snapshotter-config.yaml'))"

# Common YAML errors:
# - Incorrect indentation (use 2 spaces, not tabs)
# - Missing colons or quotes
# - Trailing spaces
```

### ConfigError: 'backups' list cannot be empty

**Problem**: No backup targets configured

**Solution**:
Edit `/srv/backups/snapshotter-config.yaml` and add at least one backup:

```yaml
backups:
  - type: database
    name: postgres-main
    container: postgres
```

### ConfigError: Invalid backup type

**Problem**: Using unsupported backup type

**Solution**:
Use only: `database`, `prometheus`, or `filesystem`

```yaml
# Wrong
- type: mysql  # Invalid

# Correct
- type: database  # Valid
```

## Docker Issues

### Docker: permission denied while trying to connect

**Problem**: User not in docker group

**Solution**:
```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Apply group changes
newgrp docker

# Verify
docker ps
```

### Docker daemon is not running

**Problem**: Docker service not started

**Solution**:
```bash
# Start Docker
sudo systemctl start docker

# Enable auto-start
sudo systemctl enable docker

# Check status
sudo systemctl status docker
```

### Container not found: 'postgres'

**Problem**: Container name doesn't exist or is stopped

**Solution**:
```bash
# List running containers
docker ps

# List all containers (including stopped)
docker ps -a

# Start container if stopped
docker start postgres

# Use correct container name in config
# Match the NAMES column from docker ps output
```

### Cannot connect to Docker daemon socket

**Problem**: Docker not accessible

**Solution**:
```bash
# Check Docker socket permissions
ls -l /var/run/docker.sock

# Restart Docker
sudo systemctl restart docker

# Verify connection
docker ps
```

## Database Backup Issues

### pg_dumpall: command not found

**Problem**: PostgreSQL tools not in Docker container

**Solution**:
```bash
# Verify PostgreSQL is running in container
docker exec postgres psql --version

# Check container has PostgreSQL client tools
docker exec postgres which pg_dumpall
```

### pg_dumpall: could not connect to database

**Problem**: PostgreSQL connection failed

**Solution**:
```bash
# Check PostgreSQL is running
docker exec postgres pg_isready

# Check credentials
docker exec postgres psql -U postgres -c "SELECT 1;"

# Check listening port
docker exec postgres netstat -tlnp | grep postgres
```

### Backup file is empty

**Problem**: Database dump produced no output

**Solution**:
```bash
# Test dump manually
docker exec postgres pg_dumpall -U postgres | head -20

# Check database size
docker exec postgres psql -U postgres -c "SELECT sum(pg_database_size(datname)) FROM pg_database;"

# Verify user has permissions
docker exec postgres psql -U postgres -c "SELECT * FROM information_schema.tables LIMIT 1;"
```

### Dump is too large

**Problem**: Backup file is unexpectedly large

**Solution**:
```bash
# Check database size
docker exec postgres psql -U postgres -c "SELECT datname, pg_size_pretty(pg_database_size(datname)) FROM pg_database ORDER BY pg_database_size DESC;"

# Check for bloat
docker exec postgres psql -U postgres -c "SELECT * FROM pg_stat_user_tables WHERE n_tup_upd > 0 OR n_tup_del > 0;"

# Consider VACUUM
docker exec postgres vacuumdb -U postgres -z
```

## Prometheus Backup Issues

### Prometheus API error: connection refused

**Problem**: Cannot connect to Prometheus

**Solution**:
```bash
# Check Prometheus is running
curl -s http://localhost:9090/-/healthy

# Check correct URL in config
# Should be: http://host:port (no trailing slash)

# Test API endpoint
curl -s http://localhost:9090/api/v1/admin/tsdb/snapshot
```

### Snapshot directory not found

**Problem**: Prometheus data directory path is incorrect

**Solution**:
```bash
# Check data directory exists
ls -l /srv/prometheus-data/

# Verify snapshots subdirectory
ls -l /srv/prometheus-data/snapshots/

# Use absolute path in config
data_dir: /srv/prometheus-data  # Not relative paths
```

### Snapshot creation timeout

**Problem**: API call taking too long

**Solution**:
```bash
# Check Prometheus is responsive
curl -I http://localhost:9090

# Check disk space for snapshot
df -h /srv/prometheus-data/

# Reduce metric retention in Prometheus config
# Then try backup again
```

### Snapshot API not available

**Problem**: Older Prometheus version or admin API disabled

**Solution**:
```bash
# Check Prometheus version
curl -s http://localhost:9090/api/v1/status/buildinfo

# Requires Prometheus 1.5+
# Enable admin API in Prometheus config:
# --web.enable-admin-api

# Restart Prometheus with flag
docker run -p 9090:9090 prom/prometheus --web.enable-admin-api
```

## Filesystem Backup Issues

### Path does not exist

**Problem**: Configured path doesn't exist

**Expected behavior**: Warning logged, backup continues with other paths

**Solution**:
```bash
# Create missing path
mkdir -p /etc/nginx

# Verify path exists
ls -l /etc/nginx

# Update config if path wrong
nano /srv/backups/snapshotter-config.yaml
```

### Permission denied reading path

**Problem**: Insufficient permissions to read files

**Solution**:
```bash
# Check file permissions
ls -l /etc/nginx/

# Run with appropriate privileges
sudo /srv/Snapshotter/venv/bin/python -m snapshotter --config /srv/backups/snapshotter-config.yaml

# Or fix permissions
sudo chmod -R 755 /etc/nginx/
```

### Backup file too large

**Problem**: Archive is huge

**Solution**:
```bash
# Check directory size
du -sh /etc/nginx/

# List large files
find /etc/nginx/ -size +10M -exec ls -lh {} \;

# Remove unnecessary files before backup
# Or adjust paths in config to exclude them
```

## File Permission Issues

### Cannot write to log file

**Problem**: Log directory not writable

**Solution**:
```bash
# Create log directory
sudo mkdir -p /srv/backups/logs

# Set permissions
sudo chmod 755 /srv/backups/logs
sudo chown root:root /srv/backups/logs

# Test write permission
touch /srv/backups/logs/test.log && rm /srv/backups/logs/test.log
```

### Cannot create backup directory

**Problem**: Backup directory not writable

**Solution**:
```bash
# Create backup directory
sudo mkdir -p /srv/backups/{database,prometheus,filesystem}

# Set permissions
sudo chmod 755 /srv/backups/
sudo chmod 755 /srv/backups/database
sudo chmod 755 /srv/backups/prometheus
sudo chmod 755 /srv/backups/filesystem
```

## Notification Issues

### Webhook connection refused

**Problem**: Cannot connect to webhook endpoint

**Solution**:
```bash
# Test webhook connectivity
curl -X POST http://localhost:5678/webhook -H "Content-Type: application/json" -d '{"test":"data"}'

# Check webhook service is running
curl http://localhost:5678/

# Update webhook URL in config
nano /srv/backups/snapshotter-config.yaml
```

### Webhook timeout

**Problem**: Webhook request too slow

**Solution**:
```bash
# Check webhook service responsiveness
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:5678/

# Increase timeout (code change required)
# Default: 30 seconds

# Check network connectivity
ping webhook.example.com
telnet webhook.example.com 5678
```

### Notification not sent

**Problem**: Webhook notification failed silently

**Solution**:
Enable debug logging:
```bash
python -m snapshotter --config config.yaml --log-level DEBUG
```

Look for messages:
```
DEBUG - Sending notifications
DEBUG - Notification failed: ...
```

## Retention & Cleanup Issues

### Old backups not deleted

**Problem**: Retention policy not working

**Solution**:
```bash
# Check retention configuration
grep -A 3 "retention:" /srv/backups/snapshotter-config.yaml

# Verify backup age
ls -lh /srv/backups/database/ | head -5

# Run backup to trigger cleanup
python -m snapshotter --config /srv/backups/snapshotter-config.yaml

# Check logs for cleanup messages
grep "Retention cleanup" /srv/backups/logs/snapshotter.log
```

### Incorrect files deleted

**Problem**: Retention deleting wrong backups

**Solution**:
```bash
# Backup important files first
cp -r /srv/backups/database /srv/backups/database.backup

# Increase retention period
nano /srv/backups/snapshotter-config.yaml
# Change: retention.database from 7 to 30

# Restore backups if needed
cp -r /srv/backups/database.backup/* /srv/backups/database/
```

## Performance Issues

### Backup runs too slowly

**Problem**: Backup taking longer than expected

**Solution**:

**For PostgreSQL**:
```bash
# Check database size
docker exec postgres psql -U postgres -c "SELECT pg_size_pretty(sum(pg_database_size(datname))) FROM pg_database;"

# Check system load
top

# Vacuum database before backup
docker exec postgres vacuumdb -U postgres -a -z
```

**For Prometheus**:
```bash
# Check metrics count
curl -s http://localhost:9090/api/v1/query?query=count(%7B__name__%7D) | jq '.data.result[0].value[1]'

# Check disk I/O
iostat -x 1 5
```

**For Filesystem**:
```bash
# Check disk speed
hdparm -Tt /dev/sda

# Check file count
find /path/to/backup -type f | wc -l
```

### High disk usage

**Problem**: Backups consuming too much space

**Solution**:
```bash
# Check backup size
du -sh /srv/backups/*

# List largest backups
ls -lhS /srv/backups/database/ | head -10

# Reduce retention
nano /srv/backups/snapshotter-config.yaml
# Lower retention days

# Manually delete old backups
find /srv/backups/database -name "*.tar.gz" -mtime +30 -delete
```

## Cron Job Issues

### Cron job not executing

**Problem**: Scheduled backup not running

**Solution**:
```bash
# Check cron is running
systemctl status cron

# Check cron logs
grep snapshotter /var/log/syslog

# Check crontab syntax
crontab -l

# Test cron command manually
/srv/Snapshotter/venv/bin/python -m snapshotter --config /srv/backups/snapshotter-config.yaml
```

### Cron job fails silently

**Problem**: Cron runs but produces no output

**Solution**:
```bash
# Add logging to cron job
# Edit crontab:
sudo crontab -e

# Change line to:
5 2 * * * /srv/Snapshotter/venv/bin/python -m snapshotter --config /srv/backups/snapshotter-config.yaml 2>&1 | tee -a /srv/backups/logs/cron.log

# Check cron output
tail -f /srv/backups/logs/cron.log
```

## General Debugging

### Enable Debug Logging

```bash
python -m snapshotter --config config.yaml --log-level DEBUG 2>&1 | tee debug.log
```

### Check Snapshotter Version

```bash
python -m snapshotter --version
```

### Verify System Requirements

```bash
# Check Python version
python3 --version  # Should be 3.10+

# Check required commands
which docker
which tar
which python3

# Check disk space
df -h /srv/
```

### Review Full Logs

```bash
# View entire log file
cat /srv/backups/logs/snapshotter.log

# Search for errors
grep ERROR /srv/backups/logs/snapshotter.log

# Follow logs in real-time
tail -f /srv/backups/logs/snapshotter.log
```

## When All Else Fails

1. **Check logs** - Always the first step
   ```bash
   tail -100 /srv/backups/logs/snapshotter.log
   ```

2. **Run with debug logging**
   ```bash
   python -m snapshotter --config config.yaml --log-level DEBUG
   ```

3. **Test individual components**
   ```bash
   docker ps          # Check Docker
   curl http://prometheus:9090/-/healthy  # Check Prometheus
   psql -U postgres   # Check PostgreSQL
   ```

4. **Check configuration**
   ```bash
   python3 -c "import yaml; print(yaml.safe_load(open('/srv/backups/snapshotter-config.yaml')))"
   ```

5. **Review documentation**
   - [Installation Guide](INSTALLATION.md)
   - [Configuration Reference](CONFIGURATION.md)
   - [Usage Guide](USAGE.md)

---

**Still having issues? Review [Usage Guide](USAGE.md) or contact system administrator.**
