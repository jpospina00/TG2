# conversation.py
# Propósito: Endpoints de conversaciones — user_id extraído del token JWT
# Fecha: 2026-05-08

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from database import get_session
from errors import Missing
from model.conversation import Conversation, ConversationCreate, ConversationRead
from model.user import User
from service.conversation import get_conversation, create_conversation, close_conversation
from utils.auth import get_db_user

router = APIRouter()


@router.get("/user/{user_id}", response_model=list[ConversationRead])
def list_user_conversations(
    user_id: int,
    limit: int = 20,
    db: Session = Depends(get_session),
    db_user: User = Depends(get_db_user),
):
    # Validar que solo acceda a sus propias conversaciones
    if db_user.id != user_id:
        raise HTTPException(status_code=403, detail="No autorizado.")
    conversations = db.exec(
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(Conversation.started_at.desc())
        .limit(limit)
    ).all()
    return conversations


@router.get("/{id}", response_model=ConversationRead)
def read_conversation(id: int, db: Session = Depends(get_session)):
    try:
        return get_conversation(id, db)
    except Missing as exc:
        raise HTTPException(status_code=404, detail=exc.msg)


@router.post("", response_model=ConversationRead, status_code=201)
def start_conversation(
    conversation: ConversationCreate,
    db: Session = Depends(get_session),
    db_user: User = Depends(get_db_user),
):
    # Forzar que el user_id de la conversación sea el del token, no el del body
    conversation.user_id = db_user.id
    return create_conversation(conversation, db)


@router.patch("/{id}/close", response_model=ConversationRead)
def end_conversation(id: int, db: Session = Depends(get_session)):
    try:
        return close_conversation(id, db)
    except Missing as exc:
        raise HTTPException(status_code=404, detail=exc.msg)