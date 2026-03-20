from datetime import datetime
from sqlmodel import Field, SQLModel


class ProgressBase(SQLModel):
    user_id: int = Field(foreign_key="user.id")
    module_id: int = Field(foreign_key="module.id")
    current_level: str = "beginner"


class Progress(ProgressBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    last_activity: datetime = Field(default_factory=datetime.utcnow)


class ProgressCreate(ProgressBase):
    pass


class ProgressRead(ProgressBase):
    id: int
    last_activity: datetime


class ProgressUpdate(SQLModel):
    current_level: str | None = None
    last_activity: datetime | None = None