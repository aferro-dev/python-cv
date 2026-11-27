import asyncio

import structlog
from fastapi import HTTPException, Request, Response

from app.api.dependencies import CurrentUser, Session
from app.db import Job
from app.jobs import transition
from app.queue import publish_job
from app.schemas import Question

log = structlog.get_logger()


async def submit_task(
    body: Question, request: Request, user: CurrentUser, db: Session, response: Response
):
    job = Job(owner_id=user.id, payload=body.model_dump())
    db.add(job)
    await db.commit()  # Il worker deve poter leggere il record prima del publish.
    try:
        await asyncio.to_thread(publish_job, request.app.state.queue, job.id)
    except Exception:
        log.exception("job_publish_failed", job_id=job.id)
        await transition(db, job.id, "failed", error="Invio alla coda non riuscito")
        raise HTTPException(503, "Coda non disponibile") from None
    # Il worker potrebbe aver già terminato: rileggi lo stato autorevole.
    await db.refresh(job)
    response.headers["Location"] = f"/api/v1/tasks/{job.id}"
    return job
