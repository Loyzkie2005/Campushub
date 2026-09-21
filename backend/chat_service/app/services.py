import hashlib
import json

from fastapi import HTTPException, status
from datetime import datetime, timezone

from sqlalchemy import Select, delete, desc, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import Actor
from app.models import Conversation, Message, Participant


def direct_key(
    first_actor_key: str,
    second_actor_key: str,
    context_key: str | None = None,
) -> str:
    if not context_key:
        pair = json.dumps(
            sorted((first_actor_key, second_actor_key)), separators=(",", ":")
        )
        return hashlib.sha256(pair.encode("utf-8")).hexdigest()

    identity = {
        "actors": sorted((first_actor_key, second_actor_key)),
        "context": context_key,
    }
    payload = json.dumps(identity, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


async def participant_for(
    db: AsyncSession, conversation_id: int, actor_key: str
) -> Participant:
    participant = await db.scalar(
        select(Participant).where(
            Participant.conversation_id == conversation_id,
            Participant.actor_key == actor_key,
        )
    )
    if participant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found or access denied",
        )
    return participant


async def conversation_for_actor(
    db: AsyncSession, conversation_id: int, actor_key: str
) -> Conversation:
    await participant_for(db, conversation_id, actor_key)
    conversation = await db.scalar(
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .options(selectinload(Conversation.participants))
    )
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


async def list_conversations(
    db: AsyncSession, actor_key: str
) -> list[Conversation]:
    result = await db.scalars(
        select(Conversation)
        .join(Participant)
        .where(
            Participant.actor_key == actor_key,
            Participant.hidden_at.is_(None),
        )
        .options(selectinload(Conversation.participants))
        .order_by(desc(Conversation.updated_at), desc(Conversation.id))
    )
    return list(result.unique())


async def conversation_summaries(
    db: AsyncSession, actor: Actor
) -> list[tuple[Conversation, Message | None, int]]:
    actor_key = actor.actor_key
    conversations = await list_conversations(db, actor_key)
    summaries: list[tuple[Conversation, Message | None, int]] = []
    participant_name_changed = False
    for conversation in conversations:
        own_participant = next(
            participant
            for participant in conversation.participants
            if participant.actor_key == actor_key
        )
        if own_participant.display_name != actor.name:
            own_participant.display_name = actor.name
            participant_name_changed = True
        last_message = await db.scalar(
            select(Message)
            .where(Message.conversation_id == conversation.id)
            .order_by(desc(Message.id))
            .limit(1)
        )
        unread_statement = select(func.count(Message.id)).where(
            Message.conversation_id == conversation.id,
            Message.sender_actor_key != actor_key,
        )
        if own_participant.last_read_message_id is not None:
            unread_statement = unread_statement.where(
                Message.id > own_participant.last_read_message_id
            )
        unread_count = int(await db.scalar(unread_statement) or 0)
        summaries.append((conversation, last_message, unread_count))
    if participant_name_changed:
        await db.commit()
    return summaries


async def delete_conversation(
    db: AsyncSession, conversation_id: int, actor_key: str
) -> list[str]:
    participant = await participant_for(db, conversation_id, actor_key)
    participant.hidden_at = datetime.now(timezone.utc)
    await db.commit()
    return [actor_key]


async def clear_conversation_messages(
    db: AsyncSession, conversation_id: int, actor_key: str
) -> list[str]:
    conversation = await conversation_for_actor(db, conversation_id, actor_key)
    for participant in conversation.participants:
        participant.last_read_message_id = None
    await db.execute(
        delete(Message).where(Message.conversation_id == conversation_id)
    )
    conversation.updated_at = datetime.now(timezone.utc)
    actor_keys = [
        participant.actor_key for participant in conversation.participants
    ]
    await db.commit()
    return actor_keys


async def refresh_participant_names(
    db: AsyncSession,
    conversation: Conversation,
    actor: Actor,
    other_actor_key: str,
    other_display_name: str,
) -> None:
    expected_names = {
        actor.actor_key: actor.name,
        other_actor_key: other_display_name,
    }
    changed = False
    for participant in conversation.participants:
        expected = expected_names.get(participant.actor_key)
        if expected and participant.display_name != expected:
            participant.display_name = expected
            changed = True
    if changed:
        await db.commit()


async def create_or_get_direct_conversation(
    db: AsyncSession,
    actor: Actor,
    other_actor_key: str,
    other_display_name: str,
    context_key: str | None = None,
) -> tuple[Conversation, bool]:
    if actor.actor_key == other_actor_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A direct conversation requires another participant",
        )
    key = direct_key(actor.actor_key, other_actor_key, context_key)
    existing = await db.scalar(
        select(Conversation)
        .where(Conversation.direct_key == key)
        .options(selectinload(Conversation.participants))
    )
    if existing is not None:
        own_participant = next(
            participant
            for participant in existing.participants
            if participant.actor_key == actor.actor_key
        )
        own_participant.hidden_at = None
        await refresh_participant_names(
            db, existing, actor, other_actor_key, other_display_name
        )
        await db.commit()
        return existing, False

    conversation = Conversation(direct_key=key)
    conversation.participants = [
        Participant(actor_key=actor.actor_key, display_name=actor.name),
        Participant(actor_key=other_actor_key, display_name=other_display_name),
    ]
    db.add(conversation)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        existing = await db.scalar(
            select(Conversation)
            .where(Conversation.direct_key == key)
            .options(selectinload(Conversation.participants))
        )
        if existing is None:
            raise
        await refresh_participant_names(
            db, existing, actor, other_actor_key, other_display_name
        )
        return existing, False

    created = await db.scalar(
        select(Conversation)
        .where(Conversation.id == conversation.id)
        .options(selectinload(Conversation.participants))
    )
    return created or conversation, True


async def create_message(
    db: AsyncSession, conversation_id: int, actor: Actor, body: str
) -> tuple[Message, list[str]]:
    conversation = await conversation_for_actor(db, conversation_id, actor.actor_key)
    # A new message restores a thread that either participant previously hid.
    for participant in conversation.participants:
        participant.hidden_at = None
    message = Message(
        conversation_id=conversation_id,
        sender_actor_key=actor.actor_key,
        sender_name=actor.name,
        body=body,
    )
    db.add(message)
    await db.flush()
    # Use the database timestamp if one was generated server-side.
    await db.refresh(message)
    conversation.updated_at = message.created_at
    await db.commit()
    return message, [participant.actor_key for participant in conversation.participants]


async def message_page(
    db: AsyncSession,
    conversation_id: int,
    actor_key: str,
    before_id: int | None,
    limit: int,
) -> tuple[list[Message], int | None]:
    await participant_for(db, conversation_id, actor_key)
    statement: Select[tuple[Message]] = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(desc(Message.id))
        .limit(limit)
    )
    if before_id is not None:
        statement = statement.where(Message.id < before_id)
    messages = list(await db.scalars(statement))
    next_before_id = messages[-1].id if len(messages) == limit else None
    messages.reverse()
    return messages, next_before_id


async def mark_read(
    db: AsyncSession,
    conversation_id: int,
    actor_key: str,
    message_id: int | None,
) -> Participant:
    participant = await participant_for(db, conversation_id, actor_key)
    if message_id is None:
        message_id = await db.scalar(
            select(Message.id)
            .where(Message.conversation_id == conversation_id)
            .order_by(desc(Message.id))
            .limit(1)
        )
    elif not await db.scalar(
        select(Message.id).where(
            Message.id == message_id, Message.conversation_id == conversation_id
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message does not belong to this conversation",
        )

    if message_id is not None and (
        participant.last_read_message_id is None
        or message_id > participant.last_read_message_id
    ):
        participant.last_read_message_id = message_id
        await db.commit()
    return participant


async def participant_actor_keys(
    db: AsyncSession, conversation_id: int
) -> list[str]:
    return list(
        await db.scalars(
            select(Participant.actor_key).where(
                Participant.conversation_id == conversation_id
            )
        )
    )
