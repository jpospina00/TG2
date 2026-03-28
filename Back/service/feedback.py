from sqlmodel import Session, select

from errors import Missing
from model.feedback import Feedback, FeedbackCreate


def get_conversation_feedback(conversation_id: int, db: Session) -> Feedback:
    feedback = db.exec(
        select(Feedback).where(Feedback.conversation_id == conversation_id)
    ).first()
    if not feedback:
        raise Missing("Feedback not found for this conversation")
    return feedback


def create_feedback(feedback: FeedbackCreate, db: Session) -> Feedback:
    new = Feedback.model_validate(feedback)
    db.add(new)
    db.commit()
    db.refresh(new)
    return new