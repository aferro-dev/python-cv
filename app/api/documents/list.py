from fastapi import Query
from sqlalchemy import select

from app.api.dependencies import CurrentUser, Session
from app.db import Document


async def list_documents(
    user: CurrentUser,
    db: Session,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    return list(
        await db.scalars(
            select(Document)
            .where(Document.owner_id == user.id)
            .order_by(Document.created_at, Document.id)
            .limit(limit)
            .offset(offset)
        )
    )
