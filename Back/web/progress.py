# progress.py
# Propósito: Router REST para progreso del usuario — validación de ownership
# Fecha: 2026-05-08

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from model.user import User
from database import get_session
from errors import Duplicate, Missing
from model.progress import ProgressCreate, ProgressRead, ProgressUpdate
from service.progress import (
    get_progress, get_user_progress, create_progress,
    update_progress, count_completed_challenges
)
from utils.auth import get_db_user

router = APIRouter()


@router.get("/user/{user_id}", response_model=list[ProgressRead])
def list_user_progress(
    user_id: int,
    db: Session = Depends(get_session),
    db_user: User = Depends(get_db_user),
):
    if db_user.id != user_id:
        raise HTTPException(status_code=403, detail="No autorizado.")
    return get_user_progress(user_id, db)


@router.get("/{id}", response_model=ProgressRead)
def read_progress(id: int, db: Session = Depends(get_session)):
    try:
        return get_progress(id, db)
    except Missing as exc:
        raise HTTPException(status_code=404, detail=exc.msg)


@router.get("/{id}/completed-challenges")
def read_completed_challenges(id: int, db: Session = Depends(get_session)):
    try:
        count = count_completed_challenges(id, db)
        return {"completed_challenges": count}
    except Missing as exc:
        raise HTTPException(status_code=404, detail=exc.msg)


@router.post("", response_model=ProgressRead, status_code=201)
def init_progress(
    progress: ProgressCreate,
    db: Session = Depends(get_session),
    db_user: User = Depends(get_db_user),
):
    # Forzar que el user_id sea siempre el del token
    progress.user_id = db_user.id
    try:
        return create_progress(progress, db)
    except Duplicate as exc:
        raise HTTPException(status_code=409, detail=exc.msg)


@router.patch("/{id}", response_model=ProgressRead)
def modify_progress(id: int, progress: ProgressUpdate, db: Session = Depends(get_session)):
    try:
        return update_progress(id, progress, db)
    except Missing as exc:
        raise HTTPException(status_code=404, detail=exc.msg)