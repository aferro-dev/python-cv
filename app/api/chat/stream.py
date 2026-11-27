import asyncio
import json

from fastapi import Request
from fastapi.responses import StreamingResponse

from app.api.chat.service import answer
from app.api.dependencies import CurrentUser, Session
from app.schemas import Question


async def stream(body: Question, request: Request, user: CurrentUser, db: Session):
    # Buffering intenzionale: errori provider prima degli header, poi eventi SSE.
    result = await answer(body, request, user, db)

    async def events():
        yield (
            "event: sources\ndata: " + json.dumps([s.model_dump() for s in result.sources]) + "\n\n"
        )
        for start in range(0, len(result.answer), 80):
            if await request.is_disconnected():
                return
            yield (
                "event: delta\ndata: "
                + json.dumps({"text": result.answer[start : start + 80]})
                + "\n\n"
            )
            await asyncio.sleep(0)
        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
