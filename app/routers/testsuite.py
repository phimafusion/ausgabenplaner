import os
import sys
import json
import re
import subprocess
import sqlite3
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.database import get_db
from app.auth import decode_access_token, require_permission

router = APIRouter(prefix="/api/admin", tags=["Testsuite"])


@router.post("/run-tests")
def run_test_suite_route(current_user: dict = Depends(require_permission("can_run_testsuite"))):
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


@router.get("/run-tests-stream")
def run_tests_stream_route(
    token: Optional[str] = None,
    conn: sqlite3.Connection = Depends(get_db),
):
    if not token:
        raise HTTPException(status_code=401, detail="Nicht authentifiziert")

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Ungültiges Token")

    username = payload.get("sub")
    user_row = conn.execute("SELECT role, can_run_testsuite FROM users WHERE username = ?", (username,)).fetchone()
    if not user_row or (user_row["role"] != "admin" and not user_row["can_run_testsuite"]):
        raise HTTPException(status_code=403, detail="Keine Berechtigung zum Ausführen der Testsuite")

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
