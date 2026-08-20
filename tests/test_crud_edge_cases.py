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


def test_update_delete_position_not_found():
    login_resp = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 404 on non-existent position update/delete
    assert client.put("/api/positions/9999", json={"title": "Test"}, headers=headers).status_code == 404
    assert client.delete("/api/positions/9999", headers=headers).status_code == 404


def test_update_delete_contribution_not_found():
    login_resp = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 404 on non-existent contribution update/delete
    assert client.put("/api/contributions/9999", json={"person_name": "Test"}, headers=headers).status_code == 404
    assert client.delete("/api/contributions/9999", headers=headers).status_code == 404


def test_non_admin_forbidden_routes():
    # Admin creates user 'normaluser'
    login_admin = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    admin_token = login_admin.json()["access_token"]
    client.post(
        "/api/users",
        json={"username": "normaluser", "password": "user123", "name": "Normal User", "role": "user"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    # User logs in
    login_user = client.post("/api/auth/login", json={"username": "normaluser", "password": "user123"})
    user_token = login_user.json()["access_token"]
    user_headers = {"Authorization": f"Bearer {user_token}"}

    # Attempt to list users (Forbidden)
    assert client.get("/api/users", headers=user_headers).status_code == 403

    # Attempt to create user (Forbidden)
    assert client.post("/api/users", json={"username": "hacker", "password": "123", "name": "Hacker"}, headers=user_headers).status_code == 403


def test_duplicate_user_creation_rejected():
    login_admin = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    token = login_admin.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Try creating 'admin' again
    resp = client.post("/api/users", json={"username": "admin", "password": "123", "name": "Admin2"}, headers=headers)
    assert resp.status_code == 400


from unittest.mock import patch, MagicMock


@patch("subprocess.run")
def test_run_tests_endpoint_security(mock_run):
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = "PASSED"
    mock_run.return_value.stderr = ""

    # Admin logs in
    login_admin = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    admin_token = login_admin.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Admin creates normal user
    client.post(
        "/api/users",
        json={"username": "normaluser2", "password": "user123", "name": "Normal User 2", "role": "user"},
        headers=admin_headers,
    )

    # User logs in
    login_user = client.post("/api/auth/login", json={"username": "normaluser2", "password": "user123"})
    user_token = login_user.json()["access_token"]
    user_headers = {"Authorization": f"Bearer {user_token}"}

    # Unauthenticated -> 401
    assert client.post("/api/admin/run-tests").status_code == 401

    # Non-admin -> 403
    assert client.post("/api/admin/run-tests", headers=user_headers).status_code == 403

    # Admin -> 200 with test results
    resp = client.post("/api/admin/run-tests", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "passed" in data
    assert "output" in data


@patch("subprocess.Popen")
def test_run_tests_stream_endpoint_security(mock_popen):
    mock_proc = MagicMock()
    mock_proc.stdout = ["test_auth.py . [100%]\n"]
    mock_proc.returncode = 0
    mock_popen.return_value = mock_proc

    # Admin logs in
    login_admin = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    admin_token = login_admin.json()["access_token"]

    # Unauthenticated -> 401
    assert client.get("/api/admin/run-tests-stream").status_code == 401

    # Admin -> 200 streaming response
    resp = client.get(f"/api/admin/run-tests-stream?token={admin_token}")
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers.get("content-type", "")



