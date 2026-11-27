"""Sessione e utente autenticato, condivisi dagli endpoint HTTP."""

from collections.abc import AsyncIterator
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import User
from app.security import decode_token

bearer = HTTPBearer(auto_error=False)


async def session(request: Request) -> AsyncIterator[AsyncSession]:
    async with request.app.state.db.sessions() as db:
        yield db


Session = Annotated[AsyncSession, Depends(session)]


async def current_user(
    request: Request,
    db: Session,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> User:
    unauthorized = HTTPException(
        401, "Credenziali non valide", headers={"WWW-Authenticate": "Bearer"}
    )
    if credentials is None:
        raise unauthorized
    try:
        user_id = decode_token(credentials.credentials, request.app.state.settings)
    except jwt.InvalidTokenError:
        raise unauthorized from None
    user = await db.get(User, user_id)
    if user is None:
        raise unauthorized
    return user


CurrentUser = Annotated[User, Depends(current_user)]
