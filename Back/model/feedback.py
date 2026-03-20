from datetime import datetime
from sqlmodel import Field, SQLModel


class FeedbackBase(SQLModel):
    conversation_id: int = Field(foreign_key="conversation.id")
    content: str
    completed: bool = False


class Feedback(FeedbackBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class FeedbackCreate(FeedbackBase):
    pass


class FeedbackRead(FeedbackBase):
    id: int
    created_at: datetime