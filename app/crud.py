import datetime
import sqlite3
from typing import List, Dict, Any, Optional
from app.domain import calculate_plan_totals, format_currency_de


def get_version_details(conn: sqlite3.Connection, version_id: int) -> Optional[Dict[str, Any]]:
    ver_row = conn.execute("SELECT * FROM versions WHERE id = ?", (version_id,)).fetchone()
    if not ver_row:
        return None

    ver = dict(ver_row)

    # Fetch positions
    pos_rows = conn.execute(
        "SELECT * FROM positions WHERE version_id = ? ORDER BY sort_order ASC, id ASC", (version_id,)
    ).fetchall()
    positions = []
    for r in pos_rows:
        p = dict(r)
        p["amount_formatted"] = format_currency_de(p["amount"])
        positions.append(p)

    # Fetch contributions
    contrib_rows = conn.execute(
        "SELECT * FROM contributions WHERE version_id = ? ORDER BY sort_order ASC, id ASC", (version_id,)
    ).fetchall()
    contributions = []
    for r in contrib_rows:
        c = dict(r)
        c["amount_formatted"] = format_currency_de(c["amount"])
        contributions.append(c)

    totals = calculate_plan_totals(positions, contributions)
    ver["positions"] = positions
    ver["contributions"] = contributions
    ver["totals"] = totals
    return ver


def get_active_plan(conn: sqlite3.Connection) -> Optional[Dict[str, Any]]:
    plan_row = conn.execute("SELECT * FROM plans ORDER BY id ASC LIMIT 1").fetchone()
    if not plan_row:
        return None

    plan = dict(plan_row)
    plan_id = plan["id"]

    ver_rows = conn.execute("SELECT id, title, effective_date, is_active, created_at FROM versions WHERE plan_id = ? ORDER BY id DESC", (plan_id,)).fetchall()
    versions = [dict(v) for v in ver_rows]
    plan["versions"] = versions

    # Active version is either marked active or newest
    active_ver_row = conn.execute("SELECT id FROM versions WHERE plan_id = ? AND is_active = 1 LIMIT 1", (plan_id,)).fetchone()
    if active_ver_row:
        plan["active_version"] = get_version_details(conn, active_ver_row["id"])
    elif versions:
        plan["active_version"] = get_version_details(conn, versions[0]["id"])
    else:
        plan["active_version"] = None

    return plan


def create_position(conn: sqlite3.Connection, version_id: int, title: str, amount: float, comment: Optional[str], category: Optional[str], sort_order: int = 0) -> Dict[str, Any]:
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO positions (version_id, title, amount, comment, category, sort_order) VALUES (?, ?, ?, ?, ?, ?)",
        (version_id, title, amount, comment, category, sort_order),
    )
    conn.commit()
    pos_id = cursor.lastrowid
    row = conn.execute("SELECT * FROM positions WHERE id = ?", (pos_id,)).fetchone()
    res = dict(row)
    res["amount_formatted"] = format_currency_de(res["amount"])
    return res


def update_position(conn: sqlite3.Connection, position_id: int, title: Optional[str] = None, amount: Optional[float] = None, comment: Optional[str] = None, category: Optional[str] = None, sort_order: Optional[int] = None) -> Optional[Dict[str, Any]]:
    existing = conn.execute("SELECT * FROM positions WHERE id = ?", (position_id,)).fetchone()
    if not existing:
        return None

    current = dict(existing)
    new_title = title if title is not None else current["title"]
    new_amount = amount if amount is not None else current["amount"]
    new_comment = comment if comment is not None else current["comment"]
    new_category = category if category is not None else current["category"]
    new_sort = sort_order if sort_order is not None else current["sort_order"]

    conn.execute(
        "UPDATE positions SET title = ?, amount = ?, comment = ?, category = ?, sort_order = ? WHERE id = ?",
        (new_title, new_amount, new_comment, new_category, new_sort, position_id),
    )
    conn.commit()

    updated = conn.execute("SELECT * FROM positions WHERE id = ?", (position_id,)).fetchone()
    res = dict(updated)
    res["amount_formatted"] = format_currency_de(res["amount"])
    return res


def delete_position(conn: sqlite3.Connection, position_id: int) -> bool:
    cursor = conn.cursor()
    cursor.execute("DELETE FROM positions WHERE id = ?", (position_id,))
    conn.commit()
    return cursor.rowcount > 0


def create_contribution(conn: sqlite3.Connection, version_id: int, person_name: str, amount: float, comment: Optional[str], sort_order: int = 0) -> Dict[str, Any]:
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO contributions (version_id, person_name, amount, comment, sort_order) VALUES (?, ?, ?, ?, ?)",
        (version_id, person_name, amount, comment, sort_order),
    )
    conn.commit()
    c_id = cursor.lastrowid
    row = conn.execute("SELECT * FROM contributions WHERE id = ?", (c_id,)).fetchone()
    res = dict(row)
    res["amount_formatted"] = format_currency_de(res["amount"])
    return res


def update_contribution(conn: sqlite3.Connection, contribution_id: int, person_name: Optional[str] = None, amount: Optional[float] = None, comment: Optional[str] = None, sort_order: Optional[int] = None) -> Optional[Dict[str, Any]]:
    existing = conn.execute("SELECT * FROM contributions WHERE id = ?", (contribution_id,)).fetchone()
    if not existing:
        return None

    current = dict(existing)
    new_person = person_name if person_name is not None else current["person_name"]
    new_amount = amount if amount is not None else current["amount"]
    new_comment = comment if comment is not None else current["comment"]
    new_sort = sort_order if sort_order is not None else current["sort_order"]

    conn.execute(
        "UPDATE contributions SET person_name = ?, amount = ?, comment = ?, sort_order = ? WHERE id = ?",
        (new_person, new_amount, new_comment, new_sort, contribution_id),
    )
    conn.commit()

    updated = conn.execute("SELECT * FROM contributions WHERE id = ?", (contribution_id,)).fetchone()
    res = dict(updated)
    res["amount_formatted"] = format_currency_de(res["amount"])
    return res


def delete_contribution(conn: sqlite3.Connection, contribution_id: int) -> bool:
    cursor = conn.cursor()
    cursor.execute("DELETE FROM contributions WHERE id = ?", (contribution_id,))
    conn.commit()
    return cursor.rowcount > 0


def create_version_snapshot(conn: sqlite3.Connection, plan_id: int, title: str, effective_date: Optional[str], copy_from_version_id: Optional[int] = None) -> Dict[str, Any]:
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO versions (plan_id, title, effective_date, is_active) VALUES (?, ?, ?, 1)",
        (plan_id, title, effective_date),
    )
    new_ver_id = cursor.lastrowid

    # If copying from an existing version, duplicate positions & contributions
    if copy_from_version_id:
        positions = conn.execute("SELECT title, amount, comment, category, sort_order FROM positions WHERE version_id = ?", (copy_from_version_id,)).fetchall()
        for p in positions:
            cursor.execute(
                "INSERT INTO positions (version_id, title, amount, comment, category, sort_order) VALUES (?, ?, ?, ?, ?, ?)",
                (new_ver_id, p["title"], p["amount"], p["comment"], p["category"], p["sort_order"]),
            )

        contributions = conn.execute("SELECT person_name, amount, comment, sort_order FROM contributions WHERE version_id = ?", (copy_from_version_id,)).fetchall()
        for c in contributions:
            cursor.execute(
                "INSERT INTO contributions (version_id, person_name, amount, comment, sort_order) VALUES (?, ?, ?, ?, ?)",
                (new_ver_id, c["person_name"], c["amount"], c["comment"], c["sort_order"]),
            )

    conn.commit()
    return get_version_details(conn, new_ver_id)


def get_history_comparison(conn: sqlite3.Connection, plan_id: int) -> Dict[str, Any]:
    ver_rows = conn.execute(
        "SELECT id, title, effective_date, created_at FROM versions WHERE plan_id = ? ORDER BY id ASC",
        (plan_id,),
    ).fetchall()

    versions = [dict(v) for v in ver_rows]
    version_ids = [v["id"] for v in versions]

    # Collect all positions across versions
    positions_map: Dict[str, Dict[str, Any]] = {}  # title -> { category, comment, values: {v_id: amount} }
    # Collect all contributions across versions
    contributions_map: Dict[str, Dict[str, Any]] = {}  # person_name -> { comment, values: {v_id: amount} }

    totals_by_version: Dict[str, Dict[str, Any]] = {}

    for v in versions:
        v_id = v["id"]
        v_details = get_version_details(conn, v_id)
        totals_by_version[str(v_id)] = v_details["totals"]

        for pos in v_details["positions"]:
            title = pos["title"]
            if title not in positions_map:
                positions_map[title] = {
                    "title": title,
                    "category": pos.get("category"),
                    "comment": pos.get("comment"),
                    "values": {},
                    "formatted_values": {},
                }
            positions_map[title]["values"][str(v_id)] = pos["amount"]
            positions_map[title]["formatted_values"][str(v_id)] = pos["amount_formatted"]

        for c in v_details["contributions"]:
            person = c["person_name"]
            if person not in contributions_map:
                contributions_map[person] = {
                    "title": f"Zahlung {person}",
                    "comment": c.get("comment"),
                    "values": {},
                    "formatted_values": {},
                }
            contributions_map[person]["values"][str(v_id)] = c["amount"]
            contributions_map[person]["formatted_values"][str(v_id)] = c["amount_formatted"]

    return {
        "versions": versions,
        "rows": list(positions_map.values()),
        "contributions_rows": list(contributions_map.values()),
        "totals": totals_by_version,
    }


def export_full_data(conn: sqlite3.Connection) -> Dict[str, Any]:
    plan_rows = conn.execute("SELECT * FROM plans ORDER BY id ASC").fetchall()
    plans = []

    for p in plan_rows:
        p_dict = dict(p)
        plan_id = p_dict["id"]

        ver_rows = conn.execute("SELECT * FROM versions WHERE plan_id = ? ORDER BY id ASC", (plan_id,)).fetchall()
        versions = []

        for v in ver_rows:
            v_dict = dict(v)
            v_id = v_dict["id"]

            pos_rows = conn.execute(
                "SELECT title, amount, comment, category, sort_order FROM positions WHERE version_id = ? ORDER BY sort_order ASC, id ASC",
                (v_id,),
            ).fetchall()
            positions = [dict(pos) for pos in pos_rows]

            contrib_rows = conn.execute(
                "SELECT person_name, amount, comment, sort_order FROM contributions WHERE version_id = ? ORDER BY sort_order ASC, id ASC",
                (v_id,),
            ).fetchall()
            contributions = [dict(c) for c in contrib_rows]

            versions.append(
                {
                    "title": v_dict["title"],
                    "effective_date": v_dict["effective_date"],
                    "is_active": v_dict["is_active"],
                    "positions": positions,
                    "contributions": contributions,
                }
            )

        plans.append(
            {
                "title": p_dict["title"],
                "description": p_dict["description"],
                "versions": versions,
            }
        )

    return {
        "version": 1,
        "exported_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "plans": plans,
    }


def import_full_data(conn: sqlite3.Connection, data: Dict[str, Any], overwrite: bool = True) -> Dict[str, Any]:
    cursor = conn.cursor()

    if overwrite:
        cursor.execute("DELETE FROM contributions;")
        cursor.execute("DELETE FROM positions;")
        cursor.execute("DELETE FROM versions;")
        cursor.execute("DELETE FROM plans;")
        conn.commit()

    plans_imported = 0
    versions_imported = 0
    positions_imported = 0
    contributions_imported = 0

    plans = data.get("plans", [])
    for p in plans:
        cursor.execute("INSERT INTO plans (title, description) VALUES (?, ?)", (p["title"], p.get("description")))
        plan_id = cursor.lastrowid
        plans_imported += 1

        versions = p.get("versions", [])
        for v in versions:
            cursor.execute(
                "INSERT INTO versions (plan_id, title, effective_date, is_active) VALUES (?, ?, ?, ?)",
                (plan_id, v["title"], v.get("effective_date"), v.get("is_active", 1)),
            )
            version_id = cursor.lastrowid
            versions_imported += 1

            positions = v.get("positions", [])
            for idx, pos in enumerate(positions):
                cursor.execute(
                    "INSERT INTO positions (version_id, title, amount, comment, category, sort_order) VALUES (?, ?, ?, ?, ?, ?)",
                    (version_id, pos["title"], pos["amount"], pos.get("comment"), pos.get("category"), pos.get("sort_order", idx)),
                )
                positions_imported += 1

            contributions = v.get("contributions", [])
            for idx, c in enumerate(contributions):
                cursor.execute(
                    "INSERT INTO contributions (version_id, person_name, amount, comment, sort_order) VALUES (?, ?, ?, ?, ?)",
                    (version_id, c["person_name"], c["amount"], c.get("comment"), c.get("sort_order", idx)),
                )
                contributions_imported += 1

    conn.commit()
    return {
        "success": True,
        "plans_imported": plans_imported,
        "versions_imported": versions_imported,
        "positions_imported": positions_imported,
        "contributions_imported": contributions_imported,
    }

