from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

from app.config import Settings

passwords = PasswordHash.recommended()


def issue_token(user_id: str, settings: Settings) -> str:
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "sub": user_id,
            "iat": now,
            "exp": now + timedelta(minutes=settings.token_minutes),
            "iss": "python-cv",
            "aud": "knowledge-api",
        },
        settings.jwt_secret.get_secret_value(),
        algorithm="HS256",
    )


def decode_token(token: str, settings: Settings) -> str:
    payload = jwt.decode(
        token,
        settings.jwt_secret.get_secret_value(),
        algorithms=["HS256"],
        issuer="python-cv",
        audience="knowledge-api",
        options={"require": ["sub", "exp", "iat"]},
    )
    return str(payload["sub"])
