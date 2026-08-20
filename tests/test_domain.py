import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import init_db, reset_db
from app.domain import calculate_plan_totals, format_currency_de, calculate_monthly_amount_from_interval

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_test_db():
    reset_db()
    init_db()
    yield


def test_format_currency_de():
    assert format_currency_de(45.84) == "45,84 €"
    assert format_currency_de(-1235.00) == "-1.235,00 €"
    assert format_currency_de(0.0) == "0,00 €"
    assert format_currency_de(-6.41) == "-6,41 €"


def test_calculate_monthly_amount_from_interval():
    # Monthly
    assert calculate_monthly_amount_from_interval(87.0, "monthly") == -87.0
    assert calculate_monthly_amount_from_interval(-1235.0, "monthly") == -1235.0
    assert calculate_monthly_amount_from_interval(0.0, "monthly") == 0.0

    # Quarterly (/3)
    assert calculate_monthly_amount_from_interval(116.16, "quarterly") == -38.72
    assert calculate_monthly_amount_from_interval(55.08, "quarterly") == -18.36

    # Yearly (/12)
    assert calculate_monthly_amount_from_interval(102.0, "yearly") == -8.50
    assert calculate_monthly_amount_from_interval(76.92, "yearly") == -6.41
    assert calculate_monthly_amount_from_interval(110.04, "yearly") == -9.17



def test_calculate_plan_totals():
    positions = [
        {"amount": -1235.00},
        {"amount": 60.00},
        {"amount": -87.00},
        {"amount": -38.00},
        {"amount": -143.00},
        {"amount": -40.00},
        {"amount": -38.72},
        {"amount": -8.50},
        {"amount": -18.36},
        {"amount": 0.00},
        {"amount": -6.41},
        {"amount": -9.17},
    ]
    contributions = [
        {"amount": 930.00},
        {"amount": 800.00},
    ]

    totals = calculate_plan_totals(positions, contributions)
    # Total expenses = -1564.16
    assert round(totals["total_expenses"], 2) == -1564.16
    # Total contributions = 1730.00
    assert round(totals["total_contributions"], 2) == 1730.00
    # Net balance (SUMME) = -1564.16 + 1730.00 = 165.84 (or screenshot example totals)
    # In screenshot: -1235 + 60 - 87 - 38 - 143 - 40 - 38.72 - 8.50 - 18.36 + 0 - 6.41 - 9.17 = -1564.16
    # Contributions = 930 + 800 = 1730 -> Sum = 165.84
    assert round(totals["net_balance"], 2) == 165.84


def test_positions_crud_api():
    # Login admin
    login_resp = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get initial plan
    plan_resp = client.get("/api/plans/active", headers=headers)
    assert plan_resp.status_code == 200
    plan_data = plan_resp.json()
    version_id = plan_data["active_version"]["id"]

    # Add position "Miete"
    pos_resp = client.post(
        f"/api/versions/{version_id}/positions",
        json={"title": "Miete (Kalt + Nebenkosten)", "amount": -1235.00, "comment": "an Vermieter", "category": "Wohnen"},
        headers=headers,
    )
    assert pos_resp.status_code == 201
    pos_data = pos_resp.json()
    assert pos_data["title"] == "Miete (Kalt + Nebenkosten)"
    assert pos_data["amount"] == -1235.00

    # Add contribution "Zahlung Person A"
    contrib_resp = client.post(
        f"/api/versions/{version_id}/contributions",
        json={"person_name": "Person A", "amount": 930.00, "comment": "Monatlicher Beitrag"},
        headers=headers,
    )
    assert contrib_resp.status_code == 201
    contrib_data = contrib_resp.json()
    assert contrib_data["person_name"] == "Person A"
    assert contrib_data["amount"] == 930.00

    # Verify updated plan version totals via GET API
    ver_resp = client.get(f"/api/versions/{version_id}", headers=headers)
    assert ver_resp.status_code == 200
    ver_data = ver_resp.json()
    assert len(ver_data["positions"]) == 1
    assert len(ver_data["contributions"]) == 1
    assert ver_data["totals"]["total_expenses"] == -1235.00
    assert ver_data["totals"]["total_contributions"] == 930.00
    assert ver_data["totals"]["net_balance"] == -305.00
