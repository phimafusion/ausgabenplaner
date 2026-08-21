import sqlite3
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from app.database import get_db
from app.auth import get_password_hash, require_permission
from app import schemas, crud

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.post("", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    req: schemas.UserCreate,
    current_user: dict = Depends(require_permission("can_manage_users")),
    conn: sqlite3.Connection = Depends(get_db),
):
    existing = conn.execute("SELECT id FROM users WHERE username = ?", (req.username,)).fetchone()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Benutzername existiert bereits")

    hashed_pw = get_password_hash(req.password)
    can_manage_plans_val = 1 if req.can_manage_plans else 0
    can_manage_categories_val = 1 if req.can_manage_categories else 0
    can_export_val = 1 if req.can_export else 0
    can_import_val = 1 if req.can_import else 0
    can_manage_backups_val = 1 if req.can_manage_backups else 0
    can_manage_users_val = 1 if req.can_manage_users else 0
    can_run_testsuite_val = 1 if req.can_run_testsuite else 0
    can_view_changelog_val = 1 if req.can_view_changelog else 0

    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO users (
            username, password_hash, name, role,
            can_manage_plans, can_manage_categories, can_export, can_import,
            can_manage_backups, can_manage_users, can_run_testsuite, can_view_changelog
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            req.username, hashed_pw, req.name, req.role,
            can_manage_plans_val, can_manage_categories_val, can_export_val, can_import_val,
            can_manage_backups_val, can_manage_users_val, can_run_testsuite_val, can_view_changelog_val,
        ),
    )
    conn.commit()
    user_id = cursor.lastrowid
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Fehler beim Erstellen des Benutzers")

    if req.assigned_plan_ids is not None:
        crud.set_user_assigned_plans(conn, user_id, req.assigned_plan_ids)
        assigned = req.assigned_plan_ids
    else:
        assigned = []

    return {
        "id": user_id,
        "username": req.username,
        "name": req.name,
        "role": req.role,
        "can_manage_plans": bool(can_manage_plans_val),
        "can_manage_categories": bool(can_manage_categories_val),
        "can_export": bool(can_export_val),
        "can_import": bool(can_import_val),
        "can_manage_backups": bool(can_manage_backups_val),
        "can_manage_users": bool(can_manage_users_val),
        "can_run_testsuite": bool(can_run_testsuite_val),
        "can_view_changelog": bool(can_view_changelog_val),
        "assigned_plan_ids": assigned,
    }


@router.get("", response_model=List[schemas.UserResponse])
def list_users(
    current_user: dict = Depends(require_permission("can_manage_users")),
    conn: sqlite3.Connection = Depends(get_db),
):
    rows = conn.execute(
        """
        SELECT id, username, name, role,
               can_manage_plans, can_manage_categories, can_export, can_import,
               can_manage_backups, can_manage_users, can_run_testsuite, can_view_changelog,
               created_at
        FROM users ORDER BY id ASC
        """
    ).fetchall()
    res = []
    for r in rows:
        d = dict(r)
        d["can_manage_plans"] = bool(d.get("can_manage_plans", 0))
        d["can_manage_categories"] = bool(d.get("can_manage_categories", 0))
        d["can_export"] = bool(d.get("can_export", 1))
        d["can_import"] = bool(d.get("can_import", 0))
        d["can_manage_backups"] = bool(d.get("can_manage_backups", 0))
        d["can_manage_users"] = bool(d.get("can_manage_users", 0))
        d["can_run_testsuite"] = bool(d.get("can_run_testsuite", 0))
        d["can_view_changelog"] = bool(d.get("can_view_changelog", 1))
        d["assigned_plan_ids"] = crud.get_user_assigned_plans(conn, d["id"])
        res.append(d)
    return res


@router.patch("/{user_id}", response_model=schemas.UserResponse)
def update_user_route(
    user_id: int,
    req: schemas.UserUpdate,
    current_user: dict = Depends(require_permission("can_manage_users")),
    conn: sqlite3.Connection = Depends(get_db),
):
    existing = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Benutzer nicht gefunden")

    current = dict(existing)
    new_name = req.name if req.name is not None else current["name"]
    new_role = req.role if req.role is not None else current["role"]
    new_can_manage_plans = (1 if req.can_manage_plans else 0) if req.can_manage_plans is not None else current.get("can_manage_plans", 0)
    new_can_manage_categories = (1 if req.can_manage_categories else 0) if req.can_manage_categories is not None else current.get("can_manage_categories", 0)
    new_can_export = (1 if req.can_export else 0) if req.can_export is not None else current.get("can_export", 1)
    new_can_import = (1 if req.can_import else 0) if req.can_import is not None else current.get("can_import", 0)
    new_can_manage_backups = (1 if req.can_manage_backups else 0) if req.can_manage_backups is not None else current.get("can_manage_backups", 0)
    new_can_manage_users = (1 if req.can_manage_users else 0) if req.can_manage_users is not None else current.get("can_manage_users", 0)
    new_can_run_testsuite = (1 if req.can_run_testsuite else 0) if req.can_run_testsuite is not None else current.get("can_run_testsuite", 0)
    new_can_view_changelog = (1 if req.can_view_changelog else 0) if req.can_view_changelog is not None else current.get("can_view_changelog", 1)

    # Admin safety: If demoting admin, ensure at least one other admin remains
    if current["role"] == "admin" and new_role != "admin":
        admin_count = conn.execute("SELECT COUNT(*) as cnt FROM users WHERE role = 'admin'").fetchone()["cnt"]
        if admin_count <= 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Der letzte Administrator kann nicht herabgestuft werden.")

    if req.password and req.password.strip():
        new_pw_hash = get_password_hash(req.password.strip())
        conn.execute(
            """
            UPDATE users SET name = ?, role = ?,
                             can_manage_plans = ?, can_manage_categories = ?, can_export = ?, can_import = ?,
                             can_manage_backups = ?, can_manage_users = ?, can_run_testsuite = ?, can_view_changelog = ?,
                             password_hash = ?
            WHERE id = ?
            """,
            (
                new_name, new_role,
                new_can_manage_plans, new_can_manage_categories, new_can_export, new_can_import,
                new_can_manage_backups, new_can_manage_users, new_can_run_testsuite, new_can_view_changelog,
                new_pw_hash, user_id,
            ),
        )
    else:
        conn.execute(
            """
            UPDATE users SET name = ?, role = ?,
                             can_manage_plans = ?, can_manage_categories = ?, can_export = ?, can_import = ?,
                             can_manage_backups = ?, can_manage_users = ?, can_run_testsuite = ?, can_view_changelog = ?
            WHERE id = ?
            """,
            (
                new_name, new_role,
                new_can_manage_plans, new_can_manage_categories, new_can_export, new_can_import,
                new_can_manage_backups, new_can_manage_users, new_can_run_testsuite, new_can_view_changelog,
                user_id,
            ),
        )
    conn.commit()

    if req.assigned_plan_ids is not None:
        crud.set_user_assigned_plans(conn, user_id, req.assigned_plan_ids)

    updated = conn.execute(
        """
        SELECT id, username, name, role,
               can_manage_plans, can_manage_categories, can_export, can_import,
               can_manage_backups, can_manage_users, can_run_testsuite, can_view_changelog
        FROM users WHERE id = ?
        """,
        (user_id,),
    ).fetchone()
    res = dict(updated)
    res["can_manage_plans"] = bool(res.get("can_manage_plans", 0))
    res["can_manage_categories"] = bool(res.get("can_manage_categories", 0))
    res["can_export"] = bool(res.get("can_export", 1))
    res["can_import"] = bool(res.get("can_import", 0))
    res["can_manage_backups"] = bool(res.get("can_manage_backups", 0))
    res["can_manage_users"] = bool(res.get("can_manage_users", 0))
    res["can_run_testsuite"] = bool(res.get("can_run_testsuite", 0))
    res["can_view_changelog"] = bool(res.get("can_view_changelog", 1))
    res["assigned_plan_ids"] = crud.get_user_assigned_plans(conn, user_id)
    return res
    res["can_manage_users"] = bool(res.get("can_manage_users", 0))
    res["can_run_testsuite"] = bool(res.get("can_run_testsuite", 0))
    res["can_view_changelog"] = bool(res.get("can_view_changelog", 1))
    res["assigned_plan_ids"] = crud.get_user_assigned_plans(conn, user_id)
    return res


@router.delete("/{user_id}")
def delete_user_route(
    user_id: int,
    current_user: dict = Depends(require_permission("can_manage_users")),
    conn: sqlite3.Connection = Depends(get_db),
):
    existing = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Benutzer nicht gefunden")

    if existing["id"] == current_user["id"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sie können Ihren eigenen Benutzer-Account nicht löschen.")

    if existing["role"] == "admin":
        admin_count = conn.execute("SELECT COUNT(*) as cnt FROM users WHERE role = 'admin'").fetchone()["cnt"]
        if admin_count <= 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Der letzte Administrator kann nicht gelöscht werden.")

    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    return {"message": "Benutzer gelöscht"}
