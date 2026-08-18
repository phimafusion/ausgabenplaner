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

    ver_rows = conn.execute(
        "SELECT id, title, effective_date, is_active, created_at, created_by, updated_at, updated_by FROM versions WHERE plan_id = ? ORDER BY id DESC",
        (plan_id,),
    ).fetchall()
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


def update_plan(conn: sqlite3.Connection, plan_id: int, title: Optional[str] = None, description: Optional[str] = None) -> Optional[Dict[str, Any]]:
    fields = []
    values = []
    if title is not None:
        fields.append("title = ?")
        values.append(title)
    if description is not None:
        fields.append("description = ?")
        values.append(description)
    if fields:
        values.append(plan_id)
        cursor = conn.cursor()
        cursor.execute(f"UPDATE plans SET {', '.join(fields)} WHERE id = ?", tuple(values))
        conn.commit()
    return get_active_plan(conn)


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


def save_new_version(
    conn: sqlite3.Connection,
    plan_id: int,
    title: str,
    effective_date: Optional[str] = None,
    positions: Optional[List[Dict[str, Any]]] = None,
    contributions: Optional[List[Dict[str, Any]]] = None,
    created_by: Optional[str] = "Administrator",
) -> Dict[str, Any]:
    cursor = conn.cursor()
    # Deactivate existing active versions for this plan
    cursor.execute("UPDATE versions SET is_active = 0 WHERE plan_id = ?", (plan_id,))

    # Insert new active version with created_by audit metadata
    cursor.execute(
        "INSERT INTO versions (plan_id, title, effective_date, is_active, created_by) VALUES (?, ?, ?, 1, ?)",
        (plan_id, title, effective_date, created_by or "Administrator"),
    )
    new_ver_id = cursor.lastrowid
    if new_ver_id is None:
        raise ValueError("Fehler beim Erstellen der Version")

    # Insert positions
    if positions:
        for idx, pos in enumerate(positions):
            p_title = pos.get("title") or ""
            p_amount = float(pos.get("amount") or 0.0)
            p_comment = pos.get("comment")
            p_cat = pos.get("category")
            p_sort = pos.get("sort_order", idx)
            cursor.execute(
                "INSERT INTO positions (version_id, title, amount, comment, category, sort_order) VALUES (?, ?, ?, ?, ?, ?)",
                (new_ver_id, p_title, p_amount, p_comment, p_cat, p_sort),
            )

    # Insert contributions
    if contributions:
        for idx, c in enumerate(contributions):
            c_person = c.get("person_name") or ""
            c_amount = float(c.get("amount") or 0.0)
            c_comment = c.get("comment")
            c_sort = c.get("sort_order", idx)
            cursor.execute(
                "INSERT INTO contributions (version_id, person_name, amount, comment, sort_order) VALUES (?, ?, ?, ?, ?)",
                (new_ver_id, c_person, c_amount, c_comment, c_sort),
            )

    conn.commit()
    details = get_version_details(conn, new_ver_id)
    if details is None:
        raise ValueError("Fehler beim Abrufen der erstellten Version")
    return details


def update_version(
    conn: sqlite3.Connection,
    version_id: int,
    title: Optional[str] = None,
    effective_date: Optional[str] = None,
    updated_by: Optional[str] = "Administrator",
) -> Optional[Dict[str, Any]]:
    existing = conn.execute("SELECT * FROM versions WHERE id = ?", (version_id,)).fetchone()
    if not existing:
        return None

    current = dict(existing)
    new_title = title if title is not None else current["title"]
    new_date = effective_date if effective_date is not None else current["effective_date"]
    now_iso = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn.execute(
        "UPDATE versions SET title = ?, effective_date = ?, updated_at = ?, updated_by = ? WHERE id = ?",
        (new_title, new_date, now_iso, updated_by or "Administrator", version_id),
    )
    conn.commit()
    return get_version_details(conn, version_id)


def delete_version(conn: sqlite3.Connection, version_id: int) -> bool:
    ver_row = conn.execute("SELECT * FROM versions WHERE id = ?", (version_id,)).fetchone()
    if not ver_row:
        return False

    ver = dict(ver_row)
    plan_id = ver["plan_id"]
    is_active = ver["is_active"]

    count_row = conn.execute("SELECT COUNT(*) as cnt FROM versions WHERE plan_id = ?", (plan_id,)).fetchone()
    if count_row and count_row["cnt"] <= 1:
        raise ValueError("Der letzte verbleibende Stand eines Plans kann nicht gelöscht werden.")

    cursor = conn.cursor()
    cursor.execute("DELETE FROM positions WHERE version_id = ?", (version_id,))
    cursor.execute("DELETE FROM contributions WHERE version_id = ?", (version_id,))
    cursor.execute("DELETE FROM versions WHERE id = ?", (version_id,))

    # If the deleted version was active, make the latest remaining version active
    if is_active == 1:
        latest = conn.execute("SELECT id FROM versions WHERE plan_id = ? ORDER BY id DESC LIMIT 1", (plan_id,)).fetchone()
        if latest:
            cursor.execute("UPDATE versions SET is_active = 1 WHERE id = ?", (latest["id"],))

    conn.commit()
    return True


def activate_version(conn: sqlite3.Connection, plan_id: int, version_id: int) -> Optional[Dict[str, Any]]:
    ver = conn.execute("SELECT id FROM versions WHERE id = ? AND plan_id = ?", (version_id, plan_id)).fetchone()
    if not ver:
        return None
    cursor = conn.cursor()
    cursor.execute("UPDATE versions SET is_active = 0 WHERE plan_id = ?", (plan_id,))
    cursor.execute("UPDATE versions SET is_active = 1 WHERE id = ?", (version_id,))
    conn.commit()
    return get_version_details(conn, version_id)


def get_plan_history(conn: sqlite3.Connection, plan_id: int) -> List[Dict[str, Any]]:
    ver_rows = conn.execute(
        "SELECT id, plan_id, title, effective_date, is_active, created_at, created_by, updated_at, updated_by FROM versions WHERE plan_id = ? ORDER BY id DESC",
        (plan_id,),
    ).fetchall()

    history = []
    for r in ver_rows:
        v_dict = dict(r)
        v_id = v_dict["id"]
        v_details = get_version_details(conn, v_id)
        if v_details:
            v_dict["positions_count"] = len(v_details["positions"])
            v_dict["contributions_count"] = len(v_details["contributions"])
            v_dict["totals"] = v_details["totals"]
        else:
            v_dict["positions_count"] = 0
            v_dict["contributions_count"] = 0
            v_dict["totals"] = {}
        history.append(v_dict)

    return history


def create_version_snapshot(conn: sqlite3.Connection, plan_id: int, title: str, effective_date: Optional[str], copy_from_version_id: Optional[int] = None) -> Dict[str, Any]:
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO versions (plan_id, title, effective_date, is_active) VALUES (?, ?, ?, 1)",
        (plan_id, title, effective_date),
    )
    new_ver_id = cursor.lastrowid
    if new_ver_id is None:
        raise ValueError("Fehler beim Erstellen der Snapshot-Version")

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
    details = get_version_details(conn, new_ver_id)
    if details is None:
        raise ValueError("Fehler beim Abrufen der Snapshot-Version")
    return details


def get_history_comparison(conn: sqlite3.Connection, plan_id: int) -> Dict[str, Any]:
    ver_rows = conn.execute(
        "SELECT id, title, effective_date, created_at, created_by, updated_at, updated_by FROM versions WHERE plan_id = ? ORDER BY id ASC",
        (plan_id,),
    ).fetchall()

    versions = [dict(v) for v in ver_rows]

    # Collect all positions across versions
    positions_map: Dict[str, Dict[str, Any]] = {}  # title -> { category, comment, values: {v_id: amount} }
    # Collect all contributions across versions
    contributions_map: Dict[str, Dict[str, Any]] = {}  # person_name -> { comment, values: {v_id: amount} }

    totals_by_version: Dict[str, Dict[str, Any]] = {}

    for v in versions:
        v_id = v["id"]
        v_details = get_version_details(conn, v_id)
        if not v_details:
            continue
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

