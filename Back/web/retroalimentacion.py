from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from database import get_session
from errors import Missing
from model.retroalimentacion import RetroalimentacionCreate, RetroalimentacionRead
from service.retroalimentacion import crear_retroalimentacion, leer_retroalimentacion_conversacion

router = APIRouter()


@router.get("/conversacion/{conversacion_id}", summary="Retroalimentación de una conversación", response_model=RetroalimentacionRead)
def get_retroalimentacion(conversacion_id: int, db: Session = Depends(get_session)):
    try:
        return leer_retroalimentacion_conversacion(conversacion_id, db)
    except Missing as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.msg)


@router.post("", summary="Guarda la retroalimentación de una conversación", response_model=RetroalimentacionRead, status_code=status.HTTP_201_CREATED)
def post_retroalimentacion(retro: RetroalimentacionCreate, db: Session = Depends(get_session)):
    return crear_retroalimentacion(retro, db)