import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import init_db, reset_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_test_db():
    reset_db()
    init_db()
    yield


def get_admin_token() -> str:
    resp = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert resp.status_code == 200
    return resp.json()["access_token"]


def test_create_user_with_granular_permissions():
    admin_token = get_admin_token()
    headers = {"Authorization": f"Bearer {admin_token}"}

    payload = {
        "username": "custom_manager",
        "name": "Custom Manager",
        "password": "manager123",
        "role": "user",
        "can_manage_plans": True,
        "can_export": True,
        "can_import": False,
        "can_manage_backups": True,
        "can_manage_users": False,
        "can_run_testsuite": True,
        "can_view_changelog": True,
        "assigned_plan_ids": [],
    }

    resp = client.post("/api/users", json=payload, headers=headers)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["username"] == "custom_manager"
    assert data["can_manage_plans"] is True
    assert data["can_export"] is True
    assert data["can_import"] is False
    assert data["can_manage_backups"] is True
    assert data["can_manage_users"] is False
    assert data["can_run_testsuite"] is True
    assert data["can_view_changelog"] is True


def test_user_login_and_me_returns_all_permissions():
    admin_token = get_admin_token()
    headers = {"Authorization": f"Bearer {admin_token}"}

    client.post(
        "/api/users",
        json={
            "username": "tester_perms",
            "name": "Perm Tester",
            "password": "pass123",
            "role": "user",
            "can_manage_plans": False,
            "can_export": False,
            "can_import": True,
            "can_manage_backups": False,
            "can_manage_users": True,
            "can_run_testsuite": False,
            "can_view_changelog": False,
        },
        headers=headers,
    )

    # Login
    login_resp = client.post("/api/auth/login", json={"username": "tester_perms", "password": "pass123"})
    assert login_resp.status_code == 200
    user_info = login_resp.json()["user"]
    token = login_resp.json()["access_token"]
    assert user_info["can_manage_plans"] is False
    assert user_info["can_export"] is False
    assert user_info["can_import"] is True
    assert user_info["can_manage_backups"] is False
    assert user_info["can_manage_users"] is True
    assert user_info["can_run_testsuite"] is False
    assert user_info["can_view_changelog"] is False

    # Get /api/auth/me
    me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["can_import"] is True
    assert me_data["can_manage_users"] is True
    assert me_data["can_export"] is False


def test_update_user_granular_permissions():
    admin_token = get_admin_token()
    headers = {"Authorization": f"Bearer {admin_token}"}

    created = client.post(
        "/api/users",
        json={
            "username": "updatable_user",
            "name": "Updatable",
            "password": "pass123",
            "role": "user",
            "can_export": True,
            "can_manage_plans": False,
        },
        headers=headers,
    ).json()

    user_id = created["id"]

    patch_resp = client.patch(
        f"/api/users/{user_id}",
        json={
            "can_manage_plans": True,
            "can_export": False,
            "can_manage_backups": True,
        },
        headers=headers,
    )
    assert patch_resp.status_code == 200
    updated = patch_resp.json()
    assert updated["can_manage_plans"] is True
    assert updated["can_export"] is False
    assert updated["can_manage_backups"] is True


def test_endpoint_rbac_enforcement_per_permission():
    admin_token = get_admin_token()
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. User with ONLY can_manage_plans = True
    client.post(
        "/api/users",
        json={
            "username": "plan_manager",
            "name": "Plan Manager",
            "password": "pass",
            "role": "user",
            "can_manage_plans": True,
            "can_export": False,
            "can_import": False,
            "can_manage_backups": False,
            "can_manage_users": False,
            "can_run_testsuite": False,
        },
        headers=headers,
    )
    token_plan = client.post("/api/auth/login", json={"username": "plan_manager", "password": "pass"}).json()["access_token"]
    h_plan = {"Authorization": f"Bearer {token_plan}"}

    # Can create plan
    create_plan_resp = client.post("/api/plans", json={"title": "Managed Plan", "description": "Desc"}, headers=h_plan)
    assert create_plan_resp.status_code == 201
    new_plan_id = create_plan_resp.json()["id"]

    # Cannot export data
    assert client.get("/api/data/export", headers=h_plan).status_code == 403
    # Cannot access backups
    assert client.get("/api/admin/backups/settings", headers=h_plan).status_code == 403
    # Cannot manage users
    assert client.get("/api/users", headers=h_plan).status_code == 403
    # Cannot run testsuite
    assert client.post("/api/admin/run-tests", headers=h_plan).status_code == 403

    # 2. User with ONLY can_manage_backups = True
    client.post(
        "/api/users",
        json={
            "username": "backup_op",
            "name": "Backup Operator",
            "password": "pass",
            "role": "user",
            "can_manage_plans": False,
            "can_manage_backups": True,
        },
        headers=headers,
    )
    token_backup = client.post("/api/auth/login", json={"username": "backup_op", "password": "pass"}).json()["access_token"]
    h_backup = {"Authorization": f"Bearer {token_backup}"}

    # Cannot create plan
    assert client.post("/api/plans", json={"title": "Denied Plan"}, headers=h_backup).status_code == 403
    # Can access backup settings
    assert client.get("/api/admin/backups/settings", headers=h_backup).status_code == 200

    # 3. User with ONLY can_manage_users = True
    client.post(
        "/api/users",
        json={
            "username": "user_admin",
            "name": "User Admin",
            "password": "pass",
            "role": "user",
            "can_manage_users": True,
        },
        headers=headers,
    )
    token_user_admin = client.post("/api/auth/login", json={"username": "user_admin", "password": "pass"}).json()["access_token"]
    h_user_admin = {"Authorization": f"Bearer {token_user_admin}"}

    # Can list users
    assert client.get("/api/users", headers=h_user_admin).status_code == 200


def test_frontend_permission_elements_present():
    """Verify that index.html contains all 7 granular permission checkmarks and JS bindings."""
    from pathlib import Path
    html_path = Path(__file__).parent.parent / "static" / "index.html"
    content = html_path.read_text(encoding="utf-8")

    assert 'id="user-permissions-group"' in content
    assert 'id="user-perm-manage-plans"' in content
    assert 'id="user-perm-export"' in content
    assert 'id="user-perm-import"' in content
    assert 'id="user-perm-manage-backups"' in content
    assert 'id="user-perm-manage-users"' in content
    assert 'id="user-perm-run-testsuite"' in content
    assert 'id="user-perm-view-changelog"' in content
