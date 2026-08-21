import sqlite3
from fastapi import APIRouter, Depends, HTTPException, status

from app.database import get_db
from app.auth import verify_password, create_access_token, get_current_user
from app import schemas, crud

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/login")
def login(req: schemas.LoginRequest, conn: sqlite3.Connection = Depends(get_db)):
    user_row = conn.execute("SELECT * FROM users WHERE username = ?", (req.username,)).fetchone()
    if not user_row or not verify_password(req.password, user_row["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ungültiger Benutzername oder Passwort",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = dict(user_row)
    token = create_access_token(
        {
            "sub": user["username"],
            "role": user["role"],
            "name": user["name"],
        }
    )

    assigned_plans = crud.get_user_assigned_plans(conn, user["id"])

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "name": user["name"],
            "role": user["role"],
            "can_manage_plans": bool(user.get("can_manage_plans", 0)),
            "can_export": bool(user.get("can_export", 1)),
            "can_import": bool(user.get("can_import", 0)),
            "can_manage_backups": bool(user.get("can_manage_backups", 0)),
            "can_manage_users": bool(user.get("can_manage_users", 0)),
            "can_run_testsuite": bool(user.get("can_run_testsuite", 0)),
            "can_view_changelog": bool(user.get("can_view_changelog", 1)),
            "assigned_plan_ids": assigned_plans,
        },
    }


@router.get("/me", response_model=schemas.UserResponse)
def get_me(current_user: dict = Depends(get_current_user), conn: sqlite3.Connection = Depends(get_db)):
    user_data = dict(current_user)
    user_data["assigned_plan_ids"] = crud.get_user_assigned_plans(conn, user_data["id"])
    return user_data
