# student_profile.py
# Propósito: Perfil del estudiante para personalizar los retos
# Dependencias: sqlmodel
# Fecha: 2026-03-29

from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field


class StudentProfile(SQLModel, table=True):
    __tablename__ = "student_profile"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True)
    semester: str                    # "1" a "10"
    specialization: str              # "ai", "backend", "frontend", "devops", "data", "security", "mobile", "other"
    self_assessed_level: str         # "beginner", "intermediate", "advanced"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)