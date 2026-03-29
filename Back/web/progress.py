from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from database import get_session
from errors import Duplicate, Missing
from model.progress import ProgressCreate, ProgressRead, ProgressUpdate
from service.progress import (
    get_progress, get_user_progress, create_progress,
    update_progress, count_completed_challenges
)

router = APIRouter()


@router.get("/user/{user_id}", summary="Get all progress for a user", response_model=list[ProgressRead])
def list_user_progress(user_id: int, db: Session = Depends(get_session)):
    return get_user_progress(user_id, db)


@router.get("/{id}", summary="Get progress by ID", response_model=ProgressRead)
def read_progress(id: int, db: Session = Depends(get_session)):
    try:
        return get_progress(id, db)
    except Missing as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.msg)


@router.get("/{id}/completed-challenges", summary="Count completed challenges at current level")
def read_completed_challenges(id: int, db: Session = Depends(get_session)):
    try:
        count = count_completed_challenges(id, db)
        return {"completed_challenges": count}
    except Missing as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.msg)


@router.post("", summary="Initialize user progress in a module", response_model=ProgressRead, status_code=status.HTTP_201_CREATED)
def init_progress(progress: ProgressCreate, db: Session = Depends(get_session)):
    try:
        return create_progress(progress, db)
    except Duplicate as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.msg)


@router.patch("/{id}", summary="Update progress level", response_model=ProgressRead)
def modify_progress(id: int, progress: ProgressUpdate, db: Session = Depends(get_session)):
    try:
        return update_progress(id, progress, db)
    except Missing as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.msg)