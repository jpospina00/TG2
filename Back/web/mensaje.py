from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from database import get_session
from errors import Missing
from model.mensaje import MensajeCreate, MensajeRead
from service.mensaje import crear_mensaje, leer_mensajes_conversacion

router = APIRouter()


@router.get("/conversacion/{conversacion_id}", summary="Mensajes de una conversación", response_model=list[MensajeRead])
def get_mensajes(conversacion_id: int, db: Session = Depends(get_session)):
    return leer_mensajes_conversacion(conversacion_id, db)


@router.post("", summary="Guarda un mensaje", response_model=MensajeRead, status_code=status.HTTP_201_CREATED)
def post_mensaje(mensaje: MensajeCreate, db: Session = Depends(get_session)):
    return crear_mensaje(mensaje, db)