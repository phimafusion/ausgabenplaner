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


def test_create_historical_snapshot():
    login_resp = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    plan_resp = client.get("/api/plans/active", headers=headers)
    plan_id = plan_resp.json()["id"]
    version1_id = plan_resp.json()["active_version"]["id"]

    # Add positions to current version
    client.post(
        f"/api/versions/{version1_id}/positions",
        json={"title": "Strom", "amount": -87.00, "comment": "Naturstrom", "category": "Energie"},
        headers=headers,
    )
    client.post(
        f"/api/versions/{version1_id}/contributions",
        json={"person_name": "Phil", "amount": 930.00, "comment": "Zahlung Phil"},
        headers=headers,
    )

    # Create new snapshot "Stand ab 01.09.2026"
    snap_resp = client.post(
        f"/api/plans/{plan_id}/snapshots",
        json={"title": "Stand ab 01.09.2026", "effective_date": "2026-09-01", "copy_from_version_id": version1_id},
        headers=headers,
    )
    assert snap_resp.status_code == 201
    snap_data = snap_resp.json()
    assert snap_data["title"] == "Stand ab 01.09.2026"
    version2_id = snap_data["id"]

    # Modify Strom in version2 to -81.00
    pos_ver2 = client.get(f"/api/versions/{version2_id}", headers=headers).json()["positions"][0]
    update_resp = client.put(
        f"/api/positions/{pos_ver2['id']}",
        json={"title": "Strom", "amount": -81.00, "comment": "Naturstrom neu"},
        headers=headers,
    )
    assert update_resp.status_code == 200

    # Historical comparison should show Strom = -87.00 in version 1 and -81.00 in version 2
    comp_resp = client.get(f"/api/plans/{plan_id}/history-comparison", headers=headers)
    assert comp_resp.status_code == 200
    comp_data = comp_resp.json()

    assert len(comp_data["versions"]) >= 2
    strom_row = next(r for r in comp_data["rows"] if r["title"] == "Strom")
    assert strom_row["values"][str(version1_id)] == -87.00
    assert strom_row["values"][str(version2_id)] == -81.00
