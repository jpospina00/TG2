from datetime import datetime
from sqlmodel import Field, SQLModel


class MessageBase(SQLModel):
    conversation_id: int = Field(foreign_key="conversation.id")
    role: str
    content: str
    order: int


class Message(MessageBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MessageCreate(MessageBase):
    pass


class MessageRead(MessageBase):
    id: int
    created_at: datetime