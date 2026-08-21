import sqlite3
import datetime
from fastapi import APIRouter, Depends, Response

from app.database import get_db
from app.auth import require_permission
from app import schemas, crud

router = APIRouter(prefix="/api/data", tags=["Data Export/Import"])


@router.get("/export", response_model=schemas.FullExportData)
def export_data_route(
    current_user: dict = Depends(require_permission("can_export")),
    conn: sqlite3.Connection = Depends(get_db),
):
    return crud.export_full_data(conn)


@router.get("/export-xlsx")
@router.get("/export/xlsx")
def export_data_xlsx_route(
    current_user: dict = Depends(require_permission("can_export")),
    conn: sqlite3.Connection = Depends(get_db),
):
    xlsx_bytes = crud.export_full_data_xlsx(conn)
    date_str = datetime.date.today().isoformat()
    filename = f"ausgabenplaner_export_{date_str}.xlsx"
    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/import")
def import_data_route(
    req: schemas.FullExportData,
    current_user: dict = Depends(require_permission("can_import")),
    conn: sqlite3.Connection = Depends(get_db),
):
    data = req.model_dump()
    return crud.import_full_data(conn, data, overwrite=True)
