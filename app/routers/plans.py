import sqlite3
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status

from app.database import get_db
from app.auth import get_current_user, require_permission
from app import schemas, crud

router = APIRouter(tags=["Plans & Versions"])


# --- Plan Endpoints ---

@router.get("/api/plans")
def list_plans_route(
    include_archived: bool = True,
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    return crud.get_all_plans(
        conn,
        user_id=current_user["id"],
        user_role=current_user["role"],
        include_archived=include_archived,
    )


@router.post("/api/plans", response_model=schemas.PlanResponse, status_code=status.HTTP_201_CREATED)
def create_plan_route(
    req: schemas.PlanCreate,
    current_user: dict = Depends(require_permission("can_manage_plans")),
    conn: sqlite3.Connection = Depends(get_db),
):
    return crud.create_plan(conn, title=req.title, description=req.description)


@router.get("/api/plans/active", response_model=schemas.PlanResponse)
def get_active_plan_route(
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    plan = crud.get_active_plan(conn, user_id=current_user["id"], user_role=current_user["role"])
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kein aktiver Plan vorhanden")
    return plan


@router.get("/api/plans/{plan_id}", response_model=schemas.PlanResponse)
def get_plan_by_id_route(
    plan_id: int,
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    if not crud.check_user_plan_access(conn, current_user["id"], current_user["role"], plan_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Kein Zugriff auf diesen Plan")
    plan = crud.get_plan_details(conn, plan_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan nicht gefunden")
    return plan


@router.patch("/api/plans/{plan_id}", response_model=schemas.PlanResponse)
def update_plan_route(
    plan_id: int,
    req: schemas.PlanUpdate,
    current_user: dict = Depends(require_permission("can_manage_plans")),
    conn: sqlite3.Connection = Depends(get_db),
):
    plan = crud.update_plan(conn, plan_id=plan_id, title=req.title, description=req.description, is_archived=req.is_archived)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan nicht gefunden")
    return plan


@router.post("/api/plans/{plan_id}/duplicate", response_model=schemas.PlanResponse, status_code=status.HTTP_201_CREATED)
def duplicate_plan_route(
    plan_id: int,
    req: Optional[schemas.PlanDuplicateRequest] = None,
    current_user: dict = Depends(require_permission("can_manage_plans")),
    conn: sqlite3.Connection = Depends(get_db),
):
    new_title = req.title if req else None
    dup = crud.duplicate_plan(conn, plan_id=plan_id, new_title=new_title)
    if not dup:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ursprünglicher Plan nicht gefunden")
    return dup


@router.delete("/api/plans/{plan_id}")
def delete_plan_route(
    plan_id: int,
    current_user: dict = Depends(require_permission("can_manage_plans")),
    conn: sqlite3.Connection = Depends(get_db),
):
    try:
        deleted = crud.delete_plan(conn, plan_id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan nicht gefunden")
        return {"message": "Plan erfolgreich gelöscht", "deleted_id": plan_id}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# --- Version & History Endpoints ---

@router.get("/api/versions/{version_id}", response_model=schemas.VersionResponse)
def get_version_route(
    version_id: int,
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    ver = crud.get_version_details(conn, version_id)
    if not ver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version nicht gefunden")
    if not crud.check_user_plan_access(conn, current_user["id"], current_user["role"], ver["plan_id"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Kein Zugriff auf diesen Plan")
    return ver


@router.post("/api/plans/{plan_id}/save-version", response_model=schemas.VersionResponse, status_code=status.HTTP_201_CREATED)
def save_version_route(
    plan_id: int,
    req: schemas.VersionSaveRequest,
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    if not crud.check_user_plan_access(conn, current_user["id"], current_user["role"], plan_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Kein Zugriff auf diesen Plan")
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


@router.get("/api/plans/{plan_id}/history", response_model=List[schemas.HistoryVersionSummary])
def get_plan_history_route(
    plan_id: int,
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    if not crud.check_user_plan_access(conn, current_user["id"], current_user["role"], plan_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Kein Zugriff auf diesen Plan")
    return crud.get_plan_history(conn, plan_id)


@router.post("/api/versions/{version_id}/activate", response_model=schemas.VersionResponse)
def activate_version_route(
    version_id: int,
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    ver = crud.get_version_details(conn, version_id)
    if not ver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version nicht gefunden")
    if not crud.check_user_plan_access(conn, current_user["id"], current_user["role"], ver["plan_id"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Kein Zugriff auf diesen Plan")
    activated = crud.activate_version(conn, plan_id=ver["plan_id"], version_id=version_id)
    if not activated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version nicht gefunden")
    return activated


@router.patch("/api/versions/{version_id}", response_model=schemas.VersionResponse)
def update_version_route(
    version_id: int,
    req: schemas.VersionUpdate,
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    ver = crud.get_version_details(conn, version_id)
    if not ver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version nicht gefunden")
    if not crud.check_user_plan_access(conn, current_user["id"], current_user["role"], ver["plan_id"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Kein Zugriff auf diesen Plan")
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


@router.delete("/api/versions/{version_id}")
def delete_version_route(
    version_id: int,
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    ver = crud.get_version_details(conn, version_id)
    if not ver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version nicht gefunden")
    if not crud.check_user_plan_access(conn, current_user["id"], current_user["role"], ver["plan_id"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Kein Zugriff auf diesen Plan")
    try:
        success = crud.delete_version(conn, version_id=version_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version nicht gefunden")
    return {"message": "Version erfolgreich gelöscht", "id": version_id}


@router.post("/api/plans/{plan_id}/snapshots", response_model=schemas.VersionResponse, status_code=status.HTTP_201_CREATED)
def create_snapshot_route(
    plan_id: int,
    req: schemas.VersionCreate,
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    if not crud.check_user_plan_access(conn, current_user["id"], current_user["role"], plan_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Kein Zugriff auf diesen Plan")
    ver = crud.create_version_snapshot(
        conn,
        plan_id=plan_id,
        title=req.title,
        effective_date=req.effective_date,
        copy_from_version_id=req.copy_from_version_id,
    )
    return ver


@router.get("/api/plans/{plan_id}/history-comparison", response_model=schemas.HistoryComparisonResponse)
def get_history_comparison_route(
    plan_id: int,
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    if not crud.check_user_plan_access(conn, current_user["id"], current_user["role"], plan_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Kein Zugriff auf diesen Plan")
    return crud.get_history_comparison(conn, plan_id)


# --- Positions Endpoints ---

@router.post("/api/versions/{version_id}/positions", response_model=schemas.PositionResponse, status_code=status.HTTP_201_CREATED)
def create_position_route(
    version_id: int,
    req: schemas.PositionCreate,
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    ver = crud.get_version_details(conn, version_id)
    if not ver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version nicht gefunden")
    if not crud.check_user_plan_access(conn, current_user["id"], current_user["role"], ver["plan_id"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Kein Zugriff auf diesen Plan")

    return crud.create_position(
        conn,
        version_id=version_id,
        title=req.title,
        amount=req.amount,
        comment=req.comment,
        category=req.category,
        sort_order=req.sort_order or 0,
    )


@router.put("/api/positions/{position_id}", response_model=schemas.PositionResponse)
def update_position_route(
    position_id: int,
    req: schemas.PositionUpdate,
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    pos_row = conn.execute(
        "SELECT p.id, v.plan_id FROM positions p JOIN versions v ON p.version_id = v.id WHERE p.id = ?",
        (position_id,),
    ).fetchone()
    if not pos_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Position nicht gefunden")
    if not crud.check_user_plan_access(conn, current_user["id"], current_user["role"], pos_row["plan_id"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Kein Zugriff auf diesen Plan")

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


@router.delete("/api/positions/{position_id}")
def delete_position_route(
    position_id: int,
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    pos_row = conn.execute(
        "SELECT p.id, v.plan_id FROM positions p JOIN versions v ON p.version_id = v.id WHERE p.id = ?",
        (position_id,),
    ).fetchone()
    if not pos_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Position nicht gefunden")
    if not crud.check_user_plan_access(conn, current_user["id"], current_user["role"], pos_row["plan_id"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Kein Zugriff auf diesen Plan")

    success = crud.delete_position(conn, position_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Position nicht gefunden")
    return {"message": "Position gelöscht"}


# --- Contributions Endpoints ---

@router.post("/api/versions/{version_id}/contributions", response_model=schemas.ContributionResponse, status_code=status.HTTP_201_CREATED)
def create_contribution_route(
    version_id: int,
    req: schemas.ContributionCreate,
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    ver = crud.get_version_details(conn, version_id)
    if not ver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version nicht gefunden")
    if not crud.check_user_plan_access(conn, current_user["id"], current_user["role"], ver["plan_id"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Kein Zugriff auf diesen Plan")

    return crud.create_contribution(
        conn,
        version_id=version_id,
        person_name=req.person_name,
        amount=req.amount,
        comment=req.comment,
        sort_order=req.sort_order or 0,
    )


@router.put("/api/contributions/{contribution_id}", response_model=schemas.ContributionResponse)
def update_contribution_route(
    contribution_id: int,
    req: schemas.ContributionUpdate,
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    contrib_row = conn.execute(
        "SELECT c.id, v.plan_id FROM contributions c JOIN versions v ON c.version_id = v.id WHERE c.id = ?",
        (contribution_id,),
    ).fetchone()
    if not contrib_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Beitrag nicht gefunden")
    if not crud.check_user_plan_access(conn, current_user["id"], current_user["role"], contrib_row["plan_id"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Kein Zugriff auf diesen Plan")

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


@router.delete("/api/contributions/{contribution_id}")
def delete_contribution_route(
    contribution_id: int,
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    contrib_row = conn.execute(
        "SELECT c.id, v.plan_id FROM contributions c JOIN versions v ON c.version_id = v.id WHERE c.id = ?",
        (contribution_id,),
    ).fetchone()
    if not contrib_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Beitrag nicht gefunden")
    if not crud.check_user_plan_access(conn, current_user["id"], current_user["role"], contrib_row["plan_id"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Kein Zugriff auf diesen Plan")

    success = crud.delete_contribution(conn, contribution_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Beitrag nicht gefunden")
    return {"message": "Beitrag gelöscht"}
