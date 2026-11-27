from app.api.dependencies import CurrentUser, Session
from app.api.tasks.service import owned_job


async def get_task(job_id: str, user: CurrentUser, db: Session):
    return await owned_job(job_id, user, db)
