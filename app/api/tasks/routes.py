from fastapi import APIRouter

from app.api.tasks.cancel import cancel_task
from app.api.tasks.list import list_tasks
from app.api.tasks.read import get_task
from app.api.tasks.submit import submit_task
from app.schemas import JobRead

router = APIRouter()

router.add_api_route(
    "/api/v1/tasks",
    submit_task,
    methods=["POST"],
    response_model=JobRead,
    status_code=202,
    tags=["tasks"],
)
router.add_api_route(
    "/api/v1/tasks", list_tasks, methods=["GET"], response_model=list[JobRead], tags=["tasks"]
)
router.add_api_route(
    "/api/v1/tasks/{job_id}", get_task, methods=["GET"], response_model=JobRead, tags=["tasks"]
)
router.add_api_route(
    "/api/v1/tasks/{job_id}",
    cancel_task,
    methods=["DELETE"],
    response_model=JobRead,
    tags=["tasks"],
)
