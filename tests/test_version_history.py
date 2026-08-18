import pytest
from app import crud, database


def test_save_new_version_workflow(client, auth_headers):
    # 1. Fetch initial active plan
    resp = client.get("/api/plans/active", headers=auth_headers)
    assert resp.status_code == 200
    plan = resp.json()
    plan_id = plan["id"]
    initial_ver = plan["active_version"]
    initial_ver_id = initial_ver["id"]
    initial_positions_count = len(initial_ver["positions"])
    initial_contributions_count = len(initial_ver["contributions"])

    # 2. Save a new version with modified and added positions
    new_positions = [
        {"title": "Miete (Kalt + NK)", "amount": -1250.00, "comment": "Mieterhöhung", "category": "Wohnen", "sort_order": 0},
        {"title": "Strom", "amount": -90.00, "comment": "Neuer Tarif", "category": "Energie", "sort_order": 1},
        {"title": "Neuer Streamingdienst", "amount": -15.00, "comment": "Monatlich", "category": "Freizeit", "sort_order": 2},
    ]
    new_contributions = [
        {"person_name": "Phil", "amount": 950.00, "comment": "Angepasst", "sort_order": 0},
        {"person_name": "Sabrina", "amount": 820.00, "comment": "Angepasst", "sort_order": 1},
    ]

    save_payload = {
        "title": "Stand ab 01.10.2026",
        "effective_date": "2026-10-01",
        "positions": new_positions,
        "contributions": new_contributions,
    }

    save_resp = client.post(f"/api/plans/{plan_id}/save-version", json=save_payload, headers=auth_headers)
    assert save_resp.status_code == 201
    new_ver = save_resp.json()

    assert new_ver["title"] == "Stand ab 01.10.2026"
    assert new_ver["effective_date"] == "2026-10-01"
    assert new_ver["is_active"] == 1
    assert len(new_ver["positions"]) == 3
    assert len(new_ver["contributions"]) == 2
    # Verify calculated totals
    assert new_ver["totals"]["total_expenses"] == -1355.00
    assert new_ver["totals"]["total_contributions"] == 1770.00
    assert new_ver["totals"]["net_balance"] == 415.00

    # 3. Verify that old version is STILL intact and archived in the database
    old_ver_resp = client.get(f"/api/versions/{initial_ver_id}", headers=auth_headers)
    assert old_ver_resp.status_code == 200
    archived_ver = old_ver_resp.json()
    assert archived_ver["is_active"] == 0
    assert len(archived_ver["positions"]) == initial_positions_count
    assert len(archived_ver["contributions"]) == initial_contributions_count

    # 4. Fetch history list
    hist_resp = client.get(f"/api/plans/{plan_id}/history", headers=auth_headers)
    assert hist_resp.status_code == 200
    history = hist_resp.json()
    assert len(history) >= 2
    # Newest version is first
    assert history[0]["id"] == new_ver["id"]
    assert history[0]["is_active"] == 1
    assert history[0]["positions_count"] == 3
    assert history[0]["contributions_count"] == 2
    assert history[0]["totals"]["net_balance"] == 415.00

    # 5. Check history comparison matrix
    comp_resp = client.get(f"/api/plans/{plan_id}/history-comparison", headers=auth_headers)
    assert comp_resp.status_code == 200
    comp_data = comp_resp.json()
    assert len(comp_data["versions"]) >= 2
    # Verify both version IDs are present in matrix totals
    assert str(initial_ver_id) in comp_data["totals"]
    assert str(new_ver["id"]) in comp_data["totals"]


def test_activate_past_version(client, auth_headers):
    # Fetch active plan
    resp = client.get("/api/plans/active", headers=auth_headers)
    plan = resp.json()
    plan_id = plan["id"]

    # Create 2 versions
    v1_payload = {
        "title": "Version 1",
        "positions": [{"title": "Posten 1", "amount": -100.0, "sort_order": 0}],
        "contributions": [{"person_name": "User 1", "amount": 100.0, "sort_order": 0}],
    }
    v1_resp = client.post(f"/api/plans/{plan_id}/save-version", json=v1_payload, headers=auth_headers)
    v1_id = v1_resp.json()["id"]

    v2_payload = {
        "title": "Version 2",
        "positions": [{"title": "Posten 2", "amount": -200.0, "sort_order": 0}],
        "contributions": [{"person_name": "User 2", "amount": 200.0, "sort_order": 0}],
    }
    v2_resp = client.post(f"/api/plans/{plan_id}/save-version", json=v2_payload, headers=auth_headers)
    v2_id = v2_resp.json()["id"]

    # Currently v2 is active
    active_plan = client.get("/api/plans/active", headers=auth_headers).json()
    assert active_plan["active_version"]["id"] == v2_id

    # Re-activate v1
    act_resp = client.post(f"/api/versions/{v1_id}/activate", headers=auth_headers)
    assert act_resp.status_code == 200
    assert act_resp.json()["is_active"] == 1

    # Check active plan is now v1
    active_plan_after = client.get("/api/plans/active", headers=auth_headers).json()
    assert active_plan_after["active_version"]["id"] == v1_id


def test_update_and_delete_historical_version(client, auth_headers):
    resp = client.get("/api/plans/active", headers=auth_headers)
    plan_id = resp.json()["id"]

    # Save a version
    v_payload = {
        "title": "Version Original",
        "effective_date": "2026-01-01",
        "positions": [{"title": "Test", "amount": -50.0, "sort_order": 0}],
        "contributions": [{"person_name": "Phil", "amount": 50.0, "sort_order": 0}],
    }
    v_resp = client.post(f"/api/plans/{plan_id}/save-version", json=v_payload, headers=auth_headers)
    v_id = v_resp.json()["id"]

    # Update metadata (unlocked state)
    patch_resp = client.patch(f"/api/versions/{v_id}", json={"title": "Version Korrigiert", "effective_date": "2026-02-01"}, headers=auth_headers)
    assert patch_resp.status_code == 200
    assert patch_resp.json()["title"] == "Version Korrigiert"
    assert patch_resp.json()["effective_date"] == "2026-02-01"

    # Delete version
    del_resp = client.delete(f"/api/versions/{v_id}", headers=auth_headers)
    assert del_resp.status_code == 200

    # Verify deleted
    get_resp = client.get(f"/api/versions/{v_id}", headers=auth_headers)
    assert get_resp.status_code == 404


def test_delete_active_version_promotes_fallback(client, auth_headers):
    # Fetch active plan
    resp = client.get("/api/plans/active", headers=auth_headers)
    plan_id = resp.json()["id"]

    # Create version 1
    v1_resp = client.post(
        f"/api/plans/{plan_id}/save-version",
        json={
            "title": "Version Alpha",
            "positions": [{"title": "Posten A", "amount": -10.0, "sort_order": 0}],
            "contributions": [{"person_name": "Phil", "amount": 10.0, "sort_order": 0}],
        },
        headers=auth_headers,
    )
    v1_id = v1_resp.json()["id"]

    # Create version 2 (will be active)
    v2_resp = client.post(
        f"/api/plans/{plan_id}/save-version",
        json={
            "title": "Version Beta",
            "positions": [{"title": "Posten B", "amount": -20.0, "sort_order": 0}],
            "contributions": [{"person_name": "Phil", "amount": 20.0, "sort_order": 0}],
        },
        headers=auth_headers,
    )
    v2_id = v2_resp.json()["id"]

    # Verify v2 is currently active
    active_resp = client.get("/api/plans/active", headers=auth_headers).json()
    assert active_resp["active_version"]["id"] == v2_id

    # Delete v2 (the active one)
    del_resp = client.delete(f"/api/versions/{v2_id}", headers=auth_headers)
    assert del_resp.status_code == 200

    # Verify active plan now automatically switched to latest remaining version (v1_id)
    active_after = client.get("/api/plans/active", headers=auth_headers).json()
    assert active_after["active_version"]["id"] == v1_id


def test_cannot_delete_only_remaining_version(client, auth_headers):
    resp = client.get("/api/plans/active", headers=auth_headers)
    plan_id = resp.json()["id"]

    # Get history and delete all versions except one
    hist_resp = client.get(f"/api/plans/{plan_id}/history", headers=auth_headers)
    versions = hist_resp.json()

    for v in versions[1:]:
        client.delete(f"/api/versions/{v['id']}", headers=auth_headers)

    # Now exactly 1 version remains
    remaining_ver_id = versions[0]["id"]
    last_del_resp = client.delete(f"/api/versions/{remaining_ver_id}", headers=auth_headers)
    assert last_del_resp.status_code == 400
    assert "Der letzte verbleibende Stand" in last_del_resp.json()["detail"]

