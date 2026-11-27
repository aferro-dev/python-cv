"""Transizioni persistenti: nessun risultato può sovrascrivere una cancellazione."""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import Job

ACTIVE = ("queued", "running", "retrying")
TERMINAL = ("succeeded", "failed", "cancelled")


async def transition(db: AsyncSession, job_id: str, status: str, **values: Any) -> bool:
    result = await db.execute(
        update(Job)
        .where(Job.id == job_id, Job.status.in_(ACTIVE))
        .values(status=status, updated_at=datetime.now(UTC), **values)
        .returning(Job.id)
    )
    changed = result.scalar_one_or_none() is not None
    await db.commit()
    return changed
