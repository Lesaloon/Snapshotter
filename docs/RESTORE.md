# Restore Procedures

How to restore data from Snapshotter backups.

## Overview

Snapshotter creates compressed tar.gz backups with SHA256 checksums. Restoration procedures vary by backup type.

## Before You Restore

### Verify Backup Integrity

Check checksum before restoring:

```bash
# Navigate to backup location
cd /srv/backups/database/

# Verify backup integrity
sha256sum -c backup-20240101-120000.tar.gz.sha256
```

Expected output:
```
backup-20240101-120000.tar.gz: OK
```

### Locate Correct Backup

Find backups by type and date:

```bash
# List database backups (newest first)
ls -lht /srv/backups/database/ | head -10

# List Prometheus backups
ls -lht /srv/backups/prometheus/ | head -10

# List filesystem backups
ls -lht /srv/backups/filesystem/ | head -10
```

### Check Available Disk Space

Ensure you have space for extraction:

```bash
# Check destination free space
df -h /srv/

# Size of backup file
du -h /srv/backups/database/backup-20240101-120000.tar.gz
```

## Restoring PostgreSQL Database

### Extract Database Dump

```bash
cd /srv/backups/database/

# Extract SQL file
tar -xzf backup-20240101-120000.tar.gz -C /tmp/

# Verify extraction
ls -lh /tmp/database.sql
```

### Restore to PostgreSQL

**Option 1: Using psql (recommended)**

```bash
# Restore into running PostgreSQL container
docker exec postgres psql -U postgres < /tmp/database.sql
```

**Option 2: Using docker cp and exec**

```bash
# Copy dump to container
docker cp /tmp/database.sql postgres:/tmp/

# Execute restore in container
docker exec postgres psql -U postgres -f /tmp/database.sql
```

**Option 3: Restore to Local PostgreSQL**

```bash
# If PostgreSQL is running locally
psql -U postgres < /tmp/database.sql
```

### Verify Database Restore

```bash
# Check tables were restored
docker exec postgres psql -U postgres -c "SELECT * FROM information_schema.tables WHERE table_schema != 'pg_catalog' AND table_schema != 'information_schema';"

# Test specific database
docker exec postgres psql -U postgres -d your_db -c "SELECT COUNT(*) FROM table_name;"
```

### Handle Restore Errors

**Error: "database already exists"**

Drop existing database first:

```bash
docker exec postgres dropdb -U postgres --if-exists your_db
# Then restore again
```

**Error: "permission denied"**

Ensure user has permissions:

```bash
docker exec postgres psql -U postgres -c "GRANT ALL ON DATABASE your_db TO your_user;"
```

**Error: "restore incomplete"**

Check SQL file integrity:

```bash
# Check if file is readable
tar -tzf backup-20240101-120000.tar.gz

# View first lines of SQL
tar -xzOf backup-20240101-120000.tar.gz database.sql | head -20
```

## Restoring Prometheus Data

### Extract Snapshot

```bash
# Extract to temporary location
cd /srv/backups/prometheus/
mkdir -p /tmp/prometheus-restore
tar -xzf prometheus-backup-20240101-120000.tar.gz -C /tmp/prometheus-restore/

# List extracted contents
ls -lh /tmp/prometheus-restore/
```

### Restore Data

**Option 1: Replace Prometheus Data Directory**

```bash
# Stop Prometheus
docker stop prometheus

# Backup current data
cp -r /srv/prometheus-data /srv/prometheus-data.backup

# Restore snapshot
cp -r /tmp/prometheus-restore/prometheus-backup-* /srv/prometheus-data/snapshots/

# Restart Prometheus
docker start prometheus

# Verify
docker logs prometheus | grep -i "snapshot"
```

**Option 2: Load Snapshot in Running Prometheus**

```bash
# Extract snapshot directory name
SNAPSHOT=$(tar -tzf prometheus-backup-20240101-120000.tar.gz | head -1 | cut -d'/' -f1)

# Extract to Prometheus data directory
tar -xzf prometheus-backup-20240101-120000.tar.gz -C /srv/prometheus-data/snapshots/

# Prometheus will discover and use snapshot
```

### Verify Prometheus Restore

```bash
# Check snapshot availability in Prometheus UI
curl -s http://localhost:9090/api/v1/status/tsdb | jq .

# Check metrics are available
curl -s 'http://localhost:9090/api/v1/query?query=up' | jq '.data.result | length'

# Check specific metric
curl -s 'http://localhost:9090/api/v1/query?query=node_memory_MemAvailable_bytes' | jq .
```

### Restore Metrics to Different Prometheus Instance

Copy snapshot to target system:

```bash
# On source system
scp /srv/backups/prometheus/backup-20240101-120000.tar.gz user@target:/tmp/

# On target system
tar -xzf /tmp/backup-20240101-120000.tar.gz -C /srv/prometheus-data/snapshots/
docker restart prometheus
```

## Restoring Filesystem Configuration

### Extract Configuration Files

```bash
cd /srv/backups/filesystem/

# Extract to temporary location
mkdir -p /tmp/config-restore
tar -xzf filesystem-backup-20240101-120000.tar.gz -C /tmp/config-restore/

# List extracted files
find /tmp/config-restore -type f
```

### Restore Specific Files

**Option 1: Copy Individual Files**

```bash
# Copy specific config file
cp /tmp/config-restore/etc/nginx/nginx.conf /etc/nginx/nginx.conf

# Copy entire directory
cp -r /tmp/config-restore/srv/app/config/* /srv/app/config/
```

**Option 2: Restore to Different Location**

```bash
# Restore to staging directory for review
mkdir -p /srv/config-staging
tar -xzf filesystem-backup-20240101-120000.tar.gz -C /srv/config-staging/

# Review before applying
diff -r /srv/config-staging/ /srv/app/config/

# Copy when ready
cp -r /srv/config-staging/srv/app/config/* /srv/app/config/
```

### Verify Configuration

```bash
# Check file exists
ls -l /etc/nginx/nginx.conf

# Check permissions
stat /etc/nginx/nginx.conf

# Validate syntax (example: nginx)
nginx -t

# Reload service if needed
systemctl reload nginx
```

## Full System Restore

### Complete Recovery Steps

1. **Stop all services**
   ```bash
   systemctl stop postgres nginx app
   docker stop $(docker ps -q)
   ```

2. **Restore databases**
   ```bash
   # Follow PostgreSQL restore procedure above
   ```

3. **Restore Prometheus**
   ```bash
   # Follow Prometheus restore procedure above
   ```

4. **Restore configurations**
   ```bash
   # Follow filesystem restore procedure above
   ```

5. **Restart services**
   ```bash
   systemctl start postgres nginx app
   docker start $(docker ps -a -q)
   ```

6. **Verify all services**
   ```bash
   # Check service status
   systemctl status postgres nginx app
   
   # Check logs
   journalctl -u postgres -n 20
   
   # Test services
   curl localhost:80
   curl localhost:9090
   ```

## Backup Recovery Testing

### Monthly Recovery Drills

Test restore procedures monthly:

```bash
#!/bin/bash
# test-restore.sh

set -e

echo "Starting backup recovery test..."

# Find latest backups
LATEST_DB=$(ls -t /srv/backups/database/*.tar.gz 2>/dev/null | head -1)
LATEST_PROM=$(ls -t /srv/backups/prometheus/*.tar.gz 2>/dev/null | head -1)
LATEST_FS=$(ls -t /srv/backups/filesystem/*.tar.gz 2>/dev/null | head -1)

# Test database recovery
if [ -f "$LATEST_DB" ]; then
    echo "Testing database backup: $LATEST_DB"
    mkdir -p /tmp/test-restore
    tar -xzf "$LATEST_DB" -C /tmp/test-restore/
    [ -f /tmp/test-restore/database.sql ] && echo "✓ Database dump valid"
fi

# Test Prometheus recovery
if [ -f "$LATEST_PROM" ]; then
    echo "Testing Prometheus backup: $LATEST_PROM"
    tar -tzf "$LATEST_PROM" > /dev/null && echo "✓ Prometheus backup valid"
fi

# Test filesystem recovery
if [ -f "$LATEST_FS" ]; then
    echo "Testing filesystem backup: $LATEST_FS"
    tar -tzf "$LATEST_FS" > /dev/null && echo "✓ Filesystem backup valid"
fi

echo "Backup recovery test complete!"
```

## Disaster Recovery Plan

### RTO/RPO Targets

- **Recovery Time Objective (RTO)**: < 1 hour for full restore
- **Recovery Point Objective (RPO)**: < 1 day (daily backups)

### Backup Locations

Keep offsite backups:

```bash
# Sync to remote server daily
rsync -av /srv/backups/ backup-server:/backups/snapshotter/
```

### Emergency Contact

Document:
- Backup location and credentials
- Recovery procedures (this document)
- Contact person for backup issues

## Troubleshooting Restore

### Corruption Detection

```bash
# Verify backup hasn't corrupted
sha256sum -c backup-20240101-120000.tar.gz.sha256

# Check tar archive integrity
tar -tzf backup-20240101-120000.tar.gz > /dev/null && echo "Archive OK"
```

### Incomplete Extraction

```bash
# Check all files extracted
tar -tzf backup-20240101-120000.tar.gz | wc -l

# Compare with actual files
find /restore/location | wc -l
```

### Insufficient Disk Space

```bash
# Check available space
df -h /

# Estimate extraction size
tar -tzf backup-20240101-120000.tar.gz | wc -l

# Free space if needed
rm -rf /tmp/old-backups
```

## Post-Restore Verification

### Health Checks

```bash
# Database
docker exec postgres psql -U postgres -c "SELECT version();"

# Prometheus
curl -s http://localhost:9090/-/healthy

# Application
curl http://localhost/health
```

### Data Verification

```bash
# Check row counts match
docker exec postgres psql -U postgres -c "SELECT COUNT(*) FROM table_name;"

# Compare with backup documentation
# (Should match records from before backup)
```

---

**Need to backup again? See [Installation Guide](INSTALLATION.md) and [Usage Guide](USAGE.md).**
