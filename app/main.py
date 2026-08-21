import asyncio
import os
import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from app.database import init_db, get_db_connection
from app import backups
from app.routers import auth, users, plans, data, backups as backups_router, testsuite, categories

APP_VERSION = "4.0.0"


async def backup_scheduler_loop():
    """Background task checking once every 60s for scheduled automated backups based on configured frequency."""
    while True:
        try:
            await asyncio.sleep(60)
            if os.getenv("TESTING") == "1":
                continue
            conn = get_db_connection()
            try:
                settings = backups.get_backup_settings(conn)
                if settings.get("backup_enabled"):
                    app_tz = backups.get_app_timezone()
                    now = backups.get_local_now()
                    now_time_str = now.strftime("%H:%M")
                    target_time = settings.get("auto_backup_time", "03:00")
                    last_backup_str = settings.get("last_backup_at")
                    freq = settings.get("backup_frequency", "daily")

                    last_backup_dt = None
                    if last_backup_str:
                        try:
                            last_backup_dt = datetime.datetime.strptime(last_backup_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=app_tz)
                        except Exception:
                            pass

                    should_backup = False
                    if freq == "hourly":
                        if not last_backup_dt or (now - last_backup_dt).total_seconds() >= 3600:
                            should_backup = True
                    elif freq == "every_6_hours":
                        if not last_backup_dt or (now - last_backup_dt).total_seconds() >= 6 * 3600:
                            should_backup = True
                    elif freq == "every_12_hours":
                        if not last_backup_dt or (now - last_backup_dt).total_seconds() >= 12 * 3600:
                            should_backup = True
                    elif freq == "weekly":
                        today_str = now.strftime("%Y-%m-%d")
                        already_backed_up_today = bool(last_backup_str and last_backup_str.startswith(today_str))
                        if now.weekday() == 0 and now_time_str == target_time and not already_backed_up_today:
                            should_backup = True
                    else:  # 'daily'
                        today_str = now.strftime("%Y-%m-%d")
                        already_backed_up_today = bool(last_backup_str and last_backup_str.startswith(today_str))
                        if now_time_str == target_time and not already_backed_up_today:
                            should_backup = True

                    if should_backup:
                        backups.create_database_backup(conn)
            finally:
                conn.close()
        except asyncio.CancelledError:
            break
        except Exception:
            pass


@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    init_db()
    scheduler_task = asyncio.create_task(backup_scheduler_loop())
    yield
    scheduler_task.cancel()
    try:
        await scheduler_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="Ausgabenplaner API",
    version=APP_VERSION,
    description="Backend API für den Ausgabenplaner",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Router Modules
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(plans.router)
app.include_router(categories.router)
app.include_router(data.router)
app.include_router(backups_router.router)
app.include_router(testsuite.router)


@app.get("/api/info")
def app_info_route():
    return {
        "app_name": "Ausgabenplaner",
        "version": APP_VERSION,
        "status": "healthy",
    }


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
