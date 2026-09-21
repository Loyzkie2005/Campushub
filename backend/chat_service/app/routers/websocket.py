import asyncio

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from app.auth import Actor, decode_token
from app.config import get_settings
from app.database import SessionLocal
from app.realtime import manager
from app.schemas import MessageCreate, MessageOut, ReadOut, WebSocketAuth, WebSocketCommand
from app.services import (
    create_message,
    mark_read,
    participant_actor_keys,
    participant_for,
)

router = APIRouter(tags=["websocket"])


async def send_error(
    websocket: WebSocket, code: str, detail: str, request_type: str | None = None
) -> None:
    event: dict[str, object] = {"type": "error", "code": code, "detail": detail}
    if request_type:
        event["request_type"] = request_type
    await websocket.send_json(event)


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    settings = get_settings()
    origin = websocket.headers.get("origin")
    if origin and "*" not in settings.allowed_origins and origin not in settings.allowed_origins:
        await websocket.close(code=1008, reason="Origin not allowed")
        return

    actor: Actor | None = None
    try:
        try:
            raw_auth = await asyncio.wait_for(
                websocket.receive_json(),
                timeout=settings.websocket_auth_timeout_seconds,
            )
            auth_event = WebSocketAuth.model_validate(raw_auth)
            if auth_event.type != "auth":
                raise ValueError("First event must have type 'auth'")
            actor = decode_token(auth_event.token)
        except asyncio.TimeoutError:
            await websocket.close(code=1008, reason="Authentication timeout")
            return
        except (ValidationError, ValueError, HTTPException):
            await websocket.close(code=1008, reason="Authentication failed")
            return

        await manager.connect(actor.actor_key, websocket)
        await websocket.send_json(
            {
                "type": "auth.ok",
                "actor": {
                    "actor_key": actor.actor_key,
                    "name": actor.name,
                    "role": actor.role,
                },
            }
        )

        async with SessionLocal() as db:
            while True:
                raw_command = await websocket.receive_json()
                try:
                    command = WebSocketCommand.model_validate(raw_command)
                    await participant_for(
                        db, command.conversation_id, actor.actor_key
                    )

                    if command.type == "message.send":
                        payload = MessageCreate(body=command.body)
                        message, actor_keys = await create_message(
                            db, command.conversation_id, actor, payload.body
                        )
                        result = MessageOut.model_validate(message)
                        await manager.broadcast(
                            actor_keys,
                            {
                                "type": "message.created",
                                "message": result.model_dump(mode="json"),
                            },
                        )
                        await manager.broadcast(
                            actor_keys,
                            {
                                "type": "conversation.updated",
                                "conversation_id": command.conversation_id,
                                "updated_at": result.created_at.isoformat(),
                            },
                        )
                    elif command.type in {"typing.start", "typing.stop"}:
                        await manager.broadcast(
                            await participant_actor_keys(db, command.conversation_id),
                            {
                                "type": command.type,
                                "conversation_id": command.conversation_id,
                                "actor_key": actor.actor_key,
                                "name": actor.name,
                            },
                            exclude_actor=actor.actor_key,
                        )
                    elif command.type == "conversation.read":
                        participant = await mark_read(
                            db,
                            command.conversation_id,
                            actor.actor_key,
                            command.message_id,
                        )
                        read = ReadOut(
                            conversation_id=command.conversation_id,
                            actor_key=actor.actor_key,
                            last_read_message_id=participant.last_read_message_id,
                        )
                        await manager.broadcast(
                            await participant_actor_keys(db, command.conversation_id),
                            {
                                "type": "conversation.updated",
                                "read": read.model_dump(mode="json"),
                            },
                        )
                    else:
                        await send_error(
                            websocket,
                            "unsupported_type",
                            "Unsupported command type",
                            command.type,
                        )
                except ValidationError as exc:
                    await send_error(
                        websocket, "validation_error", str(exc.errors()[0]["msg"])
                    )
                except HTTPException as exc:
                    await db.rollback()
                    await send_error(websocket, "forbidden", str(exc.detail))
    except WebSocketDisconnect:
        pass
    finally:
        if actor is not None:
            await manager.disconnect(actor.actor_key, websocket)
