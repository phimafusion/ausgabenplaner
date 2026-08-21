import os
import sqlite3
import datetime
import zoneinfo
from pathlib import Path
from typing import Dict, Any, List, Optional


def get_app_timezone() -> datetime.tzinfo:
    """
    Return local timezone:
    1. If APP_TIMEZONE or TZ environment variable is explicitly set, use zoneinfo.ZoneInfo.
    2. Otherwise, detect host/system local timezone dynamically via datetime.datetime.now().astimezone().tzinfo.
    3. Fallback to Europe/Berlin or UTC.
    """
    tz_env = os.getenv("APP_TIMEZONE") or os.getenv("TZ")
    if tz_env:
        try:
            return zoneinfo.ZoneInfo(tz_env)
        except Exception:
            pass
    try:
        local_tz = datetime.datetime.now().astimezone().tzinfo
        if local_tz is not None:
            return local_tz
    except Exception:
        pass
    try:
        return zoneinfo.ZoneInfo("Europe/Berlin")
    except Exception:
        return datetime.timezone.utc


def get_local_now() -> datetime.datetime:
    """Return current localized datetime according to local/configured timezone."""
    return datetime.datetime.now(get_app_timezone())


def format_file_size(size_bytes: int) -> str:
    """Format bytes into readable KB / MB string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"


def get_backup_settings(conn: sqlite3.Connection) -> Dict[str, Any]:
    """Retrieve current backup configuration."""
    row = conn.execute("SELECT * FROM backup_settings WHERE id = 1").fetchone()
    if not row:
        conn.execute(
            "INSERT INTO backup_settings (id, backup_enabled, backup_frequency, backup_folder, retention_count, auto_backup_time) VALUES (1, 1, 'daily', 'data/backups', 14, '03:00')"
        )
        conn.commit()
        row = conn.execute("SELECT * FROM backup_settings WHERE id = 1").fetchone()

    d = dict(row)
    d["backup_enabled"] = bool(d.get("backup_enabled", 1))
    d["backup_frequency"] = d.get("backup_frequency") or "daily"
    d["retention_count"] = int(d.get("retention_count", 14))
    d["backup_folder"] = d.get("backup_folder", "data/backups")
    d["auto_backup_time"] = d.get("auto_backup_time", "03:00")
    return d


def update_backup_settings(
    conn: sqlite3.Connection,
    backup_enabled: Optional[bool] = None,
    backup_frequency: Optional[str] = None,
    backup_folder: Optional[str] = None,
    retention_count: Optional[int] = None,
    auto_backup_time: Optional[str] = None,
) -> Dict[str, Any]:
    """Update backup settings in database."""
    current = get_backup_settings(conn)
    new_enabled = (1 if backup_enabled else 0) if backup_enabled is not None else (1 if current["backup_enabled"] else 0)
    allowed_freqs = {"daily", "every_12_hours", "every_6_hours", "hourly", "weekly"}
    new_freq = backup_frequency.strip() if (backup_frequency and backup_frequency.strip() in allowed_freqs) else current["backup_frequency"]
    new_folder = backup_folder.strip() if backup_folder and backup_folder.strip() else current["backup_folder"]
    new_retention = max(1, min(retention_count, 365)) if retention_count is not None else current["retention_count"]
    new_time = auto_backup_time.strip() if auto_backup_time and auto_backup_time.strip() else current["auto_backup_time"]

    conn.execute(
        """
        UPDATE backup_settings 
        SET backup_enabled = ?, backup_frequency = ?, backup_folder = ?, retention_count = ?, auto_backup_time = ?
        WHERE id = 1
        """,
        (new_enabled, new_freq, new_folder, new_retention, new_time),
    )
    conn.commit()
    return get_backup_settings(conn)


def create_database_backup(
    conn: sqlite3.Connection,
    custom_folder: Optional[str] = None,
    custom_retention: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Create an atomic SQLite snapshot using the native sqlite3 backup API.
    Saves file with timestamp and rotates old backups when retention_count is exceeded.
    """
    settings = get_backup_settings(conn)
    target_folder_str = custom_folder or settings["backup_folder"]
    retention = custom_retention or settings["retention_count"]

    target_dir = Path(target_folder_str)
    target_dir.mkdir(parents=True, exist_ok=True)

    now = get_local_now()
    timestamp_str = now.strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"ausgabenplaner_backup_{timestamp_str}.db"
    dest_path = target_dir / filename

    # Perform native transactional backup
    dest_conn = sqlite3.connect(str(dest_path))
    try:
        conn.backup(dest_conn)
    finally:
        dest_conn.close()

    file_size = dest_path.stat().st_size if dest_path.exists() else 0
    now_iso = now.strftime("%Y-%m-%d %H:%M:%S")

    # Update last_backup_at
    conn.execute("UPDATE backup_settings SET last_backup_at = ? WHERE id = 1", (now_iso,))
    conn.commit()

    # Prune / Rotate older backups if count exceeds retention
    pruned_files = []
    backup_files = sorted(
        [f for f in target_dir.glob("ausgabenplaner_backup_*.db") if f.is_file()],
        key=lambda x: x.name,
    )

    if len(backup_files) > retention:
        files_to_remove = backup_files[: len(backup_files) - retention]
        for old_file in files_to_remove:
            try:
                old_file.unlink()
                pruned_files.append(old_file.name)
            except Exception as e:
                print(f"Error pruning old backup {old_file}: {e}")

    return {
        "filename": filename,
        "path": str(dest_path),
        "file_size": file_size,
        "file_size_formatted": format_file_size(file_size),
        "created_at": now_iso,
        "pruned_files": pruned_files,
        "total_backups_count": len(backup_files) - len(pruned_files),
    }


def list_database_backups(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    """List all available backup files in the configured folder sorted descending by date."""
    settings = get_backup_settings(conn)
    target_dir = Path(settings["backup_folder"])

    if not target_dir.exists():
        return []

    backup_files = [f for f in target_dir.glob("*.db") if f.is_file()]
    backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

    tz = get_app_timezone()
    result = []
    for f in backup_files:
        st = f.stat()
        mtime = datetime.datetime.fromtimestamp(st.st_mtime, tz=tz)
        result.append(
            {
                "filename": f.name,
                "file_size": st.st_size,
                "file_size_formatted": format_file_size(st.st_size),
                "created_at": mtime.strftime("%Y-%m-%d %H:%M:%S"),
            }
        )
    return result


def delete_database_backup(conn: sqlite3.Connection, filename: str) -> bool:
    """Delete a specific backup file safely."""
    # Prevent path traversal
    clean_filename = Path(filename).name
    settings = get_backup_settings(conn)
    target_path = Path(settings["backup_folder"]) / clean_filename

    if target_path.exists() and target_path.is_file():
        target_path.unlink()
        return True
    return False


def get_backup_file_path(conn: sqlite3.Connection, filename: str) -> Optional[Path]:
    """Retrieve absolute file path for a backup after path-traversal check."""
    clean_filename = Path(filename).name
    settings = get_backup_settings(conn)
    target_path = Path(settings["backup_folder"]) / clean_filename

    if target_path.exists() and target_path.is_file():
        return target_path
    return None


def restore_database_backup(conn: sqlite3.Connection, filename: str) -> Dict[str, Any]:
    """
    Restore a database snapshot atomically into the active database connection.
    Uses SQLite's online backup API to copy snapshot into live connection safely.
    """
    clean_filename = Path(filename).name
    settings = get_backup_settings(conn)
    src_path = Path(settings["backup_folder"]) / clean_filename

    if not src_path.exists() or not src_path.is_file():
        raise FileNotFoundError(f"Backup-Datei '{filename}' nicht gefunden")

    src_conn = sqlite3.connect(str(src_path))
    try:
        src_conn.backup(conn)
    finally:
        src_conn.close()

    now_iso = get_local_now().strftime("%Y-%m-%d %H:%M:%S")
    return {
        "success": True,
        "filename": clean_filename,
        "restored_at": now_iso,
        "message": f"Datenbank erfolgreich auf Stand '{clean_filename}' wiederhergestellt",
    }

