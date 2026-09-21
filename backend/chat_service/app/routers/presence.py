from fastapi import APIRouter, Depends

from app.auth import Actor, get_current_actor
from app.realtime import manager


router = APIRouter(prefix="/presence", tags=["presence"])


@router.get("/{actor_key}")
async def actor_presence(
    actor_key: str,
    _actor: Actor = Depends(get_current_actor),
) -> dict[str, object]:
    return {
        "actor_key": actor_key,
        "online": await manager.is_connected(actor_key),
    }
