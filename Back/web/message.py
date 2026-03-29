from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from database import get_session
from model.message import MessageCreate, MessageRead
from service.message import get_conversation_messages, create_message

router = APIRouter()


@router.get("/conversation/{conversation_id}", summary="Get messages of a conversation", response_model=list[MessageRead])
def list_messages(conversation_id: int, db: Session = Depends(get_session)):
    return get_conversation_messages(conversation_id, db)


@router.post("", summary="Save a message", response_model=MessageRead, status_code=status.HTTP_201_CREATED)
def save_message(message: MessageCreate, db: Session = Depends(get_session)):
    return create_message(message, db)