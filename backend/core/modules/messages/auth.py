"""JWT bridge between Django identities and the FastAPI chat service."""

from datetime import datetime, timedelta, timezone

import jwt
from django.conf import settings


def create_chat_token(*, actor_key: str, display_name: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    lifetime = timedelta(
        seconds=getattr(settings, "CHAT_TOKEN_LIFETIME_SECONDS", 43200)
    )
    payload = {
        "sub": actor_key,
        "name": display_name or actor_key,
        "role": role or "User",
        "iat": now,
        "exp": now + lifetime,
        "iss": "campushub-django",
        "aud": "campushub-chat",
    }
    return jwt.encode(
        payload,
        settings.CHAT_JWT_SECRET,
        algorithm=settings.CHAT_JWT_ALGORITHM,
    )


def mobile_chat_token(user) -> str:
    name = f"{user.first_name} {user.last_name}".strip() or user.username
    role = (getattr(user, "user_type", "") or "Student").title()
    return create_chat_token(
        actor_key=f"mobile:{user.id}",
        display_name=name,
        role=role,
    )


def admin_chat_token(user) -> str:
    name = user.get_full_name().strip() or user.username
    return create_chat_token(
        actor_key=f"admin:{user.id}",
        display_name=name,
        role=user.role or "Admin",
    )
