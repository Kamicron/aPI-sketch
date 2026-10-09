from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app import __version__
from app.db import SessionLocal

router = APIRouter(tags=["health"])


@router.get("/api/health")
def health():
    """Sondé par PI-ng : 200 si l'API et la base répondent, 503 sinon."""
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        db_state = "up"
    except Exception:
        db_state = "down"
    body = {"status": "UP" if db_state == "up" else "DOWN", "db": db_state, "version": __version__}
    return JSONResponse(body, status_code=200 if db_state == "up" else 503)
