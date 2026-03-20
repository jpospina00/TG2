from datetime import datetime
from sqlmodel import Field, SQLModel


class ConversationBase(SQLModel):
    user_id: int = Field(foreign_key="user.id")
    challenge_id: int = Field(foreign_key="challenge.id")


class Conversation(ConversationBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: datetime | None = None


class ConversationCreate(ConversationBase):
    pass


class ConversationRead(ConversationBase):
    id: int
    started_at: datetime
    ended_at: datetime | None


class ConversationUpdate(SQLModel):
    ended_at: datetime | None = None