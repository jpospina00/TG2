from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from database import get_session
from errors import Missing
from model.conversation import ConversationCreate, ConversationRead
from service.conversation import (
    get_conversation, get_user_conversations,
    create_conversation, close_conversation
)

router = APIRouter()


@router.get("/user/{user_id}", summary="Get all conversations for a user", response_model=list[ConversationRead])
def list_user_conversations(user_id: int, db: Session = Depends(get_session)):
    return get_user_conversations(user_id, db)


@router.get("/{id}", summary="Get conversation by ID", response_model=ConversationRead)
def read_conversation(id: int, db: Session = Depends(get_session)):
    try:
        return get_conversation(id, db)
    except Missing as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.msg)


@router.post("", summary="Start a conversation", response_model=ConversationRead, status_code=status.HTTP_201_CREATED)
def start_conversation(conversation: ConversationCreate, db: Session = Depends(get_session)):
    return create_conversation(conversation, db)


@router.patch("/{id}/close", summary="Close a conversation", response_model=ConversationRead)
def end_conversation(id: int, db: Session = Depends(get_session)):
    try:
        return close_conversation(id, db)
    except Missing as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.msg)