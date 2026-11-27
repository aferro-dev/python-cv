from fastapi import HTTPException
from sqlalchemy import text

from app.api.dependencies import Session


async def ready(db: Session):
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        raise HTTPException(503, "Database non disponibile") from None
    return {"status": "ready"}
