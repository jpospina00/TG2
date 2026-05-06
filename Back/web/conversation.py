from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from database import get_session
from errors import Missing
from model.conversation import Conversation, ConversationCreate, ConversationRead
from service.conversation import (
    get_conversation,
    create_conversation,
    close_conversation
)

router = APIRouter()


@router.get("/user/{user_id}", response_model=list[ConversationRead])
def list_user_conversations(user_id: int, limit: int = 20, db: Session = Depends(get_session)):
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.msg)


@router.post("", response_model=ConversationRead, status_code=status.HTTP_201_CREATED)
def start_conversation(conversation: ConversationCreate, db: Session = Depends(get_session)):
    return create_conversation(conversation, db)


@router.patch("/{id}/close", response_model=ConversationRead)
def end_conversation(id: int, db: Session = Depends(get_session)):
    try:
        return close_conversation(id, db)
    except Missing as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.msg)