from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from database import get_session
from errors import Duplicate, Missing
from model.user import UserCreate, UserRead, UserUpdate
from service.user import (
    get_users, get_user, get_user_by_auth0,
    create_user, update_user, delete_user
)

router = APIRouter()


@router.get("", summary="Get all users", response_model=list[UserRead])
def list_users(db: Session = Depends(get_session)):
    return get_users(db)


@router.get("/{id}", summary="Get user by ID", response_model=UserRead)
def read_user(id: int, db: Session = Depends(get_session)):
    try:
        return get_user(id, db)
    except Missing as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.msg)


@router.get("/auth0/{auth0_id}", summary="Get user by auth0_id", response_model=UserRead)
def read_user_auth0(auth0_id: str, db: Session = Depends(get_session)):
    try:
        return get_user_by_auth0(auth0_id, db)
    except Missing as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.msg)


@router.post("", summary="Create user from Auth0 token", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate, db: Session = Depends(get_session)):
    try:
        return create_user(user, db)
    except Duplicate as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.msg)


@router.patch("/{id}", summary="Update user", response_model=UserRead)
def modify_user(id: int, user: UserUpdate, db: Session = Depends(get_session)):
    try:
        return update_user(id, user, db)
    except Missing as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.msg)


@router.delete("/{id}", summary="Delete user")
def remove_user(id: int, db: Session = Depends(get_session)):
    try:
        return delete_user(id, db)
    except Missing as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.msg)