from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import Job, User


async def owned_job(job_id: str, user: User, db: AsyncSession) -> Job:
    job = await db.scalar(select(Job).where(Job.id == job_id, Job.owner_id == user.id))
    if job is None:
        raise HTTPException(404, "Task non trovato")
    return job
