# challenge.py
# Propósito: Router REST para retos — user_id desde JWT en consultas personalizadas
# Fecha: 2026-05-08

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from model.user import User
from database import get_session
from errors import Missing
from model.challenge import Challenge, ChallengeCreate, ChallengeRead, ChallengeUpdate
from service.challenge import (
    get_challenges, get_challenge,
    create_challenge, update_challenge, delete_challenge
)
from utils.auth import get_db_user

router = APIRouter()


@router.get("", response_model=list[ChallengeRead])
def list_challenges(db: Session = Depends(get_session)):
    return get_challenges(db)


@router.get("/{id}", response_model=ChallengeRead)
def read_challenge(id: int, db: Session = Depends(get_session)):
    try:
        return get_challenge(id, db)
    except Missing as exc:
        raise HTTPException(status_code=404, detail=exc.msg)


@router.get("/module/{module_id}/level/{level}")
def get_challenges_by_module_and_level(
    module_id: int,
    level: str,
    db: Session = Depends(get_session),
    db_user: User = Depends(get_db_user),
):
    """Obtiene retos personalizados del usuario; si no hay, devuelve los globales."""
    # user_id desde el token — nunca desde query param
    user_id = db_user.id
    challenges = db.exec(
        select(Challenge).where(
            Challenge.module_id == module_id,
            Challenge.level == level,
            Challenge.user_id == user_id
        )
    ).all()
    if challenges:
        return challenges

    # Fallback a retos globales
    challenges = db.exec(
        select(Challenge).where(
            Challenge.module_id == module_id,
            Challenge.level == level,
            Challenge.user_id == None
        )
    ).all()
    return challenges


@router.post("", response_model=ChallengeRead, status_code=201)
def create_new_challenge(challenge: ChallengeCreate, db: Session = Depends(get_session)):
    return create_challenge(challenge, db)


@router.patch("/{id}", response_model=ChallengeRead)
def modify_challenge(id: int, challenge: ChallengeUpdate, db: Session = Depends(get_session)):
    try:
        return update_challenge(id, challenge, db)
    except Missing as exc:
        raise HTTPException(status_code=404, detail=exc.msg)


@router.delete("/{id}")
def remove_challenge(id: int, db: Session = Depends(get_session)):
    try:
        return delete_challenge(id, db)
    except Missing as exc:
        raise HTTPException(status_code=404, detail=exc.msg)