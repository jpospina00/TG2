# message.py
# Propósito: Router REST para mensajes — ownership validado via conversación
# Fecha: 2026-05-08

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from model.user import User
from model.conversation import Conversation
from database import get_session
from model.message import MessageCreate, MessageRead
from service.message import get_conversation_messages, create_message
from utils.auth import get_db_user

router = APIRouter()


@router.get("/conversation/{conversation_id}", response_model=list[MessageRead])
def list_messages(
    conversation_id: int,
    db: Session = Depends(get_session),
    db_user: User = Depends(get_db_user),
):
    # Verificar que la conversación pertenece al usuario
    conv = db.get(Conversation, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversación no encontrada.")
    if conv.user_id != db_user.id:
        raise HTTPException(status_code=403, detail="No autorizado.")
    return get_conversation_messages(conversation_id, db)


@router.post("", response_model=MessageRead, status_code=201)
def save_message(
    message: MessageCreate,
    db: Session = Depends(get_session),
    db_user: User = Depends(get_db_user),
):
    # Verificar que la conversación pertenece al usuario
    conv = db.get(Conversation, message.conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversación no encontrada.")
    if conv.user_id != db_user.id:
        raise HTTPException(status_code=403, detail="No autorizado.")
    return create_message(message, db)