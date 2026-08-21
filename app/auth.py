import os
from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
import bcrypt
from fastapi import Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import sqlite3
from app.database import get_db

SECRET_KEY = os.getenv("JWT_SECRET", "super-secret-key-ausgabenplaner-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

security = HTTPBearer(auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        pwd_bytes = plain_password.encode("utf-8")
        hash_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(pwd_bytes, hash_bytes)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")



def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    token_param: Optional[str] = Query(None, alias="token"),
    conn: sqlite3.Connection = Depends(get_db),
) -> dict:
    token = credentials.credentials if credentials else token_param
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nicht authentifiziert",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ungültiges Token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Ungültiges Token")

    user_row = conn.execute(
        """
        SELECT id, username, name, role, can_manage_plans, can_export, can_import,
               can_manage_backups, can_manage_users, can_run_testsuite, can_view_changelog
        FROM users WHERE username = ?
        """,
        (username,),
    ).fetchone()
    if user_row is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Benutzer nicht gefunden")

    res = dict(user_row)
    res["can_manage_plans"] = bool(res.get("can_manage_plans", 0))
    res["can_export"] = bool(res.get("can_export", 1))
    res["can_import"] = bool(res.get("can_import", 0))
    res["can_manage_backups"] = bool(res.get("can_manage_backups", 0))
    res["can_manage_users"] = bool(res.get("can_manage_users", 0))
    res["can_run_testsuite"] = bool(res.get("can_run_testsuite", 0))
    res["can_view_changelog"] = bool(res.get("can_view_changelog", 1))

    # Assigned plans
    assigned_rows = conn.execute("SELECT plan_id FROM user_plans WHERE user_id = ?", (res["id"],)).fetchall()
    res["assigned_plan_ids"] = [r[0] for r in assigned_rows]
    return res


def get_current_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin-Rechte erforderlich")
    return current_user


PERMISSION_ERROR_MESSAGES = {
    "can_manage_plans": "Sie besitzen keine Berechtigung zum Verwalten von Plänen.",
    "can_export": "Sie besitzen keine Berechtigung zum Exportieren der Daten.",
    "can_import": "Sie besitzen keine Berechtigung zum Importieren von Daten.",
    "can_manage_backups": "Sie besitzen keine Berechtigung zur Verwaltung von Backups.",
    "can_manage_users": "Sie besitzen keine Berechtigung zur Benutzerverwaltung.",
    "can_run_testsuite": "Sie besitzen keine Berechtigung zum Ausführen der Testsuite.",
    "can_view_changelog": "Sie besitzen keine Berechtigung zum Einsehen des Changelogs.",
}


def require_permission(permission_key: str):
    """Dependency factory checking if current user is admin OR has specific permission."""
    def _perm_checker(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user.get("role") == "admin" or current_user.get(permission_key):
            return current_user
        err_msg = PERMISSION_ERROR_MESSAGES.get(
            permission_key, f"Fehlende Berechtigung ({permission_key})"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=err_msg,
        )
    return _perm_checker
