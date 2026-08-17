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


def test_recreate_user_spreadsheet_dataset():
    # Login admin
    login_resp = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get active plan version
    plan_data = client.get("/api/plans/active", headers=headers).json()
    version_id = plan_data["active_version"]["id"]

    # Insert items from user's screenshot
    positions_data = [
        {"title": "Miete (Kalt + Nebenkosten) an Vermieter", "amount": -1235.00, "comment": ""},
        {"title": "Kita", "amount": -60.00, "comment": ""},
        {"title": "Strom / Naturstrom", "amount": -87.00, "comment": ""},
        {"title": "Wasser (Stadtwerke OS)", "amount": -38.00, "comment": ""},
        {"title": "eprimo (Gas)", "amount": -143.00, "comment": ""},
        {"title": "Internet / Osnatel", "amount": -40.00, "comment": "Wird an Phil überwiesen"},
        {"title": "OSBO Versicherung", "amount": -38.72, "comment": "Wird quartalsweise eingezogen (COSMOS)"},
        {"title": "OSBO Steuer", "amount": -8.50, "comment": "Wird jährlich eingezogen, (Bundeskasse Kiel)"},
        {"title": "Rundfunkgebühr", "amount": -18.36, "comment": "Wird quartalsweise eingezogen, Wird an Sabrina überwiesen"},
        {"title": "OSC Mitgliedschaft Jonti", "amount": 0.00, "comment": ""},
        {"title": "Familienhaftpflichtversicherung", "amount": -6.41, "comment": "Wird jährlich eingezogen (COSMOS)"},
        {"title": "Hausratsversicherung", "amount": -9.17, "comment": "Wird jährlich eingezogen (Docura)"},
    ]

    for idx, p in enumerate(positions_data):
        res = client.post(
            f"/api/versions/{version_id}/positions",
            json={**p, "sort_order": idx},
            headers=headers,
        )
        assert res.status_code == 201

    # Insert contributions
    contributions_data = [
        {"person_name": "Phil", "amount": 930.00, "comment": "Zahlung Phil"},
        {"person_name": "Sabrina", "amount": 800.00, "comment": "Zahlung Sabrina"},
    ]

    for idx, c in enumerate(contributions_data):
        res = client.post(
            f"/api/versions/{version_id}/contributions",
            json={**c, "sort_order": idx},
            headers=headers,
        )
        assert res.status_code == 201

    # Fetch updated version
    ver_resp = client.get(f"/api/versions/{version_id}", headers=headers)
    assert ver_resp.status_code == 200
    totals = ver_resp.json()["totals"]

    assert totals["total_expenses"] == -1684.16
    assert totals["total_contributions"] == 1730.00
    # Exact match to SUMME in user screenshot: 45,84 €!
    assert totals["net_balance"] == 45.84
    assert totals["net_balance_formatted"] == "45,84 €"
