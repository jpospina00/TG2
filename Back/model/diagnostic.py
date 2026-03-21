# diagnostic.py
# Propósito: Modelo para guardar resultados del test diagnóstico por usuario y módulo
# Dependencias: sqlmodel
# Fecha: 2026-03-20

from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field

class Diagnostic(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    module_id: int = Field(foreign_key="module.id")
    level_result: str  # beginner, intermediate, advanced
    multiple_choice_score: int  # 0-3 respuestas correctas
    written_response: str  # respuesta libre del usuario
    written_feedback: str  # feedback de la IA sobre la respuesta
    strengths: str  # fortalezas detectadas
    weaknesses: str  # debilidades detectadas
    created_at: datetime = Field(default_factory=datetime.utcnow)