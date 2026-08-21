import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import init_db, reset_db


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    monkeypatch.setenv("TESTING", "1")
    reset_db()
    init_db(seed=False)


def get_auth_token(client: TestClient, username: str = "admin", password: str = "admin123") -> str:
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200
    return res.json()["access_token"]


def test_save_version_as_new_historical_version():
    client = TestClient(app)
    token = get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    plan_res = client.get("/api/plans/active", headers=headers)
    assert plan_res.status_code == 200
    plan = plan_res.json()
    plan_id = plan["id"]
    initial_version_id = plan["active_version"]["id"]

    # History before save
    hist_before = client.get(f"/api/plans/{plan_id}/history", headers=headers).json()
    initial_count = len(hist_before)

    # Save as new version (update_current = False)
    payload = {
        "title": "Neuer Stand 2026",
        "effective_date": "2026-11-01",
        "update_current": False,
        "positions": [
            {"title": "Miete neu", "amount": -1200.0, "category": "Wohnen"},
            {"title": "Internet", "amount": -45.0, "category": "Medien & Kommunikation"},
        ],
        "contributions": [
            {"person_name": "Alice", "amount": 622.5},
            {"person_name": "Bob", "amount": 622.5},
        ],
    }

    res_save = client.post(f"/api/plans/{plan_id}/save-version", json=payload, headers=headers)
    assert res_save.status_code == 201
    new_ver = res_save.json()
    assert new_ver["id"] != initial_version_id
    assert new_ver["title"] == "Neuer Stand 2026"
    assert len(new_ver["positions"]) == 2
    assert len(new_ver["contributions"]) == 2

    # History count should increase by 1
    hist_after = client.get(f"/api/plans/{plan_id}/history", headers=headers).json()
    assert len(hist_after) == initial_count + 1


def test_update_existing_version_in_place():
    client = TestClient(app)
    token = get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    plan_res = client.get("/api/plans/active", headers=headers)
    assert plan_res.status_code == 200
    plan = plan_res.json()
    plan_id = plan["id"]
    current_version_id = plan["active_version"]["id"]

    # History before in-place update
    hist_before = client.get(f"/api/plans/{plan_id}/history", headers=headers).json()
    count_before = len(hist_before)

    # In-place update
    payload = {
        "title": "Aktueller Stand (Direkt korrigiert)",
        "effective_date": "2026-10-15",
        "update_current": True,
        "version_id": current_version_id,
        "positions": [
            {"title": "Kaltmiete korrigiert", "amount": -1150.0, "category": "Wohnen"},
            {"title": "Strom & Gas", "amount": -180.0, "category": "Energie & Nebenkosten"},
            {"title": "GEZ", "amount": -18.36, "category": "Medien & Kommunikation"},
        ],
        "contributions": [
            {"person_name": "Phil", "amount": 800.0},
            {"person_name": "Partner", "amount": 548.36},
        ],
    }

    res_save = client.post(f"/api/plans/{plan_id}/save-version", json=payload, headers=headers)
    assert res_save.status_code == 200
    saved_ver = res_save.json()

    # Verify ID did NOT change
    assert saved_ver["id"] == current_version_id
    assert saved_ver["title"] == "Aktueller Stand (Direkt korrigiert)"
    assert saved_ver["effective_date"] == "2026-10-15"
    assert len(saved_ver["positions"]) == 3
    assert len(saved_ver["contributions"]) == 2

    # Verify history count did NOT increase
    hist_after = client.get(f"/api/plans/{plan_id}/history", headers=headers).json()
    assert len(hist_after) == count_before

    # Verify fetching version directly returns updated positions
    ver_fetched = client.get(f"/api/versions/{current_version_id}", headers=headers).json()
    pos_titles = [p["title"] for p in ver_fetched["positions"]]
    assert "Kaltmiete korrigiert" in pos_titles
    assert "Strom & Gas" in pos_titles
    assert "GEZ" in pos_titles


def test_update_version_in_place_invalid_version_fails():
    client = TestClient(app)
    token = get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    plan_res = client.get("/api/plans/active", headers=headers)
    plan_id = plan_res.json()["id"]

    payload = {
        "title": "Ungültig",
        "update_current": True,
        "version_id": 999999,  # Non-existent version
        "positions": [],
        "contributions": [],
    }

    res = client.post(f"/api/plans/{plan_id}/save-version", json=payload, headers=headers)
    assert res.status_code == 404
