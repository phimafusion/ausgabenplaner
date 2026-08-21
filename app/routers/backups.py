import sqlite3
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse

from app.database import get_db
from app.auth import require_permission
from app import schemas, backups

router = APIRouter(prefix="/api/admin/backups", tags=["Backups"])


@router.get("/settings", response_model=schemas.BackupSettingsResponse)
def get_backup_settings_route(
    current_user: dict = Depends(require_permission("can_manage_backups")),
    conn: sqlite3.Connection = Depends(get_db),
):
    return backups.get_backup_settings(conn)


@router.patch("/settings", response_model=schemas.BackupSettingsResponse)
def update_backup_settings_route(
    req: schemas.BackupSettingsUpdate,
    current_user: dict = Depends(require_permission("can_manage_backups")),
    conn: sqlite3.Connection = Depends(get_db),
):
    return backups.update_backup_settings(
        conn,
        backup_enabled=req.backup_enabled,
        backup_frequency=req.backup_frequency,
        backup_folder=req.backup_folder,
        retention_count=req.retention_count,
        auto_backup_time=req.auto_backup_time,
    )


@router.get("", response_model=List[schemas.BackupFileInfo])
def list_backups_route(
    current_user: dict = Depends(require_permission("can_manage_backups")),
    conn: sqlite3.Connection = Depends(get_db),
):
    return backups.list_database_backups(conn)


@router.post("/create", response_model=schemas.BackupCreateResponse, status_code=status.HTTP_201_CREATED)
def create_backup_route(
    current_user: dict = Depends(require_permission("can_manage_backups")),
    conn: sqlite3.Connection = Depends(get_db),
):
    return backups.create_database_backup(conn)


@router.get("/download/{filename}")
def download_backup_route(
    filename: str,
    current_user: dict = Depends(require_permission("can_manage_backups")),
    conn: sqlite3.Connection = Depends(get_db),
):
    file_path = backups.get_backup_file_path(conn, filename)
    if not file_path or not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backup-Datei nicht gefunden")
    return FileResponse(
        str(file_path),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{file_path.name}"'},
    )


@router.delete("/{filename}")
def delete_backup_route(
    filename: str,
    current_user: dict = Depends(require_permission("can_manage_backups")),
    conn: sqlite3.Connection = Depends(get_db),
):
    success = backups.delete_database_backup(conn, filename)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backup-Datei nicht gefunden")
    return {"message": f"Backup '{filename}' gelöscht"}


@router.post("/restore/{filename}")
def restore_backup_route(
    filename: str,
    current_user: dict = Depends(require_permission("can_manage_backups")),
    conn: sqlite3.Connection = Depends(get_db),
):
    try:
        return backups.restore_database_backup(conn, filename)
    except FileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Backup '{filename}' nicht gefunden")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Fehler bei der Wiederherstellung: {str(e)}")
