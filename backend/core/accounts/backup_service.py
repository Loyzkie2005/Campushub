import os
import subprocess
from datetime import datetime
from pathlib import Path

from django.conf import settings

# Backup directory
BACKUP_DIR = Path(settings.PROJECT_ROOT) / "backups"
BACKUP_DIR.mkdir(exist_ok=True)


def get_db_config():
    """Get database connection info from Django settings."""
    db = settings.DATABASES["default"]
    return {
        "host": db["HOST"],
        "port": db["PORT"],
        "name": db["NAME"],
        "user": db["USER"],
        "password": db["PASSWORD"],
    }


def create_backup(backup_type="full"):
    """
    Create a PostgreSQL backup using pg_dump.
    Returns dict with backup info or error.
    """
    db = get_db_config()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"campushub_postgres_{timestamp}.sql"
    filepath = BACKUP_DIR / filename

    # Build pg_dump command
    env = os.environ.copy()
    env["PGPASSWORD"] = db["password"]

    # Find pg_dump path
    pg_dump = "pg_dump"
    pg_paths = [
        r"C:\Program Files\PostgreSQL\18\bin\pg_dump.exe",
        r"C:\Program Files\PostgreSQL\17\bin\pg_dump.exe",
        r"C:\Program Files\PostgreSQL\16\bin\pg_dump.exe",
    ]
    for p in pg_paths:
        if os.path.exists(p):
            pg_dump = f'"{p}"'
            break

    # Determine tables based on backup type
    if backup_type == "marketplace":
        tables = "--table=campushub_product --table=campushub_orders --table=campushub_seller_request"
    elif backup_type == "users":
        tables = "--table=campushub_accounts_user --table=campushub_department --table=campushub_role"
    elif backup_type == "facilities":
        tables = "--table=campushub_facility --table=campushub_rooms"
    else:
        tables = ""  # Full backup

    cmd = (
        f'{pg_dump} -h {db["host"]} -p {db["port"]} -U {db["user"]} '
        f'-d {db["name"]} {tables} -f "{filepath}"'
    )

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode == 0 and filepath.exists():
            size = filepath.stat().st_size
            return {
                "success": True,
                "filename": filename,
                "filepath": str(filepath),
                "size": size,
                "size_display": format_size(size),
                "timestamp": datetime.now(),
                "type": backup_type,
            }
        else:
            return {
                "success": False,
                "error": result.stderr or "pg_dump failed",
                "filename": filename,
            }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Backup timed out (120s)"}
    except FileNotFoundError:
        return {
            "success": False,
            "error": "pg_dump not found. Install PostgreSQL client tools.",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_backup_list():
    """List all backup files with metadata."""
    backups = []
    if not BACKUP_DIR.exists():
        return backups

    for f in sorted(BACKUP_DIR.glob("campushub_*.sql"), reverse=True):
        stat = f.stat()
        backups.append({
            "filename": f.name,
            "filepath": str(f),
            "size": stat.st_size,
            "size_display": format_size(stat.st_size),
            "created_at": datetime.fromtimestamp(stat.st_mtime),
            "status": "Completed" if stat.st_size > 0 else "Failed",
            "type": "PostgreSQL Database",
        })

    return backups


def get_backup_stats():
    """Get backup statistics."""
    backups = get_backup_list()
    total = len(backups)
    successful = sum(1 for b in backups if b["status"] == "Completed")
    failed = total - successful
    total_size = sum(b["size"] for b in backups)
    last_backup = backups[0]["created_at"] if backups else None

    return {
        "total": total,
        "successful": successful,
        "failed": failed,
        "total_size": format_size(total_size),
        "total_size_bytes": total_size,
        "storage_percent": round(total_size / (40 * 1024 * 1024 * 1024) * 100, 2) if total_size else 0,
        "last_backup": last_backup,
    }


def delete_backup(filename):
    """Delete a backup file."""
    filepath = BACKUP_DIR / filename
    if filepath.exists() and filepath.parent == BACKUP_DIR:
        filepath.unlink()
        return True
    return False


def restore_backup(filepath):
    """
    Restore a PostgreSQL backup using psql.
    Returns dict with result info.
    """
    db = get_db_config()
    env = os.environ.copy()
    env["PGPASSWORD"] = db["password"]

    # Find psql path
    psql = "psql"
    psql_paths = [
        r"C:\Program Files\PostgreSQL\18\bin\psql.exe",
        r"C:\Program Files\PostgreSQL\17\bin\psql.exe",
        r"C:\Program Files\PostgreSQL\16\bin\psql.exe",
    ]
    for p in psql_paths:
        if os.path.exists(p):
            psql = f'"{p}"'
            break

    cmd = (
        f'{psql} -h {db["host"]} -p {db["port"]} -U {db["user"]} '
        f'-d {db["name"]} -f "{filepath}"'
    )

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            env=env,
            capture_output=True,
            text=True,
            timeout=180,
        )

        if result.returncode == 0:
            return {"success": True, "message": "Database restored successfully."}
        else:
            return {"success": False, "error": result.stderr or "psql restore failed"}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Restore timed out (180s)"}
    except FileNotFoundError:
        return {"success": False, "error": "psql not found. Install PostgreSQL client tools."}
    except Exception as e:
        return {"success": False, "error": str(e)}


def restore_from_upload(uploaded_file):
    """
    Save uploaded file and restore it.
    """
    # Save uploaded file to backups dir
    filename = uploaded_file.name
    if not filename.endswith((".sql", ".zip")):
        return {"success": False, "error": "Only .sql and .zip files are supported."}

    save_path = BACKUP_DIR / f"restore_{filename}"
    with open(save_path, "wb") as f:
        for chunk in uploaded_file.chunks():
            f.write(chunk)

    if filename.endswith(".sql"):
        result = restore_backup(save_path)
        # Clean up the uploaded restore file
        if save_path.exists():
            save_path.unlink()
        return result
    else:
        return {"success": False, "error": ".zip restore not yet implemented. Use .sql files."}


def get_latest_backup():
    """Get the most recent successful backup file path."""
    backups = get_backup_list()
    for b in backups:
        if b["status"] == "Completed":
            return b
    return None


# ── Auto Backup Settings (stored in a JSON file) ──
import json

AUTO_BACKUP_CONFIG = BACKUP_DIR / "auto_backup_config.json"

DEFAULT_CONFIG = {
    "enabled": True,
    "frequency": "daily",
    "time": "02:30",
}


def get_auto_backup_config():
    """Load auto backup settings."""
    if AUTO_BACKUP_CONFIG.exists():
        try:
            with open(AUTO_BACKUP_CONFIG) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return DEFAULT_CONFIG.copy()


def save_auto_backup_config(enabled, frequency):
    """Save auto backup settings."""
    config = get_auto_backup_config()
    config["enabled"] = enabled
    config["frequency"] = frequency
    with open(AUTO_BACKUP_CONFIG, "w") as f:
        json.dump(config, f, indent=2)
    return config


def format_size(size_bytes):
    """Format bytes to human readable."""
    if size_bytes == 0:
        return "0 B"
    elif size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
