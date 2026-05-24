# model/conversation.py
# Propósito: Modelo de conversación — user_id opcional en Create (se inyecta desde JWT)
# Fecha: 2026-05-08

from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class ConversationBase(SQLModel):
    challenge_id: int = Field(foreign_key="challenge.id")


class Conversation(ConversationBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None


class ConversationCreate(ConversationBase):
    # user_id no viene del cliente — lo inyecta el router desde el JWT
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")


class ConversationRead(ConversationBase):
    id: int
    user_id: int
    started_at: datetime
    ended_at: Optional[datetime]


class ConversationUpdate(SQLModel):
    ended_at: Optional[datetime] = None