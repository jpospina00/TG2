from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from database import get_session
from errors import Missing
from model.feedback import FeedbackCreate, FeedbackRead
from service.feedback import get_conversation_feedback, create_feedback

router = APIRouter()


@router.get("/conversation/{conversation_id}", summary="Get feedback for a conversation", response_model=FeedbackRead)
def read_feedback(conversation_id: int, db: Session = Depends(get_session)):
    try:
        return get_conversation_feedback(conversation_id, db)
    except Missing as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.msg)


@router.post("", summary="Save feedback for a conversation", response_model=FeedbackRead, status_code=status.HTTP_201_CREATED)
def save_feedback(feedback: FeedbackCreate, db: Session = Depends(get_session)):
    return create_feedback(feedback, db)