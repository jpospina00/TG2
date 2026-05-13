# student_profile.py
# Propósito: Router REST para el perfil del estudiante — user_id desde JWT
# Dependencias: fastapi, sqlmodel
# Fecha: 2026-05-08

from fastapi import APIRouter, HTTPException, status, Depends
from sqlmodel import Session, select
from pydantic import BaseModel
from datetime import datetime
from database import get_session
from model.student_profile import StudentProfile
from model.user import User
from utils.auth import get_db_user

router = APIRouter(tags=["Student Profile"])


class StudentProfileRequest(BaseModel):
    # user_id ya NO viene del cliente — se extrae del JWT con get_db_user
    semester: str
    specialization: str
    self_assessed_level: str


@router.post("/profile", status_code=status.HTTP_201_CREATED)
def create_profile(
    req: StudentProfileRequest,
    db: Session = Depends(get_session),
    db_user: User = Depends(get_db_user),
):
    user_id = db_user.id

    existing = db.exec(
        select(StudentProfile).where(StudentProfile.user_id == user_id)
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
        user_id=user_id,
        semester=req.semester,
        specialization=req.specialization,
        self_assessed_level=req.self_assessed_level,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/profile/user/{user_id}")
def get_profile(
    user_id: int,
    db: Session = Depends(get_session),
    db_user: User = Depends(get_db_user),
):
    # Solo puede ver su propio perfil
    if db_user.id != user_id:
        raise HTTPException(status_code=403, detail="No autorizado.")

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