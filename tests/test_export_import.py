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


def test_export_and_import_flow():
    # Login admin
    login_resp = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Add sample position & contribution to active plan
    plan_resp = client.get("/api/plans/active", headers=headers)
    assert plan_resp.status_code == 200
    version_id = plan_resp.json()["active_version"]["id"]

    pos_resp = client.post(
        f"/api/versions/{version_id}/positions",
        json={"title": "Miete Export Test", "amount": -1000.0, "comment": "Test Comment", "category": "Wohnen"},
        headers=headers,
    )
    assert pos_resp.status_code == 201

    contrib_resp = client.post(
        f"/api/versions/{version_id}/contributions",
        json={"person_name": "Alex", "amount": 500.0, "comment": "Alex Beitrag"},
        headers=headers,
    )
    assert contrib_resp.status_code == 201

    # 1. Export data
    export_resp = client.get("/api/data/export", headers=headers)
    assert export_resp.status_code == 200
    export_data = export_resp.json()

    assert export_data["version"] == 1
    assert len(export_data["plans"]) == 1
    plan_data = export_data["plans"][0]
    assert plan_data["title"] == "Tütingstraße 22"
    assert len(plan_data["versions"]) == 1

    ver_data = plan_data["versions"][0]
    assert len(ver_data["positions"]) == 1
    assert ver_data["positions"][0]["title"] == "Miete Export Test"
    assert ver_data["positions"][0]["amount"] == -1000.0

    assert len(ver_data["contributions"]) == 1
    assert ver_data["contributions"][0]["person_name"] == "Alex"
    assert ver_data["contributions"][0]["amount"] == 500.0

    # 2. Clear database
    reset_db()
    init_db(seed=False)

    # Confirm DB has 0 positions and 0 contributions
    ver_check = client.get(f"/api/versions/{version_id}", headers=headers)
    assert ver_check.status_code == 200
    assert len(ver_check.json()["positions"]) == 0
    assert len(ver_check.json()["contributions"]) == 0

    # 3. Import data back
    import_resp = client.post("/api/data/import", json=export_data, headers=headers)
    assert import_resp.status_code == 200
    import_res = import_resp.json()
    assert import_res["success"] is True
    assert import_res["positions_imported"] == 1
    assert import_res["contributions_imported"] == 1

    # 4. Verify restored active plan data
    restored_plan = client.get("/api/plans/active", headers=headers).json()
    restored_ver = restored_plan["active_version"]
    assert len(restored_ver["positions"]) == 1
    assert restored_ver["positions"][0]["title"] == "Miete Export Test"
    assert restored_ver["positions"][0]["amount"] == -1000.0

    assert len(restored_ver["contributions"]) == 1
    assert restored_ver["contributions"][0]["person_name"] == "Alex"
    assert restored_ver["contributions"][0]["amount"] == 500.0
    assert restored_ver["totals"]["net_balance"] == -500.0
