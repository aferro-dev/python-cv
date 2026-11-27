import asyncio

from fastapi import HTTPException, Request
from sqlalchemy.exc import IntegrityError

from app.api.dependencies import Session
from app.db import User
from app.schemas import Credentials, Token
from app.security import issue_token, passwords


async def register(body: Credentials, db: Session, request: Request):
    hashed = await asyncio.to_thread(passwords.hash, body.password)
    user = User(username=body.username, password_hash=hashed)
    db.add(user)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(409, "Username già registrato") from None
    return Token(access_token=issue_token(user.id, request.app.state.settings))
