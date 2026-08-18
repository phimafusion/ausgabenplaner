import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db, init_db, reset_db
from app.auth import verify_password, get_password_hash, create_access_token, decode_access_token

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_test_db():
    reset_db()
    init_db()
    yield


def test_password_hashing():
    password = "secretpassword"
    hashed = get_password_hash(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False


def test_jwt_token():
    token = create_access_token({"sub": "admin", "role": "admin"})
    payload = decode_access_token(token)
    assert payload is not None
    assert payload.get("sub") == "admin"
    assert payload.get("role") == "admin"


def test_default_admin_created():
    response = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "admin"
    assert data["user"]["role"] == "admin"


def test_login_invalid_password():
    response = client.post("/api/auth/login", json={"username": "admin", "password": "wrongpassword"})
    assert response.status_code == 401
    assert "error" in response.json() or "detail" in response.json()


def test_get_current_user_profile():
    # First login to get token
    login_resp = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    token = login_resp.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    me_resp = client.get("/api/auth/me", headers=headers)
    assert me_resp.status_code == 200
    user_data = me_resp.json()
    assert user_data["username"] == "admin"
    assert user_data["role"] == "admin"


def test_admin_creates_new_user():
    # Admin logs in
    login_resp = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create new user 'sabrina'
    create_resp = client.post(
        "/api/users",
        json={"username": "sabrina", "password": "password123", "name": "Sabrina", "role": "user"},
        headers=headers,
    )
    assert create_resp.status_code == 201
    user_data = create_resp.json()
    assert user_data["username"] == "sabrina"

    # Verify new user can login
    sabrina_login = client.post("/api/auth/login", json={"username": "sabrina", "password": "password123"})
    assert sabrina_login.status_code == 200


def test_user_export_permissions_and_editing():
    # Admin logs in
    admin_login = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"}).json()
    admin_headers = {"Authorization": f"Bearer {admin_login['access_token']}"}

    # 1. Admin creates user 'sabrina' with can_export = False
    create_resp = client.post(
        "/api/users",
        json={"username": "sabrina", "password": "password123", "name": "Sabrina", "role": "user", "can_export": False},
        headers=admin_headers,
    )
    assert create_resp.status_code == 201
    sabrina_data = create_resp.json()
    assert sabrina_data["can_export"] is False
    sabrina_id = sabrina_data["id"]

    # 2. Sabrina logs in
    sabrina_login = client.post("/api/auth/login", json={"username": "sabrina", "password": "password123"}).json()
    assert sabrina_login["user"]["can_export"] is False
    sabrina_headers = {"Authorization": f"Bearer {sabrina_login['access_token']}"}

    # 3. Sabrina tries to export data (JSON & XLSX) -> 403 Forbidden
    export_forbidden = client.get("/api/data/export", headers=sabrina_headers)
    assert export_forbidden.status_code == 403
    assert "Exportieren" in export_forbidden.json()["detail"]

    export_xlsx_forbidden = client.get("/api/data/export-xlsx", headers=sabrina_headers)
    assert export_xlsx_forbidden.status_code == 403

    # 4. Admin edits user Sabrina: grant export permission, update name and new password
    edit_resp = client.patch(
        f"/api/users/{sabrina_id}",
        json={"name": "Sabrina M.", "role": "user", "can_export": True, "password": "newpassword456"},
        headers=admin_headers,
    )
    assert edit_resp.status_code == 200
    updated = edit_resp.json()
    assert updated["name"] == "Sabrina M."
    assert updated["can_export"] is True

    # 5. Sabrina logs in with new password
    new_login = client.post("/api/auth/login", json={"username": "sabrina", "password": "newpassword456"}).json()
    assert new_login["user"]["can_export"] is True
    new_sabrina_headers = {"Authorization": f"Bearer {new_login['access_token']}"}

    # 6. Now Sabrina can successfully export (JSON & XLSX)
    export_allowed = client.get("/api/data/export", headers=new_sabrina_headers)
    assert export_allowed.status_code == 200
    assert "plans" in export_allowed.json()

    export_xlsx_allowed = client.get("/api/data/export-xlsx", headers=new_sabrina_headers)
    assert export_xlsx_allowed.status_code == 200
    assert len(export_xlsx_allowed.content) > 0


    # 7. Admin deletes user Sabrina
    del_resp = client.delete(f"/api/users/{sabrina_id}", headers=admin_headers)
    assert del_resp.status_code == 200

    # 8. Admin cannot delete own account
    admin_id = admin_login["user"]["id"]
    self_del = client.delete(f"/api/users/{admin_id}", headers=admin_headers)
    assert self_del.status_code == 400

