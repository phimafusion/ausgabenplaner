import os
import shutil
import sqlite3
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db, init_db, reset_db, get_db_connection
from app import backups


@pytest.fixture(autouse=True)
def setup_test_db():
    os.environ["TESTING"] = "1"
    reset_db()
    init_db(seed=True)
    yield
    reset_db()
    # Cleanup any test backup folders
    for test_dir in ["data/test_backups", "data/test_rotation_backups"]:
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir, ignore_errors=True)


def get_admin_token(client: TestClient) -> str:
    res = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert res.status_code == 200
    return res.json()["access_token"]


def get_user_token(client: TestClient) -> str:
    admin_token = get_admin_token(client)
    client.post(
        "/api/users",
        json={"username": "testuser", "name": "Normal User", "password": "user123", "role": "user", "can_export": True},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    res = client.post("/api/auth/login", json={"username": "testuser", "password": "user123"})
    assert res.status_code == 200
    return res.json()["access_token"]


def test_backup_settings_crud_api():
    client = TestClient(app)
    admin_token = get_admin_token(client)
    user_token = get_user_token(client)

    # 1. Admin gets initial settings
    res = client.get("/api/admin/backups/settings", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["backup_enabled"] is True
    assert data["backup_frequency"] == "daily"
    assert data["retention_count"] == 14
    assert data["auto_backup_time"] == "03:00"
    assert data["backup_folder"] == "data/backups"

    # 2. Admin updates settings
    update_res = client.patch(
        "/api/admin/backups/settings",
        json={
            "backup_enabled": False,
            "backup_frequency": "every_12_hours",
            "retention_count": 7,
            "auto_backup_time": "04:30",
            "backup_folder": "data/test_backups",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert update_res.status_code == 200
    updated_data = update_res.json()
    assert updated_data["backup_enabled"] is False
    assert updated_data["backup_frequency"] == "every_12_hours"
    assert updated_data["retention_count"] == 7
    assert updated_data["auto_backup_time"] == "04:30"
    assert updated_data["backup_folder"] == "data/test_backups"

    # 3. Regular user forbidden (403)
    user_res = client.get("/api/admin/backups/settings", headers={"Authorization": f"Bearer {user_token}"})
    assert user_res.status_code == 403


def test_create_manual_backup_and_retention_rotation():
    client = TestClient(app)
    admin_token = get_admin_token(client)

    test_folder = "data/test_rotation_backups"
    if os.path.exists(test_folder):
        shutil.rmtree(test_folder)

    # Configure retention count to 3
    client.patch(
        "/api/admin/backups/settings",
        json={"retention_count": 3, "backup_folder": test_folder},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    # Create 5 snapshots in sequence
    conn = get_db_connection()
    try:
        # Create directly via helper with simulated filenames to test rotation cleanly
        for i in range(1, 6):
            target_file = Path(test_folder) / f"ausgabenplaner_backup_2026-08-18_00-00-0{i}.db"
            target_file.parent.mkdir(parents=True, exist_ok=True)
            with open(target_file, "w") as f:
                f.write(f"dummy backup content {i}")

        # Now trigger create backup through API
        res = client.post("/api/admin/backups/create", headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 201
        data = res.json()
        assert "ausgabenplaner_backup_" in data["filename"]
        assert data["file_size"] > 0
        assert data["total_backups_count"] == 3

        # Check files on disk
        files = sorted(list(Path(test_folder).glob("ausgabenplaner_backup_*.db")))
        assert len(files) == 3
    finally:
        conn.close()


def test_list_download_and_delete_backup():
    client = TestClient(app)
    admin_token = get_admin_token(client)
    test_folder = "data/test_backups"

    client.patch(
        "/api/admin/backups/settings",
        json={"backup_folder": test_folder, "retention_count": 10},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    # Create a backup
    res = client.post("/api/admin/backups/create", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 201
    created = res.json()
    filename = created["filename"]

    # 1. List backups
    list_res = client.get("/api/admin/backups", headers={"Authorization": f"Bearer {admin_token}"})
    assert list_res.status_code == 200
    backups_list = list_res.json()
    assert len(backups_list) >= 1
    assert any(b["filename"] == filename for b in backups_list)

    # 2. Download backup
    dl_res = client.get(f"/api/admin/backups/download/{filename}", headers={"Authorization": f"Bearer {admin_token}"})
    assert dl_res.status_code == 200
    assert len(dl_res.content) > 0
    assert f'filename="{filename}"' in dl_res.headers.get("Content-Disposition", "")

    # Test path-traversal download 404
    dl_bad = client.get("/api/admin/backups/download/../../etc/passwd", headers={"Authorization": f"Bearer {admin_token}"})
    assert dl_bad.status_code == 404

    # 3. Delete backup
    del_res = client.delete(f"/api/admin/backups/{filename}", headers={"Authorization": f"Bearer {admin_token}"})
    assert del_res.status_code == 200

    # Verify deleted from list
    list_after = client.get("/api/admin/backups", headers={"Authorization": f"Bearer {admin_token}"}).json()
    assert not any(b["filename"] == filename for b in list_after)


def test_restore_database_backup():
    client = TestClient(app)
    admin_token = get_admin_token(client)
    test_folder = "data/test_backups"

    client.patch(
        "/api/admin/backups/settings",
        json={"backup_folder": test_folder},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    # 1. Take a snapshot of current DB
    create_res = client.post("/api/admin/backups/create", headers={"Authorization": f"Bearer {admin_token}"})
    assert create_res.status_code == 201
    snapshot_filename = create_res.json()["filename"]

    # 2. Modify database: change plan title to something modified
    conn = get_db_connection()
    try:
        conn.execute("UPDATE plans SET title = 'GEÄNDERTER PLAN TITEL'")
        conn.commit()
    finally:
        conn.close()

    # Verify plan was modified
    plan_res = client.get("/api/plans/active", headers={"Authorization": f"Bearer {admin_token}"})
    assert plan_res.status_code == 200
    assert plan_res.json()["title"] == "GEÄNDERTER PLAN TITEL"

    # 3. Restore from snapshot
    restore_res = client.post(f"/api/admin/backups/restore/{snapshot_filename}", headers={"Authorization": f"Bearer {admin_token}"})
    assert restore_res.status_code == 200
    assert restore_res.json()["success"] is True

    # 4. Verify database state is restored
    plan_after = client.get("/api/plans/active", headers={"Authorization": f"Bearer {admin_token}"})
    assert plan_after.status_code == 200
    assert plan_after.json()["title"] == "Muster-Wirtschaftsplan"

    # Non-existent restore 404
    bad_res = client.post("/api/admin/backups/restore/non_existent.db", headers={"Authorization": f"Bearer {admin_token}"})
    assert bad_res.status_code == 404


def test_non_admin_forbidden_backup_routes():
    client = TestClient(app)
    user_token = get_user_token(client)

    assert client.get("/api/admin/backups/settings", headers={"Authorization": f"Bearer {user_token}"}).status_code == 403
    assert client.patch("/api/admin/backups/settings", json={}, headers={"Authorization": f"Bearer {user_token}"}).status_code == 403
    assert client.get("/api/admin/backups", headers={"Authorization": f"Bearer {user_token}"}).status_code == 403
    assert client.post("/api/admin/backups/create", headers={"Authorization": f"Bearer {user_token}"}).status_code == 403
    assert client.get("/api/admin/backups/download/test.db", headers={"Authorization": f"Bearer {user_token}"}).status_code == 403
    assert client.post("/api/admin/backups/restore/test.db", headers={"Authorization": f"Bearer {user_token}"}).status_code == 403
    assert client.delete("/api/admin/backups/test.db", headers={"Authorization": f"Bearer {user_token}"}).status_code == 403


def test_backup_timezone_support_and_filename():
    """Verify that backup timezone detects local timezone (MEZ/MESZ) and filenames reflect local time."""
    tz = backups.get_app_timezone()
    assert tz is not None

    local_now = backups.get_local_now()
    assert local_now.tzinfo is not None

    client = TestClient(app)
    admin_token = get_admin_token(client)

    test_folder = "data/test_tz_backups"
    if os.path.exists(test_folder):
        shutil.rmtree(test_folder)

    client.patch(
        "/api/admin/backups/settings",
        json={"backup_folder": test_folder},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    create_res = client.post("/api/admin/backups/create", headers={"Authorization": f"Bearer {admin_token}"})
    assert create_res.status_code == 201
    created_data = create_res.json()
    filename = created_data["filename"]

    # Verify filename format and timestamp corresponds to local date
    local_date_str = local_now.strftime("%Y-%m-%d")
    assert f"ausgabenplaner_backup_{local_date_str}_" in filename

    # Verify created_at string
    assert created_data["created_at"].startswith(local_date_str)

    # Cleanup
    if os.path.exists(test_folder):
        shutil.rmtree(test_folder)

