import os
import sys
import json
import re
import subprocess
import sqlite3
import datetime
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, Response, StreamingResponse

from app.database import get_db, init_db
from app.auth import verify_password, create_access_token, get_current_user, get_current_admin, get_password_hash, decode_access_token
from app import schemas, crud



@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Ausgabenplaner API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Auth Endpoints ---

@app.post("/api/auth/login", response_model=schemas.TokenResponse)
def login(req: schemas.LoginRequest, conn: sqlite3.Connection = Depends(get_db)):
    user_row = conn.execute("SELECT * FROM users WHERE username = ?", (req.username,)).fetchone()
    if not user_row:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Ungültiger Benutzername oder Passwort")

    user = dict(user_row)
    if not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Ungültiger Benutzername oder Passwort")

    token = create_access_token({"sub": user["username"], "role": user["role"]})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "name": user["name"],
            "role": user["role"],
            "can_export": bool(user.get("can_export", 1)),
        },
    }


@app.get("/api/auth/me", response_model=schemas.UserResponse)
def get_me(current_user: dict = Depends(get_current_user)):
    return current_user


# --- User Management Endpoints (Admin only) ---

@app.post("/api/users", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    req: schemas.UserCreate,
    current_admin: dict = Depends(get_current_admin),
    conn: sqlite3.Connection = Depends(get_db),
):
    existing = conn.execute("SELECT id FROM users WHERE username = ?", (req.username,)).fetchone()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Benutzername existiert bereits")

    hashed_pw = get_password_hash(req.password)
    can_export_val = 1 if req.can_export else 0
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (username, password_hash, name, role, can_export) VALUES (?, ?, ?, ?, ?)",
        (req.username, hashed_pw, req.name, req.role, can_export_val),
    )
    conn.commit()
    user_id = cursor.lastrowid
    return {"id": user_id, "username": req.username, "name": req.name, "role": req.role, "can_export": bool(can_export_val)}


@app.get("/api/users")
def list_users(
    current_admin: dict = Depends(get_current_admin),
    conn: sqlite3.Connection = Depends(get_db),
):
    rows = conn.execute("SELECT id, username, name, role, can_export, created_at FROM users ORDER BY id ASC").fetchall()
    res = []
    for r in rows:
        d = dict(r)
        d["can_export"] = bool(d.get("can_export", 1))
        res.append(d)
    return res


@app.patch("/api/users/{user_id}", response_model=schemas.UserResponse)
def update_user_route(
    user_id: int,
    req: schemas.UserUpdate,
    current_admin: dict = Depends(get_current_admin),
    conn: sqlite3.Connection = Depends(get_db),
):
    existing = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Benutzer nicht gefunden")

    current = dict(existing)
    new_name = req.name if req.name is not None else current["name"]
    new_role = req.role if req.role is not None else current["role"]
    new_can_export = (1 if req.can_export else 0) if req.can_export is not None else current.get("can_export", 1)

    # Admin safety: If demoting admin, ensure at least one other admin remains
    if current["role"] == "admin" and new_role != "admin":
        admin_count = conn.execute("SELECT COUNT(*) as cnt FROM users WHERE role = 'admin'").fetchone()["cnt"]
        if admin_count <= 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Der letzte Administrator kann nicht herabgestuft werden.")

    if req.password and req.password.strip():
        new_pw_hash = get_password_hash(req.password.strip())
        conn.execute(
            "UPDATE users SET name = ?, role = ?, can_export = ?, password_hash = ? WHERE id = ?",
            (new_name, new_role, new_can_export, new_pw_hash, user_id),
        )
    else:
        conn.execute(
            "UPDATE users SET name = ?, role = ?, can_export = ? WHERE id = ?",
            (new_name, new_role, new_can_export, user_id),
        )
    conn.commit()

    updated = conn.execute("SELECT id, username, name, role, can_export FROM users WHERE id = ?", (user_id,)).fetchone()
    res = dict(updated)
    res["can_export"] = bool(res.get("can_export", 1))
    return res


@app.delete("/api/users/{user_id}")
def delete_user_route(
    user_id: int,
    current_admin: dict = Depends(get_current_admin),
    conn: sqlite3.Connection = Depends(get_db),
):
    existing = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Benutzer nicht gefunden")

    if existing["id"] == current_admin["id"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sie können Ihren eigenen Administrator-Account nicht löschen.")

    if existing["role"] == "admin":
        admin_count = conn.execute("SELECT COUNT(*) as cnt FROM users WHERE role = 'admin'").fetchone()["cnt"]
        if admin_count <= 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Der letzte Administrator kann nicht gelöscht werden.")

    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    return {"message": "Benutzer gelöscht"}


@app.post("/api/admin/run-tests")
def run_test_suite_route(current_admin: dict = Depends(get_current_admin)):
    env = os.environ.copy()
    env["TESTING"] = "1"

    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests",
            "-v",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    return {
        "status": "success" if res.returncode == 0 else "failure",
        "passed": res.returncode == 0,
        "returncode": res.returncode,
        "output": res.stdout + "\n" + res.stderr,
    }


@app.get("/api/admin/run-tests-stream")
def run_tests_stream_route(
    token: Optional[str] = None,
    conn: sqlite3.Connection = Depends(get_db),
):
    if not token:
        raise HTTPException(status_code=401, detail="Nicht authentifiziert")

    payload = decode_access_token(token)
    if not payload or payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin-Rechte erforderlich")

    def event_generator():
        env = os.environ.copy()
        env["TESTING"] = "1"
        env["PYTHONUNBUFFERED"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"

        proc = subprocess.Popen(
            [
                sys.executable,
                "-u",
                "-m",
                "pytest",
                "tests",
                "-v",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            env=env,
        )

        progress = 0
        pattern = re.compile(r"\[\s*(\d+)%\]")

        yield f"data: {json.dumps({'type': 'start', 'message': 'Starte Pytest Testsuite...'})}\n\n"

        if proc.stdout is not None:
            if hasattr(proc.stdout, "readline") and callable(proc.stdout.readline):
                for line in iter(proc.stdout.readline, ''):
                    if not line:
                        break
                    match = pattern.search(line)
                    if match:
                        progress = int(match.group(1))
                    yield f"data: {json.dumps({'type': 'log', 'line': line, 'progress': progress})}\n\n"
            else:
                for line in proc.stdout:
                    match = pattern.search(line)
                    if match:
                        progress = int(match.group(1))
                    yield f"data: {json.dumps({'type': 'log', 'line': line, 'progress': progress})}\n\n"

        proc.wait()
        passed = proc.returncode == 0
        yield f"data: {json.dumps({'type': 'complete', 'passed': passed, 'progress': 100})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )





# --- Plan & Version Endpoints ---

@app.get("/api/plans/active", response_model=schemas.PlanResponse)
def get_active_plan_route(
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    plan = crud.get_active_plan(conn)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kein aktiver Plan vorhanden")
    return plan


@app.patch("/api/plans/{plan_id}", response_model=schemas.PlanResponse)
def update_plan_route(
    plan_id: int,
    req: schemas.PlanUpdate,
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    plan = crud.update_plan(conn, plan_id=plan_id, title=req.title, description=req.description)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan nicht gefunden")
    return plan


@app.get("/api/versions/{version_id}", response_model=schemas.VersionResponse)
def get_version_route(
    version_id: int,
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    ver = crud.get_version_details(conn, version_id)
    if not ver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version nicht gefunden")
    return ver


@app.post("/api/plans/{plan_id}/save-version", response_model=schemas.VersionResponse, status_code=status.HTTP_201_CREATED)
def save_version_route(
    plan_id: int,
    req: schemas.VersionSaveRequest,
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    positions_data = [p.model_dump() for p in req.positions]
    contributions_data = [c.model_dump() for c in req.contributions]
    user_name = current_user.get("name") or current_user.get("username") or "Administrator"
    ver = crud.save_new_version(
        conn,
        plan_id=plan_id,
        title=req.title,
        effective_date=req.effective_date,
        positions=positions_data,
        contributions=contributions_data,
        created_by=user_name,
    )
    return ver


@app.get("/api/plans/{plan_id}/history", response_model=List[schemas.HistoryVersionSummary])
def get_plan_history_route(
    plan_id: int,
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    return crud.get_plan_history(conn, plan_id)


@app.post("/api/versions/{version_id}/activate", response_model=schemas.VersionResponse)
def activate_version_route(
    version_id: int,
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    ver = crud.get_version_details(conn, version_id)
    if not ver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version nicht gefunden")
    activated = crud.activate_version(conn, plan_id=ver["plan_id"], version_id=version_id)
    if not activated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version nicht gefunden")
    return activated


@app.patch("/api/versions/{version_id}", response_model=schemas.VersionResponse)
def update_version_route(
    version_id: int,
    req: schemas.VersionUpdate,
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    user_name = current_user.get("name") or current_user.get("username") or "Administrator"
    updated = crud.update_version(
        conn,
        version_id=version_id,
        title=req.title,
        effective_date=req.effective_date,
        updated_by=user_name,
    )
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version nicht gefunden")
    return updated


@app.delete("/api/versions/{version_id}")
def delete_version_route(
    version_id: int,
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    try:
        success = crud.delete_version(conn, version_id=version_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version nicht gefunden")
    return {"message": "Version erfolgreich gelöscht", "id": version_id}



@app.post("/api/plans/{plan_id}/snapshots", response_model=schemas.VersionResponse, status_code=status.HTTP_201_CREATED)
def create_snapshot_route(
    plan_id: int,
    req: schemas.VersionCreate,
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    ver = crud.create_version_snapshot(
        conn,
        plan_id=plan_id,
        title=req.title,
        effective_date=req.effective_date,
        copy_from_version_id=req.copy_from_version_id,
    )
    return ver


@app.get("/api/plans/{plan_id}/history-comparison", response_model=schemas.HistoryComparisonResponse)
def get_history_comparison_route(
    plan_id: int,
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    return crud.get_history_comparison(conn, plan_id)


# --- Positions Endpoints ---

@app.post("/api/versions/{version_id}/positions", response_model=schemas.PositionResponse, status_code=status.HTTP_201_CREATED)
def create_position_route(
    version_id: int,
    req: schemas.PositionCreate,
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    return crud.create_position(
        conn,
        version_id=version_id,
        title=req.title,
        amount=req.amount,
        comment=req.comment,
        category=req.category,
        sort_order=req.sort_order or 0,
    )


@app.put("/api/positions/{position_id}", response_model=schemas.PositionResponse)
def update_position_route(
    position_id: int,
    req: schemas.PositionUpdate,
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    updated = crud.update_position(
        conn,
        position_id=position_id,
        title=req.title,
        amount=req.amount,
        comment=req.comment,
        category=req.category,
        sort_order=req.sort_order,
    )
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Position nicht gefunden")
    return updated


@app.delete("/api/positions/{position_id}")
def delete_position_route(
    position_id: int,
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    success = crud.delete_position(conn, position_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Position nicht gefunden")
    return {"message": "Position gelöscht"}


# --- Contributions Endpoints ---

@app.post("/api/versions/{version_id}/contributions", response_model=schemas.ContributionResponse, status_code=status.HTTP_201_CREATED)
def create_contribution_route(
    version_id: int,
    req: schemas.ContributionCreate,
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    return crud.create_contribution(
        conn,
        version_id=version_id,
        person_name=req.person_name,
        amount=req.amount,
        comment=req.comment,
        sort_order=req.sort_order or 0,
    )


@app.put("/api/contributions/{contribution_id}", response_model=schemas.ContributionResponse)
def update_contribution_route(
    contribution_id: int,
    req: schemas.ContributionUpdate,
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    updated = crud.update_contribution(
        conn,
        contribution_id=contribution_id,
        person_name=req.person_name,
        amount=req.amount,
        comment=req.comment,
        sort_order=req.sort_order,
    )
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Beitrag nicht gefunden")
    return updated


@app.delete("/api/contributions/{contribution_id}")
def delete_contribution_route(
    contribution_id: int,
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    success = crud.delete_contribution(conn, contribution_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Beitrag nicht gefunden")
    return {"message": "Beitrag gelöscht"}


# --- Export / Import Endpoints ---

@app.get("/api/data/export", response_model=schemas.FullExportData)
def export_data_route(
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    if current_user.get("role") != "admin" and not current_user.get("can_export"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sie besitzen keine Berechtigung zum Exportieren der Daten.")
    return crud.export_full_data(conn)


@app.get("/api/data/export-xlsx")
@app.get("/api/data/export/xlsx")
def export_data_xlsx_route(
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    if current_user.get("role") != "admin" and not current_user.get("can_export"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sie besitzen keine Berechtigung zum Exportieren der Daten.")
    xlsx_bytes = crud.export_full_data_xlsx(conn)
    date_str = datetime.date.today().isoformat()
    filename = f"ausgabenplaner_export_{date_str}.xlsx"
    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )



@app.post("/api/data/import")
def import_data_route(
    req: schemas.FullExportData,
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    if current_user.get("role") != "admin" and not current_user.get("can_export"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sie besitzen keine Berechtigung zum Importieren der Daten.")
    data = req.model_dump()
    return crud.import_full_data(conn, data, overwrite=True)


# --- Static Files / SPA Mounting ---

static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/{full_path:path}")
def serve_spa(full_path: str):
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API route not found")
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(
            index_file,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
            },
        )
    return JSONResponse({"message": "Ausgabenplaner API running"})
