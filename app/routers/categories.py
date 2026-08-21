import sqlite3
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from app.database import get_db
from app.auth import get_current_user, require_permission
from app import schemas, crud

router = APIRouter(prefix="/api/categories", tags=["Categories"])


@router.get("", response_model=List[schemas.CategoryResponse])
def list_categories_route(
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    return crud.get_all_categories(conn)


@router.post("", response_model=schemas.CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category_route(
    req: schemas.CategoryCreate,
    current_user: dict = Depends(require_permission("can_manage_categories")),
    conn: sqlite3.Connection = Depends(get_db),
):
    existing = conn.execute("SELECT id FROM categories WHERE name = ?", (req.name.strip(),)).fetchone()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Eine Kategorie mit diesem Namen existiert bereits")

    return crud.create_category(
        conn,
        name=req.name,
        color=req.color or "#64748b",
        icon=req.icon or "📦",
        sort_order=req.sort_order or 0,
    )


@router.patch("/{category_id}", response_model=schemas.CategoryResponse)
def update_category_route(
    category_id: int,
    req: schemas.CategoryUpdate,
    current_user: dict = Depends(require_permission("can_manage_categories")),
    conn: sqlite3.Connection = Depends(get_db),
):
    if req.name and req.name.strip():
        existing = conn.execute("SELECT id FROM categories WHERE name = ? AND id != ?", (req.name.strip(), category_id)).fetchone()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Eine Kategorie mit diesem Namen existiert bereits")

    cat = crud.update_category(
        conn,
        category_id=category_id,
        name=req.name,
        color=req.color,
        icon=req.icon,
        sort_order=req.sort_order,
    )
    if not cat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kategorie nicht gefunden")
    return cat


@router.delete("/{category_id}")
def delete_category_route(
    category_id: int,
    current_user: dict = Depends(require_permission("can_manage_categories")),
    conn: sqlite3.Connection = Depends(get_db),
):
    try:
        success = crud.delete_category(conn, category_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kategorie nicht gefunden")
        return {"message": "Kategorie erfolgreich gelöscht"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
