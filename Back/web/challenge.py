# web/challenge.py
# Propósito: Router REST para retos — soporta retos personalizados por usuario
# Dependencias: fastapi, sqlmodel, service/challenge
# Fecha: 2026-03-20

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import Optional

from database import get_session
from errors import Missing
from model.challenge import Challenge, ChallengeCreate, ChallengeRead, ChallengeUpdate
from service.challenge import (
    get_challenges, get_challenge,
    create_challenge, update_challenge, delete_challenge
)

router = APIRouter()


@router.get("", summary="Get all challenges", response_model=list[ChallengeRead])
def list_challenges(db: Session = Depends(get_session)):
    return get_challenges(db)


@router.get("/{id}", summary="Get challenge by ID", response_model=ChallengeRead)
def read_challenge(id: int, db: Session = Depends(get_session)):
    try:
        return get_challenge(id, db)
    except Missing as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.msg)


@router.get("/module/{module_id}/level/{level}", summary="Get challenges by module, level and user")
def get_challenges_by_module_and_level(
    module_id: int,
    level: str,
    user_id: Optional[int] = None,
    db: Session = Depends(get_session)
):
    """Obtiene retos — primero los personalizados del usuario, luego los globales."""
    if user_id:
        challenges = db.exec(
            select(Challenge).where(
                Challenge.module_id == module_id,
                Challenge.level == level,
                Challenge.user_id == user_id
            )
        ).all()
        if challenges:
            return challenges

    challenges = db.exec(
        select(Challenge).where(
            Challenge.module_id == module_id,
            Challenge.level == level,
            Challenge.user_id == None
        )
    ).all()
    return challenges


@router.post("", summary="Create a challenge", response_model=ChallengeRead, status_code=status.HTTP_201_CREATED)
def create_new_challenge(challenge: ChallengeCreate, db: Session = Depends(get_session)):
    return create_challenge(challenge, db)


@router.patch("/{id}", summary="Update a challenge", response_model=ChallengeRead)
def modify_challenge(id: int, challenge: ChallengeUpdate, db: Session = Depends(get_session)):
    try:
        return update_challenge(id, challenge, db)
    except Missing as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.msg)


@router.delete("/{id}", summary="Delete a challenge")
def remove_challenge(id: int, db: Session = Depends(get_session)):
    try:
        return delete_challenge(id, db)
    except Missing as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.msg)