# challenge.py
# Propósito: Modelo de reto — puede ser global (user_id=None) o personalizado por usuario
# Dependencias: sqlmodel
# Fecha: 2026-03-20

from sqlmodel import SQLModel, Field
from typing import Optional


class ChallengeBase(SQLModel):
    module_id: int = Field(foreign_key="module.id")
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    level: str
    type: str
    agent_profile: str
    context: str
    opening_message: str


class Challenge(ChallengeBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)


class ChallengeCreate(ChallengeBase):
    pass


class ChallengeRead(ChallengeBase):
    id: int


class ChallengeUpdate(SQLModel):
    agent_profile: Optional[str] = None
    context: Optional[str] = None
    opening_message: Optional[str] = None