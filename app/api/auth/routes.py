from fastapi import APIRouter

from app.api.auth.login import login
from app.api.auth.register import register
from app.schemas import Token

router = APIRouter()

router.add_api_route(
    "/api/v1/auth/register",
    register,
    methods=["POST"],
    response_model=Token,
    status_code=201,
    tags=["auth"],
)
router.add_api_route(
    "/api/v1/auth/token", login, methods=["POST"], response_model=Token, tags=["auth"]
)
