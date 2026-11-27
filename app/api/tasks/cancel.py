from app.api.dependencies import CurrentUser, Session
from app.api.tasks.service import owned_job
from app.jobs import ACTIVE, transition


async def cancel_task(job_id: str, user: CurrentUser, db: Session):
    job = await owned_job(job_id, user, db)
    if job.status in ACTIVE:
        await transition(db, job.id, "cancelled", error=None)
        await db.refresh(job)
    # Cancellazione logica persistente; niente terminate=True su processi condivisi.
    return job
