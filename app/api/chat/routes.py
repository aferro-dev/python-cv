from fastapi import APIRouter

from app.api.chat.chat import chat
from app.api.chat.stream import stream
from app.schemas import Answer

router = APIRouter()

router.add_api_route("/api/v1/chat", chat, methods=["POST"], response_model=Answer, tags=["rag"])
router.add_api_route("/api/v1/chat/stream", stream, methods=["POST"], tags=["rag"])
