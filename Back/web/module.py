from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from database import get_session
from errors import Missing
from model.module import ModuleRead
from service.module import get_modules, get_module

router = APIRouter()


@router.get("", summary="Get all modules", response_model=list[ModuleRead])
def list_modules(db: Session = Depends(get_session)):
    return get_modules(db)


@router.get("/{id}", summary="Get module by ID", response_model=ModuleRead)
def read_module(id: int, db: Session = Depends(get_session)):
    try:
        return get_module(id, db)
    except Missing as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.msg)