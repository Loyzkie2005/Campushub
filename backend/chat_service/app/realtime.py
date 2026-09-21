import asyncio
from collections import defaultdict

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, actor_key: str, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections[actor_key].add(websocket)

    async def disconnect(self, actor_key: str, websocket: WebSocket) -> None:
        async with self._lock:
            sockets = self._connections.get(actor_key)
            if sockets is None:
                return
            sockets.discard(websocket)
            if not sockets:
                self._connections.pop(actor_key, None)

    async def is_connected(self, actor_key: str) -> bool:
        async with self._lock:
            return bool(self._connections.get(actor_key))

    async def broadcast(
        self,
        actor_keys: list[str],
        event: dict[str, object],
        exclude_actor: str | None = None,
    ) -> None:
        async with self._lock:
            targets = [
                (actor_key, websocket)
                for actor_key in set(actor_keys)
                if actor_key != exclude_actor
                for websocket in self._connections.get(actor_key, set()).copy()
            ]
        stale: list[tuple[str, WebSocket]] = []
        for actor_key, websocket in targets:
            try:
                await websocket.send_json(event)
            except Exception:
                stale.append((actor_key, websocket))
        for actor_key, websocket in stale:
            await self.disconnect(actor_key, websocket)


manager = ConnectionManager()
