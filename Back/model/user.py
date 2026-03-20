from datetime import datetime
from sqlmodel import Field, SQLModel


class UserBase(SQLModel):
    auth0_id: str = Field(unique=True, index=True)
    name: str
    email: str


class User(UserBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class UserCreate(UserBase):
    pass


class UserRead(UserBase):
    id: int
    created_at: datetime


class UserUpdate(SQLModel):
    name: str | None = None
    email: str | None = None