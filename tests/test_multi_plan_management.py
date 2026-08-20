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


def test_multi_plan_creation_rename_and_get():
    # Login Admin
    login_resp = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {token}"}

    # 1. Create first additional plan
    p1_resp = client.post(
        "/api/plans",
        json={"title": "Musterstraße 10", "description": "Hauptgebäude"},
        headers=admin_headers,
    )
    assert p1_resp.status_code == 201
    p1 = p1_resp.json()
    assert p1["title"] == "Musterstraße 10"
    assert p1["description"] == "Hauptgebäude"
    assert p1["is_archived"] is False
    assert len(p1["versions"]) == 1

    p1_id = p1["id"]

    # 2. Rename / update plan
    update_resp = client.patch(
        f"/api/plans/{p1_id}",
        json={"title": "Musterstraße 10 (Saniert)", "description": "Wirtschaftsplan A"},
        headers=admin_headers,
    )
    assert update_resp.status_code == 200
    p1_updated = update_resp.json()
    assert p1_updated["title"] == "Musterstraße 10 (Saniert)"
    assert p1_updated["description"] == "Wirtschaftsplan A"

    # 3. Get plan by ID
    get_resp = client.get(f"/api/plans/{p1_id}", headers=admin_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == p1_id


def test_plan_duplication_deep_copy():
    login_resp = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    token = login_resp.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {token}"}

    # 1. Create a source plan
    create_resp = client.post(
        "/api/plans",
        json={"title": "Vorlage Wirtschaftsplan", "description": "Standardtemplate"},
        headers=admin_headers,
    )
    assert create_resp.status_code == 201
    src_plan = create_resp.json()
    src_id = src_plan["id"]
    src_ver_id = src_plan["active_version"]["id"]

    # 2. Add position and contribution to source plan version
    pos_resp = client.post(
        f"/api/versions/{src_ver_id}/positions",
        json={"title": "Treppenhausreinigung", "amount": 150.0, "comment": "Monatlich", "category": "Dienstleistung"},
        headers=admin_headers,
    )
    assert pos_resp.status_code == 201

    con_resp = client.post(
        f"/api/versions/{src_ver_id}/contributions",
        json={"person_name": "Eigentümer 1", "amount": 150.0, "comment": "Hausgeld"},
        headers=admin_headers,
    )
    assert con_resp.status_code == 201

    # 3. Duplicate plan
    dup_resp = client.post(
        f"/api/plans/{src_id}/duplicate",
        json={"title": "Kopie Objekt Süd"},
        headers=admin_headers,
    )
    assert dup_resp.status_code == 201
    dup_plan = dup_resp.json()
    assert dup_plan["id"] != src_id
    assert dup_plan["title"] == "Kopie Objekt Süd"
    assert dup_plan["description"] == "Standardtemplate"
    assert len(dup_plan["versions"]) >= 1

    # Verify positions and contributions were copied
    dup_ver = dup_plan["active_version"]
    assert len(dup_ver["positions"]) == 1
    assert dup_ver["positions"][0]["title"] == "Treppenhausreinigung"
    assert dup_ver["positions"][0]["amount"] == 150.0

    assert len(dup_ver["contributions"]) == 1
    assert dup_ver["contributions"][0]["person_name"] == "Eigentümer 1"
    assert dup_ver["contributions"][0]["amount"] == 150.0


def test_plan_archiving_and_reactivation():
    login_resp = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    token = login_resp.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {token}"}

    # Create plan
    plan_resp = client.post(
        "/api/plans",
        json={"title": "Altes Projekt", "description": "Abgeschlossen"},
        headers=admin_headers,
    )
    plan_id = plan_resp.json()["id"]

    # Archive plan
    arch_resp = client.patch(
        f"/api/plans/{plan_id}",
        json={"is_archived": True},
        headers=admin_headers,
    )
    assert arch_resp.status_code == 200
    assert arch_resp.json()["is_archived"] is True

    # List all plans (include_archived=False vs True)
    list_active = client.get("/api/plans?include_archived=false", headers=admin_headers).json()
    assert not any(p["id"] == plan_id for p in list_active)

    list_all = client.get("/api/plans?include_archived=true", headers=admin_headers).json()
    assert any(p["id"] == plan_id for p in list_all)

    # Reactivate plan
    reactivate_resp = client.patch(
        f"/api/plans/{plan_id}",
        json={"is_archived": False},
        headers=admin_headers,
    )
    assert reactivate_resp.status_code == 200
    assert reactivate_resp.json()["is_archived"] is False


def test_user_plan_assignments_and_access_control():
    # 1. Admin logs in
    admin_login = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"}).json()
    admin_headers = {"Authorization": f"Bearer {admin_login['access_token']}"}

    # 2. Create two distinct plans
    plan_a = client.post("/api/plans", json={"title": "Haus A", "description": "Wirtschaftsplan A"}, headers=admin_headers).json()
    plan_b = client.post("/api/plans", json={"title": "Haus B", "description": "Wirtschaftsplan B"}, headers=admin_headers).json()
    plan_a_id = plan_a["id"]
    plan_b_id = plan_b["id"]

    # 3. Create normal user assigned only to Plan A
    user_resp = client.post(
        "/api/users",
        json={
            "username": "user_a",
            "password": "secretpassword",
            "name": "Verwalter Haus A",
            "role": "user",
            "assigned_plan_ids": [plan_a_id],
        },
        headers=admin_headers,
    )
    assert user_resp.status_code == 201
    user_data = user_resp.json()
    assert user_data["assigned_plan_ids"] == [plan_a_id]

    # 4. User logs in
    user_login = client.post("/api/auth/login", json={"username": "user_a", "password": "secretpassword"}).json()
    assert user_login["user"]["assigned_plan_ids"] == [plan_a_id]
    user_headers = {"Authorization": f"Bearer {user_login['access_token']}"}

    # 5. User lists plans -> should only see Plan A
    user_plans = client.get("/api/plans", headers=user_headers).json()
    plan_ids = [p["id"] for p in user_plans]
    assert plan_a_id in plan_ids
    assert plan_b_id not in plan_ids

    # 6. User accesses Plan A -> 200 OK
    assert client.get(f"/api/plans/{plan_a_id}", headers=user_headers).status_code == 200

    # 7. User tries to access Plan B -> 403 Forbidden
    assert client.get(f"/api/plans/{plan_b_id}", headers=user_headers).status_code == 403

    # 8. User tries to view history or add positions/contributions to Plan B -> 403 Forbidden
    assert client.get(f"/api/plans/{plan_b_id}/history", headers=user_headers).status_code == 403
    ver_b_id = plan_b["active_version"]["id"]
    assert client.post(
        f"/api/versions/{ver_b_id}/positions",
        json={"title": "Test Pos", "amount": 100.0},
        headers=user_headers,
    ).status_code == 403
    assert client.post(
        f"/api/versions/{ver_b_id}/contributions",
        json={"person_name": "Test Contrib", "amount": 100.0},
        headers=user_headers,
    ).status_code == 403

    # 9. Admin updates user to also have access to Plan B
    update_user = client.patch(
        f"/api/users/{user_data['id']}",
        json={"assigned_plan_ids": [plan_a_id, plan_b_id]},
        headers=admin_headers,
    )
    assert update_user.status_code == 200
    assert sorted(update_user.json()["assigned_plan_ids"]) == sorted([plan_a_id, plan_b_id])

    # 10. User now has access to Plan B and can add positions
    assert client.get(f"/api/plans/{plan_b_id}", headers=user_headers).status_code == 200
    pos_b_resp = client.post(
        f"/api/versions/{ver_b_id}/positions",
        json={"title": "Erlaubte Position", "amount": 250.0},
        headers=user_headers,
    )
    assert pos_b_resp.status_code == 201
    pos_b_id = pos_b_resp.json()["id"]

    # Can update and delete now
    assert client.put(
        f"/api/positions/{pos_b_id}",
        json={"title": "Aktualisiert", "amount": 300.0},
        headers=user_headers,
    ).status_code == 200
    assert client.delete(f"/api/positions/{pos_b_id}", headers=user_headers).status_code == 200



def test_multi_plan_frontend_elements():
    from pathlib import Path
    static_dir = Path(__file__).resolve().parent.parent / "static"
    index_html = (static_dir / "index.html").read_text(encoding="utf-8")
    styles_css = (static_dir / "styles.css").read_text(encoding="utf-8")
    plans_js = (static_dir / "js" / "components" / "plans.js").read_text(encoding="utf-8")
    dom_js = (static_dir / "js" / "dom.js").read_text(encoding="utf-8")

    # Verify HTML elements in Settings
    assert 'id="tab-btn-plans"' in index_html
    assert 'id="tab-settings-plans"' in index_html
    assert 'id="plans-grid"' in index_html
    assert 'id="btn-open-create-plan"' in index_html
    assert 'id="modal-create-plan"' in index_html
    assert 'id="modal-edit-plan"' in index_html
    assert 'id="modal-duplicate-plan"' in index_html
    assert 'id="user-plans-assignment-container"' in index_html

    # Verify clean main dashboard header (no cluttered plan buttons on main page)
    assert 'id="btn-quick-new-plan"' not in index_html
    assert 'id="btn-quick-duplicate-plan"' not in index_html

    # Verify CSS classes
    assert ".plans-grid" in styles_css
    assert ".plan-card" in styles_css

    # Verify JS logic
    assert "loadAllPlans" in plans_js
    assert "switchPlan" in plans_js
    assert "renderPlansManagementGrid" in plans_js
    assert "renderUserPlanAssignmentCheckboxes" in plans_js
    assert "plansGrid: document.getElementById" in dom_js

