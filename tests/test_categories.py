import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db_connection, init_db, reset_db


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    monkeypatch.setenv("TESTING", "1")
    reset_db()
    init_db(seed=False)


def get_auth_token(client: TestClient, username: str = "admin", password: str = "admin123") -> str:
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200
    return res.json()["access_token"]


def test_list_seeded_default_categories():
    client = TestClient(app)
    token = get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/categories", headers=headers)
    assert res.status_code == 200
    categories = res.json()
    assert len(categories) >= 9
    names = [c["name"] for c in categories]
    assert "Wohnen" in names
    assert "Energie & Nebenkosten" in names
    assert "Versicherung" in names
    assert "Instandhaltung" in names
    assert "Rücklagen & Sparen" in names
    assert "Medien & Kommunikation" in names
    assert "Kind" in names
    assert "Freizeit" in names
    assert "Allgemein" in names


def test_create_update_and_delete_custom_category():
    client = TestClient(app)
    token = get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create custom category
    res = client.post(
        "/api/categories",
        json={"name": "Mobilität & Kfz", "color": "#0ea5e9", "icon": "🚗", "sort_order": 10},
        headers=headers,
    )
    assert res.status_code == 201
    cat = res.json()
    cat_id = cat["id"]
    assert cat["name"] == "Mobilität & Kfz"
    assert cat["color"] == "#0ea5e9"
    assert cat["icon"] == "🚗"
    assert cat["is_default"] is False

    # 2. Duplicate name rejection
    res_dup = client.post(
        "/api/categories",
        json={"name": "Mobilität & Kfz", "color": "#0ea5e9", "icon": "🚗"},
        headers=headers,
    )
    assert res_dup.status_code == 400

    # 3. Update category
    res_up = client.patch(
        f"/api/categories/{cat_id}",
        json={"name": "Fahrzeuge & Mobilität", "icon": "🏎️"},
        headers=headers,
    )
    assert res_up.status_code == 200
    up_cat = res_up.json()
    assert up_cat["name"] == "Fahrzeuge & Mobilität"
    assert up_cat["icon"] == "🏎️"

    # 4. Delete custom category
    res_del = client.delete(f"/api/categories/{cat_id}", headers=headers)
    assert res_del.status_code == 200


def test_cannot_delete_default_category():
    client = TestClient(app)
    token = get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # Find a default category
    res = client.get("/api/categories", headers=headers)
    assert res.status_code == 200
    default_cat = next(c for c in res.json() if c["is_default"])

    res_del = client.delete(f"/api/categories/{default_cat['id']}", headers=headers)
    assert res_del.status_code == 400
    assert "Standard-Kategorien können nicht gelöscht werden" in res_del.json()["detail"]


def test_category_rbac_permissions():
    client = TestClient(app)
    admin_token = get_auth_token(client)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Create a user without can_manage_categories
    res_u1 = client.post(
        "/api/users",
        json={
            "username": "viewer",
            "password": "password123",
            "name": "Viewer User",
            "role": "user",
            "can_manage_categories": False,
        },
        headers=admin_headers,
    )
    assert res_u1.status_code == 201

    # 2. Create a user with can_manage_categories
    res_u2 = client.post(
        "/api/users",
        json={
            "username": "category_manager",
            "password": "password123",
            "name": "Category Manager",
            "role": "user",
            "can_manage_categories": True,
        },
        headers=admin_headers,
    )
    assert res_u2.status_code == 201

    viewer_token = get_auth_token(client, "viewer", "password123")
    viewer_headers = {"Authorization": f"Bearer {viewer_token}"}

    mgr_token = get_auth_token(client, "category_manager", "password123")
    mgr_headers = {"Authorization": f"Bearer {mgr_token}"}

    # Viewer can read categories
    res_get = client.get("/api/categories", headers=viewer_headers)
    assert res_get.status_code == 200

    # Viewer cannot create categories (403 Forbidden)
    res_create_denied = client.post(
        "/api/categories",
        json={"name": "Haustiere", "color": "#f43f5e", "icon": "🐱"},
        headers=viewer_headers,
    )
    assert res_create_denied.status_code == 403

    # Manager can create categories (201 Created)
    res_create_ok = client.post(
        "/api/categories",
        json={"name": "Haustiere", "color": "#f43f5e", "icon": "🐱"},
        headers=mgr_headers,
    )
    assert res_create_ok.status_code == 201
    created_id = res_create_ok.json()["id"]

    # Manager can edit and delete
    res_edit_ok = client.patch(
        f"/api/categories/{created_id}",
        json={"name": "Haustiere & Tierarzt"},
        headers=mgr_headers,
    )
    assert res_edit_ok.status_code == 200

    res_del_ok = client.delete(f"/api/categories/{created_id}", headers=mgr_headers)
    assert res_del_ok.status_code == 200


def test_position_category_migration_on_category_rename_and_delete():
    client = TestClient(app)
    token = get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # Create category
    res_cat = client.post(
        "/api/categories",
        json={"name": "Streaming", "color": "#ec4899", "icon": "🎬"},
        headers=headers,
    )
    assert res_cat.status_code == 201
    cat_id = res_cat.json()["id"]

    # Get active version
    plan_res = client.get("/api/plans/active", headers=headers)
    assert plan_res.status_code == 200
    version_id = plan_res.json()["active_version"]["id"]

    # Add position with category 'Streaming'
    pos_res = client.post(
        f"/api/versions/{version_id}/positions",
        json={"title": "Netflix", "amount": -17.99, "category": "Streaming"},
        headers=headers,
    )
    assert pos_res.status_code == 201
    pos_id = pos_res.json()["id"]

    # Rename category
    client.patch(
        f"/api/categories/{cat_id}",
        json={"name": "Streaming & Abos"},
        headers=headers,
    )

    # Position category should now be 'Streaming & Abos'
    ver_after_rename = client.get(f"/api/versions/{version_id}", headers=headers).json()
    pos = next(p for p in ver_after_rename["positions"] if p["id"] == pos_id)
    assert pos["category"] == "Streaming & Abos"

    # Delete category
    client.delete(f"/api/categories/{cat_id}", headers=headers)

    # Position category should now fallback to 'Allgemein'
    ver_after_del = client.get(f"/api/versions/{version_id}", headers=headers).json()
    pos_del = next(p for p in ver_after_del["positions"] if p["id"] == pos_id)
    assert pos_del["category"] == "Allgemein"
