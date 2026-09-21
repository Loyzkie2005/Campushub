from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import Actor, get_current_actor
from app.database import get_db
from app.realtime import manager
from app.schemas import (
    ConversationCreate,
    ConversationOut,
    MessageCreate,
    MessageOut,
    MessagePage,
    ReadOut,
    ReadRequest,
)
from app.services import (
    create_message,
    create_or_get_direct_conversation,
    clear_conversation_messages,
    conversation_summaries,
    delete_conversation,
    mark_read,
    message_page,
    participant_actor_keys,
)

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", response_model=list[ConversationOut])
async def conversations(
    actor: Actor = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db),
) -> list[ConversationOut]:
    items = await conversation_summaries(db, actor)
    return [
        ConversationOut.model_validate(conversation).model_copy(
            update={
                "last_message": (
                    MessageOut.model_validate(last_message)
                    if last_message is not None
                    else None
                ),
                "unread_count": unread_count,
            }
        )
        for conversation, last_message, unread_count in items
    ]


@router.post("", response_model=ConversationOut)
async def create_conversation(
    payload: ConversationCreate,
    response: Response,
    actor: Actor = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db),
) -> ConversationOut:
    conversation, created = await create_or_get_direct_conversation(
        db,
        actor,
        payload.participant.actor_key,
        payload.participant.display_name,
        payload.context_key,
    )
    response.status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    result = ConversationOut.model_validate(conversation)
    if created:
        await manager.broadcast(
            [participant.actor_key for participant in conversation.participants],
            {"type": "conversation.updated", "conversation": result.model_dump(mode="json")},
        )
    return result


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_conversation(
    conversation_id: int,
    actor: Actor = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db),
) -> Response:
    actor_keys = await delete_conversation(db, conversation_id, actor.actor_key)
    await manager.broadcast(
        actor_keys,
        {"type": "conversation.deleted", "conversation_id": conversation_id},
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{conversation_id}/messages", response_model=MessagePage)
async def messages(
    conversation_id: int,
    before_id: int | None = Query(default=None, ge=1),
    limit: int = Query(default=50, ge=1, le=100),
    actor: Actor = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db),
) -> MessagePage:
    items, next_before_id = await message_page(
        db, conversation_id, actor.actor_key, before_id, limit
    )
    return MessagePage(items=items, next_before_id=next_before_id)


@router.delete(
    "/{conversation_id}/messages",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def clear_messages(
    conversation_id: int,
    actor: Actor = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db),
) -> Response:
    actor_keys = await clear_conversation_messages(
        db, conversation_id, actor.actor_key
    )
    await manager.broadcast(
        actor_keys,
        {"type": "conversation.cleared", "conversation_id": conversation_id},
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{conversation_id}/messages",
    response_model=MessageOut,
    status_code=status.HTTP_201_CREATED,
)
async def send_message(
    conversation_id: int,
    payload: MessageCreate,
    actor: Actor = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db),
) -> MessageOut:
    message, actor_keys = await create_message(db, conversation_id, actor, payload.body)
    result = MessageOut.model_validate(message)
    await manager.broadcast(
        actor_keys,
        {"type": "message.created", "message": result.model_dump(mode="json")},
    )
    await manager.broadcast(
        actor_keys,
        {
            "type": "conversation.updated",
            "conversation_id": conversation_id,
            "updated_at": result.created_at.isoformat(),
        },
    )
    return result


@router.post("/{conversation_id}/read", response_model=ReadOut)
async def read_conversation(
    conversation_id: int,
    payload: ReadRequest,
    actor: Actor = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db),
) -> ReadOut:
    participant = await mark_read(
        db, conversation_id, actor.actor_key, payload.message_id
    )
    result = ReadOut(
        conversation_id=conversation_id,
        actor_key=actor.actor_key,
        last_read_message_id=participant.last_read_message_id,
    )
    await manager.broadcast(
        await participant_actor_keys(db, conversation_id),
        {"type": "conversation.updated", "read": result.model_dump(mode="json")},
    )
    return result
