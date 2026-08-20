import pytest
from fastapi.testclient import TestClient
from app.main import app, APP_VERSION
from app.database import init_db, reset_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_test_db():
    reset_db()
    init_db()
    yield


def test_app_info_endpoint():
    resp = client.get("/api/info")
    assert resp.status_code == 200
    data = resp.json()
    assert data["app_name"] == "Ausgabenplaner"
    assert data["version"] == APP_VERSION
    assert data["status"] == "healthy"


def test_plan_crud_and_deletion_flow():
    # 1. Login Admin
    login_resp = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    token = login_resp.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {token}"}

    # 2. List initial plans (should be 1)
    list_resp = client.get("/api/plans", headers=admin_headers)
    assert list_resp.status_code == 200
    plans = list_resp.json()
    assert len(plans) == 1
    first_plan_id = plans[0]["id"]

    # 3. Attempt to delete only remaining plan -> should fail with 400
    del_fail = client.delete(f"/api/plans/{first_plan_id}", headers=admin_headers)
    assert del_fail.status_code == 400
    assert "Der letzte verbleibende Plan" in del_fail.json()["detail"]

    # 4. Create a second plan
    create_resp = client.post(
        "/api/plans",
        json={"title": "Zweiter Plan (Objekt B)", "description": "Liegenschaft 2"},
        headers=admin_headers,
    )
    assert create_resp.status_code == 201
    second_plan = create_resp.json()
    second_plan_id = second_plan["id"]

    # 5. List plans now -> should be 2
    list_after = client.get("/api/plans", headers=admin_headers).json()
    assert len(list_after) == 2

    # 6. Delete second plan -> should succeed
    del_ok = client.delete(f"/api/plans/{second_plan_id}", headers=admin_headers)
    assert del_ok.status_code == 200
    assert del_ok.json()["deleted_id"] == second_plan_id

    # 7. List plans again -> 1
    list_final = client.get("/api/plans", headers=admin_headers).json()
    assert len(list_final) == 1

    # 8. Delete non-existent plan -> 404
    del_404 = client.delete("/api/plans/99999", headers=admin_headers)
    assert del_404.status_code == 404


def test_non_admin_cannot_create_or_delete_plan():
    # Admin creates normal user
    admin_login = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"}).json()
    admin_headers = {"Authorization": f"Bearer {admin_login['access_token']}"}

    client.post(
        "/api/users",
        json={"username": "user1", "password": "pw", "name": "Normal User", "role": "user"},
        headers=admin_headers,
    )

    # User logs in
    user_login = client.post("/api/auth/login", json={"username": "user1", "password": "pw"}).json()
    user_headers = {"Authorization": f"Bearer {user_login['access_token']}"}

    # Forbidden on POST /api/plans
    assert client.post("/api/plans", json={"title": "Test"}, headers=user_headers).status_code == 403

    # Forbidden on DELETE /api/plans/1
    assert client.delete("/api/plans/1", headers=user_headers).status_code == 403
