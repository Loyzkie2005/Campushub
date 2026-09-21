from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ParticipantCreate(BaseModel):
    actor_key: str = Field(min_length=3, max_length=255)
    display_name: str = Field(min_length=1, max_length=255)

    @field_validator("actor_key")
    @classmethod
    def namespaced_actor_key(cls, value: str) -> str:
        value = value.strip()
        if ":" not in value or any(part == "" for part in value.split(":", 1)):
            raise ValueError("actor_key must be namespaced, for example mobile:24")
        return value

    @field_validator("display_name")
    @classmethod
    def clean_display_name(cls, value: str) -> str:
        return value.strip()


class ConversationCreate(BaseModel):
    participant: ParticipantCreate
    context_key: str | None = Field(default=None, max_length=128)

    @field_validator("context_key")
    @classmethod
    def clean_context_key(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class ParticipantOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    actor_key: str
    display_name: str
    last_read_message_id: int | None


class MessageCreate(BaseModel):
    body: str = Field(min_length=1, max_length=2000)

    @field_validator("body")
    @classmethod
    def nonblank_body(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("body must not be blank")
        return value


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    conversation_id: int
    sender_actor_key: str
    sender_name: str
    body: str
    created_at: datetime


class ConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    participants: list[ParticipantOut]
    created_at: datetime
    updated_at: datetime
    last_message: MessageOut | None = None
    unread_count: int = 0


class MessagePage(BaseModel):
    items: list[MessageOut]
    next_before_id: int | None


class ReadRequest(BaseModel):
    message_id: int | None = Field(default=None, ge=1)


class ReadOut(BaseModel):
    conversation_id: int
    actor_key: str
    last_read_message_id: int | None


class WebSocketAuth(BaseModel):
    type: str
    token: str


class WebSocketCommand(BaseModel):
    type: str
    conversation_id: int = Field(ge=1)
    body: str | None = Field(default=None, max_length=2000)
    message_id: int | None = Field(default=None, ge=1)
