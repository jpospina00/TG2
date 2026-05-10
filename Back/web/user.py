from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from database import get_session
from errors import Duplicate, Missing
from model.user import UserCreate, UserRead, UserUpdate
from service.user import (
    get_users, get_user, get_user_by_auth0,
    create_user, update_user, delete_user
)
from utils.auth import get_current_user

router = APIRouter()


@router.get("/{id}", response_model=UserRead)
def read_user(
    id: int,
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    try:
        return get_user(id, db)
    except Missing as exc:
        raise HTTPException(status_code=404, detail=exc.msg)


# Público — se llama justo después del login, antes de tener token configurado
@router.get("/auth0/{auth0_id}", response_model=UserRead)
def read_user_auth0(auth0_id: str, db: Session = Depends(get_session)):
    try:
        return get_user_by_auth0(auth0_id, db)
    except Missing as exc:
        raise HTTPException(status_code=404, detail=exc.msg)


# Público — crea el usuario la primera vez que inicia sesión
@router.post("", response_model=UserRead, status_code=201)
def register_user(user: UserCreate, db: Session = Depends(get_session)):
    try:
        return create_user(user, db)
    except Duplicate as exc:
        raise HTTPException(status_code=409, detail=exc.msg)


@router.patch("/{id}", response_model=UserRead)
def modify_user(
    id: int,
    user: UserUpdate,
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    try:
        return update_user(id, user, db)
    except Missing as exc:
        raise HTTPException(status_code=404, detail=exc.msg)


@router.delete("/{id}")
def remove_user(
    id: int,
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    try:
        return delete_user(id, db)
    except Missing as exc:
        raise HTTPException(status_code=404, detail=exc.msg)