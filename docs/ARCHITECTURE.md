# Architecture & Design

System design, architecture decisions, and extensibility guide for Snapshotter.

## System Overview

Snapshotter is a modular, extensible backup orchestration system designed for:

- **Multi-target coordination** - Manage multiple backup types in one operation
- **Resilience** - Continue on individual backup failures
- **Observability** - Comprehensive logging and notifications
- **Extensibility** - Add new backup types easily
- **Type safety** - Full type hints for IDE support

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                       CLI Interface                     │
│              (snapshotter/__main__.py)                  │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│                   BackupOrchestrator                    │
│                 (snapshotter/main.py)                   │
│  - Manages backup execution                            │
│  - Aggregates results                                  │
│  - Handles notifications                              │
│  - Implements retention policies                       │
└──────────────┬──────────────────┬──────────────────────┘
               │                  │
      ┌────────▼─────────┐    ┌───▼────────────────┐
      │  Config Module   │    │  Logger Module     │
      │  (YAML parsing)  │    │  (File/console)    │
      └──────────────────┘    └────────────────────┘
               │
      ┌────────▼────────────────────────────────┐
      │         Backup Targets                  │
      │      (snapshotter/backups/)             │
      │                                         │
      │  ┌──────────┐  ┌──────────┐  ┌──────┐ │
      │  │ Database │  │Prometheus│  │Files │ │
      │  └──────────┘  └──────────┘  └──────┘ │
      └────────────────────────────────────────┘
               │
      ┌────────▼──────────────────────────────┐
      │          Utilities                    │
      │      (snapshotter/utils/)             │
      │                                       │
      │  ┌──────┐  ┌──────────┐  ┌──────┐  │
      │  │Checks│  │Compress  │  │Retent│  │
      │  └──────┘  └──────────┘  └──────┘  │
      └───────────────────────────────────────┘
               │
      ┌────────▼──────────────────────────────┐
      │        Notifications                  │
      │    (snapshotter/notifiers/)           │
      │          └─► Webhooks               │
      └───────────────────────────────────────┘
```

## Module Structure

### Core Package (snapshotter/)

#### `__init__.py`
- Package initialization
- Version definition
- Public API exports

#### `__main__.py`
- CLI entry point
- Argument parsing
- Configuration loading
- Orchestrator initialization

#### `config.py` - Configuration Management
- YAML file loading
- Configuration validation
- Environment variable substitution
- Schema verification

**Key Classes**:
- `Config` - Main configuration class

#### `logger.py` - Logging System
- File-based logging with rotation
- Console output
- Optional syslog integration
- Formatted output with timestamps

**Key Classes**:
- `SnapshatterLogger` - Logger wrapper

#### `exceptions.py` - Exception Hierarchy
```
SnapshatterError (root)
├── ConfigError
├── BackupError
│   ├── DatabaseBackupError
│   ├── PrometheusBackupError
│   └── FilesystemBackupError
├── NotificationError
├── CompressionError
└── RetentionError
```

#### `main.py` - Orchestration Engine
- Backup execution coordination
- Result aggregation
- Notification triggering
- Retention policy enforcement

**Key Classes**:
- `BackupOrchestrator` - Main orchestration logic

### Backup Module (snapshotter/backups/)

#### `base.py` - Abstract Base Classes
Defines interface for all backup types.

**Key Classes**:
- `BackupTarget` - Abstract base for backup implementations
- `BackupResult` - Backup operation result dataclass

#### `database.py` - PostgreSQL Backup
- Uses `docker exec pg_dumpall`
- Creates SQL dump
- Compresses to tar.gz
- Calculates checksums

**Key Classes**:
- `DatabaseBackup` - PostgreSQL backup implementation

#### `prometheus.py` - Prometheus Backup
- Uses `/api/v1/admin/tsdb/snapshot` endpoint
- Zero-downtime snapshots
- Polls for snapshot completion
- Compresses snapshot directory

**Key Classes**:
- `PrometheusBackup` - Prometheus backup implementation

#### `filesystem.py` - Filesystem Backup
- Backs up files and directories
- Supports multiple paths
- Validates all paths exist
- Creates tar.gz archives

**Key Classes**:
- `FilesystemBackup` - Filesystem backup implementation

### Utilities Module (snapshotter/utils/)

#### `checksums.py` - Checksum Management
- SHA256 calculation
- Checksum file writing
- Checksum verification

**Key Functions**:
- `calculate_sha256(file_path)` - Calculate file hash
- `write_checksum(file_path, checksum)` - Write checksum file
- `verify_checksum(file_path)` - Verify file integrity

#### `compression.py` - Archive Management
- tar.gz creation
- Archive extraction
- Archive validation

**Key Functions**:
- `create_tar_gz(source, output)` - Create archive
- `extract_tar_gz(archive, path)` - Extract archive
- `verify_tar_gz(archive)` - Validate archive

#### `retention.py` - Backup Retention
- Find old backups
- Delete expired backups
- Report cleanup statistics

**Key Functions**:
- `find_old_backups(dir, pattern, days)` - Find old files
- `cleanup_old_backups(dir, pattern, days)` - Delete old files

### Notifiers Module (snapshotter/notifiers/)

#### `base.py` - Abstract Notifier
Defines interface for notification systems.

**Key Classes**:
- `BaseNotifier` - Abstract base for notifiers
- `NotificationResult` - Notification operation result

#### `webhook.py` - Webhook Notifier
- HTTP POST to webhook URL
- JSON payload with event data
- Error handling and timeout protection

**Key Classes**:
- `WebhookNotifier` - Webhook-based notifications

## Data Flow

### Backup Execution

```
1. Load Configuration
   ├─ Parse YAML file
   ├─ Validate schema
   └─ Substitute environment variables

2. Initialize Logger
   ├─ Create log file
   ├─ Setup rotation
   └─ Configure output

3. Create BackupOrchestrator
   └─ Initialize with config and logger

4. Execute Orchestrator.run()
   ├─ For each backup target:
   │  ├─ Create target instance
   │  ├─ Validate configuration
   │  └─ Execute backup()
   │
   ├─ Aggregate results
   │
   ├─ Execute retention cleanup
   │
   ├─ Send notifications
   │
   └─ Log summary

5. Return success status
```

### Single Backup Execution

```
BackupTarget.backup(backup_dir)
├─ Record start time
├─ Try execution:
│  ├─ Validate target config
│  ├─ Create output directory
│  ├─ Execute backup operation
│  │  └─ Type-specific logic
│  ├─ Verify archive integrity
│  ├─ Calculate checksum
│  └─ Write checksum file
├─ Record end time
└─ Return BackupResult with:
   ├─ success (bool)
   ├─ backup_file (Path or None)
   ├─ error_message (str or None)
   ├─ duration_seconds (float)
   ├─ size_mb (float)
   └─ metadata (dict)
```

## Design Decisions

### 1. Abstract Base Classes for Extensibility

**Decision**: Use `ABC` with abstract methods for backup types

**Rationale**:
- Clear interface contract
- Easy to add new backup types
- Type-safe implementation

**Example**: To add a new backup type:
```python
from snapshotter.backups import BackupTarget, BackupResult

class MySQLBackup(BackupTarget):
    def backup(self, backup_dir: Path) -> BackupResult:
        # Implementation
        pass
    
    def validate_config(self) -> bool:
        # Validation
        pass
```

### 2. Dataclasses for Result Objects

**Decision**: Use `@dataclass` for `BackupResult` and `NotificationResult`

**Rationale**:
- Immutable by default
- Type safety
- Easy serialization to JSON
- Properties for computed values

### 3. Environment Variable Substitution

**Decision**: Support `${VAR_NAME}` in configuration

**Rationale**:
- Secrets not stored in files
- Different deployments (dev/staging/prod)
- Secure credential management

### 4. Graceful Degradation

**Decision**: Continue on individual backup failures

**Rationale**:
- If database fails, Prometheus still backs up
- If notification fails, backup still succeeds
- Better observability of issues

### 5. Zero-Downtime Prometheus Snapshots

**Decision**: Use API snapshot method instead of filesystem copy

**Rationale**:
- No service interruption
- Consistent snapshots
- Prometheus continues serving

### 6. Type Hints Throughout

**Decision**: 100% type coverage

**Rationale**:
- IDE autocompletion support
- Catch bugs at development time
- Self-documenting code
- mypy compatibility

## Extensibility Guide

### Adding a New Backup Type

1. **Create backup implementation**:
```python
# snapshotter/backups/mybackup.py
from pathlib import Path
from snapshotter.backups import BackupTarget, BackupResult

class MyBackup(BackupTarget):
    def backup(self, backup_dir: Path) -> BackupResult:
        start_time = datetime.now()
        try:
            # Your backup logic here
            pass
        except Exception as e:
            return BackupResult(..., success=False, error_message=str(e))
    
    def validate_config(self) -> bool:
        return bool(self.config.get("required_field"))
```

2. **Update backups/__init__.py**:
```python
from snapshotter.backups.mybackup import MyBackup
__all__ = [..., "MyBackup"]
```

3. **Update main.py** to handle new type:
```python
if backup_type == "mybackup":
    target = MyBackup(backup_name_str, backup_config)
```

4. **Add test file** `tests/test_mybackup.py`:
```python
def test_mybackup_success():
    backup = MyBackup("test", {...})
    result = backup.backup(Path("/tmp"))
    assert result.success
```

### Adding a New Notifier Type

1. **Create notifier implementation**:
```python
# snapshotter/notifiers/mynotifier.py
from snapshotter.notifiers import BaseNotifier, NotificationResult

class MyNotifier(BaseNotifier):
    def notify(self, event: str, data: Dict[str, Any]) -> NotificationResult:
        # Your notification logic
        pass
    
    def validate_config(self) -> bool:
        return bool(self.config.get("required_field"))
```

2. **Update notifiers/__init__.py**:
```python
from snapshotter.notifiers.mynotifier import MyNotifier
__all__ = [..., "MyNotifier"]
```

3. **Update main.py** to use new notifier:
```python
if "mynotifier" in notifications_config:
    notifier = MyNotifier(notifications_config["mynotifier"])
```

## Performance Characteristics

### Backup Speed

- **PostgreSQL**: 10-50 MB/s (depends on disk I/O)
- **Prometheus**: 1-5 seconds (API overhead) + compression
- **Filesystem**: 50-200 MB/s (depends on file count)

### Compression Ratios

- **PostgreSQL SQL**: 3-5x compression
- **Prometheus metrics**: 3-8x compression
- **Filesystem configs**: 2-4x compression

### Memory Usage

- **Running backup**: ~50-100 MB
- **Compression**: Streaming (low memory)
- **Notification**: Minimal overhead

### Disk I/O

- **Log rotation**: 10 MB per file, 5 backups kept
- **Checksums**: Small (~64 bytes per backup)
- **Metadata**: Minimal

## Security Considerations

### File Permissions

- Backup directory: `700` (rwx------)
- Log files: `600` (rw-------)
- Configuration: `600` (rw-------)

### Credential Management

- Passwords in configuration via environment variables
- No credentials logged
- Webhook URLs can contain tokens

### Data Integrity

- SHA256 checksums for all backups
- Archive integrity validation
- Error on checksum mismatch

## Testing Strategy

### Unit Tests (48+ cases)

- Configuration parsing
- Logger functionality
- Backup implementations
- Utility functions
- Notifications

### Integration Tests

- End-to-end backup execution
- Result aggregation
- Error handling

### Mock Fixtures

- Docker operations
- Prometheus API
- Webhook requests
- File system operations

## Future Enhancements

Potential extensions:

- **S3/GCS backup**: Store backups to cloud
- **Backup deduplication**: Reduce storage with dedup
- **Incremental backups**: Only backup changes
- **Encryption**: AES-256 encryption for backups
- **Multi-site replication**: Sync to multiple locations
- **Backup verification**: Periodic integrity checks
- **Additional notifiers**: Slack, PagerDuty, email
- **Metrics export**: Prometheus metrics about backups
- **Web dashboard**: View backup status and history

## Deployment Patterns

### Single Server

```
Server
├─ PostgreSQL (docker)
├─ Prometheus (docker)
├─ Snapshotter (cron job)
└─ Backups (/srv/backups)
```

### HA Setup

```
Primary               Secondary
├─ Snapshotter       ├─ Snapshotter
├─ Backups           ├─ Backups
└─ Replication ◄────► Replication
```

### Offsite Backup

```
Local                  Remote
├─ Snapshotter        ├─ Backups
├─ Backups            └─ rsync receiver
└─ rsync client ────► 
```

---

**Ready to extend? Check [Usage Guide](USAGE.md) for deployment details.**
