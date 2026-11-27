import asyncio

from fastapi import HTTPException, Request
from sqlalchemy import select

from app.api.dependencies import Session
from app.db import User
from app.schemas import Credentials, Token
from app.security import issue_token, passwords


async def login(body: Credentials, db: Session, request: Request):
    user = await db.scalar(select(User).where(User.username == body.username))
    valid = await asyncio.to_thread(
        passwords.verify,
        body.password,
        user.password_hash if user else request.app.state.dummy_password_hash,
    )
    if not user or not valid:
        raise HTTPException(401, "Credenziali non valide", headers={"WWW-Authenticate": "Bearer"})
    return Token(access_token=issue_token(user.id, request.app.state.settings))
