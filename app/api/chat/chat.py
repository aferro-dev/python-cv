from fastapi import Request

from app.api.chat.service import answer
from app.api.dependencies import CurrentUser, Session
from app.schemas import Question


async def chat(body: Question, request: Request, user: CurrentUser, db: Session):
    return await answer(body, request, user, db)
