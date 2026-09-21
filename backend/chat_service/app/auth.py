from dataclasses import dataclass

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError

from app.config import get_settings


@dataclass(frozen=True)
class Actor:
    actor_key: str
    name: str
    role: str


bearer = HTTPBearer(auto_error=False)


def decode_token(token: str) -> Actor:
    settings = get_settings()
    try:
        claims = jwt.decode(
            token,
            settings.chat_jwt_secret,
            algorithms=["HS256"],
            issuer=settings.chat_jwt_issuer,
            audience=settings.chat_jwt_audience,
            options={"require": ["sub", "name", "role", "exp", "iss", "aud"]},
        )
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    subject = claims.get("sub")
    name = claims.get("name")
    role = claims.get("role")
    if not all(isinstance(value, str) and value.strip() for value in (subject, name, role)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token claims must be non-empty strings",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if ":" not in subject or len(subject) > 255:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token subject must be a namespaced actor key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Actor(subject, name[:255], role)


async def get_current_actor(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> Actor:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decode_token(credentials.credentials)
