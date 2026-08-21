import os
import sqlite3
from typing import Generator, Optional

def get_db_path() -> str:
    if os.getenv("TESTING") == "1":
        return "data/test_ausgabenplaner.db"
    return os.getenv("DB_PATH", "data/ausgabenplaner.db")


def get_db_connection() -> sqlite3.Connection:
    db_path = get_db_path()
    if db_path != ":memory:":
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def get_db() -> Generator[sqlite3.Connection, None, None]:
    conn = get_db_connection()
    try:
        yield conn
    finally:
        conn.close()


def reset_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS categories;")
    cursor.execute("DROP TABLE IF EXISTS user_plans;")
    cursor.execute("DROP TABLE IF EXISTS contributions;")
    cursor.execute("DROP TABLE IF EXISTS positions;")
    cursor.execute("DROP TABLE IF EXISTS versions;")
    cursor.execute("DROP TABLE IF EXISTS plans;")
    cursor.execute("DROP TABLE IF EXISTS users;")
    cursor.execute("DROP TABLE IF EXISTS backup_settings;")
    conn.commit()
    conn.close()


def init_db(seed: Optional[bool] = None):
    if seed is None:
        seed = os.getenv("TESTING") != "1"

    conn = get_db_connection()
    cursor = conn.cursor()

    # Users table
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        name TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'user',
        can_manage_plans INTEGER NOT NULL DEFAULT 0,
        can_manage_categories INTEGER NOT NULL DEFAULT 0,
        can_export INTEGER NOT NULL DEFAULT 1,
        can_import INTEGER NOT NULL DEFAULT 0,
        can_manage_backups INTEGER NOT NULL DEFAULT 0,
        can_manage_users INTEGER NOT NULL DEFAULT 0,
        can_run_testsuite INTEGER NOT NULL DEFAULT 0,
        can_view_changelog INTEGER NOT NULL DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    )

    # Migration for users table
    user_cols = [row[1] for row in cursor.execute("PRAGMA table_info(users)").fetchall()]
    user_col_defs = {
        "can_manage_plans": "INTEGER NOT NULL DEFAULT 0",
        "can_manage_categories": "INTEGER NOT NULL DEFAULT 0",
        "can_export": "INTEGER NOT NULL DEFAULT 1",
        "can_import": "INTEGER NOT NULL DEFAULT 0",
        "can_manage_backups": "INTEGER NOT NULL DEFAULT 0",
        "can_manage_users": "INTEGER NOT NULL DEFAULT 0",
        "can_run_testsuite": "INTEGER NOT NULL DEFAULT 0",
        "can_view_changelog": "INTEGER NOT NULL DEFAULT 1",
    }
    for col_name, col_def in user_col_defs.items():
        if col_name not in user_cols:
            cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}")

    # Plans table
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        is_archived INTEGER NOT NULL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    )

    # Migration for plans table
    plan_cols = [row[1] for row in cursor.execute("PRAGMA table_info(plans)").fetchall()]
    if "is_archived" not in plan_cols:
        cursor.execute("ALTER TABLE plans ADD COLUMN is_archived INTEGER NOT NULL DEFAULT 0")

    # User-Plan Assignments table (Multi-Plan RBAC)
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS user_plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        plan_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, plan_id),
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
        FOREIGN KEY (plan_id) REFERENCES plans (id) ON DELETE CASCADE
    );
    """
    )

    # Versions / Snapshots ("Stände") table
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS versions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        plan_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        effective_date TEXT,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_by TEXT DEFAULT 'Administrator',
        updated_at TIMESTAMP,
        updated_by TEXT,
        FOREIGN KEY (plan_id) REFERENCES plans (id) ON DELETE CASCADE
    );
    """
    )

    # Migration for existing databases
    ver_cols = [row[1] for row in cursor.execute("PRAGMA table_info(versions)").fetchall()]
    if "created_by" not in ver_cols:
        cursor.execute("ALTER TABLE versions ADD COLUMN created_by TEXT DEFAULT 'Administrator'")
    if "updated_at" not in ver_cols:
        cursor.execute("ALTER TABLE versions ADD COLUMN updated_at TIMESTAMP")
    if "updated_by" not in ver_cols:
        cursor.execute("ALTER TABLE versions ADD COLUMN updated_by TEXT")

    # Positions table
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS positions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        version_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        amount REAL NOT NULL,
        comment TEXT,
        category TEXT,
        sort_order INTEGER DEFAULT 0,
        FOREIGN KEY (version_id) REFERENCES versions (id) ON DELETE CASCADE
    );
    """
    )

    # Contributions table
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS contributions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        version_id INTEGER NOT NULL,
        person_name TEXT NOT NULL,
        amount REAL NOT NULL,
        comment TEXT,
        sort_order INTEGER DEFAULT 0,
        FOREIGN KEY (version_id) REFERENCES versions (id) ON DELETE CASCADE
    );
    """
    )

    # Backup Settings table
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS backup_settings (
        id INTEGER PRIMARY KEY,
        backup_enabled INTEGER NOT NULL DEFAULT 1,
        backup_frequency TEXT NOT NULL DEFAULT 'daily',
        backup_folder TEXT NOT NULL DEFAULT 'data/backups',
        retention_count INTEGER NOT NULL DEFAULT 14,
        auto_backup_time TEXT NOT NULL DEFAULT '03:00',
        last_backup_at TEXT
    );
    """
    )

    # Categories table
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        color TEXT NOT NULL DEFAULT '#64748b',
        icon TEXT NOT NULL DEFAULT '📦',
        is_default INTEGER NOT NULL DEFAULT 0,
        sort_order INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    )

    # Seed default categories if table is empty
    default_categories = [
        ("Wohnen", "#3b82f6", "🏠", 1, 0),
        ("Energie & Nebenkosten", "#eab308", "⚡", 1, 1),
        ("Versicherung", "#10b981", "🛡️", 1, 2),
        ("Instandhaltung", "#f97316", "🔧", 1, 3),
        ("Rücklagen & Sparen", "#8b5cf6", "💰", 1, 4),
        ("Medien & Kommunikation", "#06b6d4", "🌐", 1, 5),
        ("Kind", "#ec4899", "👶", 1, 6),
        ("Freizeit", "#14b8a6", "🎉", 1, 7),
        ("Allgemein", "#64748b", "📦", 1, 8),
    ]
    for cat_name, cat_color, cat_icon, cat_default, cat_order in default_categories:
        cursor.execute(
            """
            INSERT OR IGNORE INTO categories (name, color, icon, is_default, sort_order)
            VALUES (?, ?, ?, ?, ?)
            """,
            (cat_name, cat_color, cat_icon, cat_default, cat_order),
        )

    # Migration for backup_settings
    backup_cols = [row[1] for row in cursor.execute("PRAGMA table_info(backup_settings)").fetchall()]
    if "backup_frequency" not in backup_cols:
        cursor.execute("ALTER TABLE backup_settings ADD COLUMN backup_frequency TEXT NOT NULL DEFAULT 'daily'")

    # Ensure default row exists
    settings_exists = cursor.execute("SELECT id FROM backup_settings WHERE id = 1").fetchone()
    if not settings_exists:
        cursor.execute(
            "INSERT INTO backup_settings (id, backup_enabled, backup_frequency, backup_folder, retention_count, auto_backup_time) VALUES (1, 1, 'daily', 'data/backups', 14, '03:00')"
        )

    conn.commit()

    # Seed default admin user if not exists
    from app.auth import get_password_hash

    admin_exists = cursor.execute("SELECT id FROM users WHERE username = 'admin'").fetchone()
    if not admin_exists:
        admin_pass = os.getenv("ADMIN_PASSWORD", "admin123")
        cursor.execute(
            "INSERT OR IGNORE INTO users (username, password_hash, name, role, can_manage_plans, can_manage_categories, can_export, can_import, can_manage_backups, can_manage_users, can_run_testsuite, can_view_changelog) VALUES (?, ?, ?, ?, 1, 1, 1, 1, 1, 1, 1, 1)",
            ("admin", get_password_hash(admin_pass), "Administrator", "admin"),
        )
        conn.commit()

    # Create initial empty plan structure if not exists
    plan_exists = cursor.execute("SELECT id FROM plans LIMIT 1").fetchone()
    if not plan_exists:
        cursor.execute("INSERT INTO plans (title, description) VALUES (?, ?)", ("Muster-Wirtschaftsplan", "Haushalts-Ausgabenplaner"))
        plan_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO versions (plan_id, title, effective_date, is_active, created_by) VALUES (?, ?, ?, 1, 'Administrator')",
            (plan_id, "Aktueller Stand", None),
        )
        conn.commit()

    conn.close()
