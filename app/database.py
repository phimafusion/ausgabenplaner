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
    cursor.execute("DROP TABLE IF EXISTS contributions;")
    cursor.execute("DROP TABLE IF EXISTS positions;")
    cursor.execute("DROP TABLE IF EXISTS versions;")
    cursor.execute("DROP TABLE IF EXISTS plans;")
    cursor.execute("DROP TABLE IF EXISTS users;")
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
        can_export INTEGER NOT NULL DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    )

    # Migration for users table
    user_cols = [row[1] for row in cursor.execute("PRAGMA table_info(users)").fetchall()]
    if "can_export" not in user_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN can_export INTEGER NOT NULL DEFAULT 1")

    # Plans table
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

    conn.commit()

    # Seed default admin user if not exists
    from app.auth import get_password_hash

    admin_exists = cursor.execute("SELECT id FROM users WHERE username = 'admin'").fetchone()
    if not admin_exists:
        admin_pass = os.getenv("ADMIN_PASSWORD", "admin123")
        cursor.execute(
            "INSERT INTO users (username, password_hash, name, role, can_export) VALUES (?, ?, ?, ?, 1)",
            ("admin", get_password_hash(admin_pass), "Administrator", "admin"),
        )
        conn.commit()

    # Seed initial plan and dataset from screenshot if not exists
    plan_exists = cursor.execute("SELECT id FROM plans LIMIT 1").fetchone()
    if not plan_exists:
        cursor.execute("INSERT INTO plans (title, description) VALUES (?, ?)", ("Tütingstraße 22", "Haushalts-Ausgabenplaner"))
        plan_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO versions (plan_id, title, effective_date, is_active, created_by) VALUES (?, ?, ?, 1, 'Administrator')",
            (plan_id, "Stand ab 01.09.2026", "2026-09-01"),
        )
        version_id = cursor.lastrowid

        if seed:
            # Positions from user spreadsheet
            positions_seed = [
                ("Miete (Kalt + Nebenkosten) an Vermieter", -1235.00, ""),
                ("Kita", -60.00, ""),
                ("Strom / Naturstrom", -87.00, ""),
                ("Wasser (Stadtwerke OS)", -38.00, ""),
                ("eprimo (Gas)", -143.00, ""),
                ("Internet / Osnatel", -40.00, "Wird an Phil überwiesen"),
                ("OSBO Versicherung", -38.72, "Wird quartalsweise eingezogen (COSMOS)"),
                ("OSBO Steuer", -8.50, "Wird jährlich eingezogen, (Bundeskasse Kiel)"),
                ("Rundfunkgebühr", -18.36, "Wird quartalsweise eingezogen, Wird an Sabrina überwiesen"),
                ("OSC Mitgliedschaft Jonti", 0.00, ""),
                ("Familienhaftpflichtversicherung", -6.41, "Wird jährlich eingezogen (COSMOS)"),
                ("Hausratsversicherung", -9.17, "Wird jährlich eingezogen (Docura)"),
            ]

            for idx, (title, amount, comment) in enumerate(positions_seed):
                cursor.execute(
                    "INSERT INTO positions (version_id, title, amount, comment, sort_order) VALUES (?, ?, ?, ?, ?)",
                    (version_id, title, amount, comment, idx),
                )

            # Contributions from user spreadsheet
            contributions_seed = [
                ("Phil", 930.00, "Zahlung Phil"),
                ("Sabrina", 800.00, "Zahlung Sabrina"),
            ]

            for idx, (person, amount, comment) in enumerate(contributions_seed):
                cursor.execute(
                    "INSERT INTO contributions (version_id, person_name, amount, comment, sort_order) VALUES (?, ?, ?, ?, ?)",
                    (version_id, person, amount, comment, idx),
                )

        conn.commit()

    conn.close()
