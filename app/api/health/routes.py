from fastapi import APIRouter

from app.api.health.live import live
from app.api.health.metrics import metrics
from app.api.health.ready import ready
from app.api.health.root import root

router = APIRouter()

router.add_api_route("/", root, methods=["GET"], tags=["health"])
router.add_api_route("/health/live", live, methods=["GET"], tags=["health"])
router.add_api_route("/health/ready", ready, methods=["GET"], tags=["health"])
router.add_api_route("/metrics", metrics, methods=["GET"], include_in_schema=False)
