from fastapi import Query
from sqlalchemy import select

from app.api.dependencies import CurrentUser, Session
from app.db import Job


async def list_tasks(
    user: CurrentUser,
    db: Session,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    return list(
        await db.scalars(
            select(Job)
            .where(Job.owner_id == user.id)
            .order_by(Job.created_at.desc(), Job.id)
            .limit(limit)
            .offset(offset)
        )
    )
