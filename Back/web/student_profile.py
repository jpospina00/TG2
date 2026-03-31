# student_profile.py
# Propósito: Router REST para el perfil del estudiante
# Dependencias: fastapi, sqlmodel
# Fecha: 2026-03-29

from fastapi import APIRouter, HTTPException, status
from sqlmodel import Session, select
from pydantic import BaseModel
from datetime import datetime
from database import engine
from model.student_profile import StudentProfile

router = APIRouter(tags=["Student Profile"])


class StudentProfileRequest(BaseModel):
    user_id: int
    semester: str
    specialization: str
    self_assessed_level: str


@router.post("/profile", status_code=status.HTTP_201_CREATED)
def create_profile(req: StudentProfileRequest):
    """Crea o actualiza el perfil del estudiante."""
    with Session(engine) as db:
        existing = db.exec(
            select(StudentProfile).where(StudentProfile.user_id == req.user_id)
        ).first()

        if existing:
            existing.semester = req.semester
            existing.specialization = req.specialization
            existing.self_assessed_level = req.self_assessed_level
            existing.updated_at = datetime.utcnow()
            db.add(existing)
            db.commit()
            db.refresh(existing)
            return existing

        profile = StudentProfile(
            user_id=req.user_id,
            semester=req.semester,
            specialization=req.specialization,
            self_assessed_level=req.self_assessed_level,
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return profile


@router.get("/profile/user/{user_id}")
def get_profile(user_id: int):
    """Obtiene el perfil del estudiante."""
    with Session(engine) as db:
        profile = db.exec(
            select(StudentProfile).where(StudentProfile.user_id == user_id)
        ).first()

        if not profile:
            return {"has_profile": False}

        return {
            "has_profile": True,
            "semester": profile.semester,
            "specialization": profile.specialization,
            "self_assessed_level": profile.self_assessed_level,
        }