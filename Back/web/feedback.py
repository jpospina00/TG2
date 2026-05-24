# feedback.py
# Propósito: Router REST para feedback — ownership validado via conversación
# Fecha: 2026-05-08

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from model.user import User
from model.conversation import Conversation
from database import get_session
from errors import Missing
from model.feedback import FeedbackCreate, FeedbackRead
from service.feedback import get_conversation_feedback, create_feedback
from utils.auth import get_db_user

router = APIRouter()


@router.get("/conversation/{conversation_id}", response_model=FeedbackRead)
def read_feedback(
    conversation_id: int,
    db: Session = Depends(get_session),
    db_user: User = Depends(get_db_user),
):
    conv = db.get(Conversation, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversación no encontrada.")
    if conv.user_id != db_user.id:
        raise HTTPException(status_code=403, detail="No autorizado.")
    try:
        return get_conversation_feedback(conversation_id, db)
    except Missing as exc:
        raise HTTPException(status_code=404, detail=exc.msg)


@router.post("", response_model=FeedbackRead, status_code=201)
def save_feedback(
    feedback: FeedbackCreate,
    db: Session = Depends(get_session),
    db_user: User = Depends(get_db_user),
):
    conv = db.get(Conversation, feedback.conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversación no encontrada.")
    if conv.user_id != db_user.id:
        raise HTTPException(status_code=403, detail="No autorizado.")
    return create_feedback(feedback, db)