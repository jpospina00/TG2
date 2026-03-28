from datetime import datetime
from sqlmodel import Session, select

from errors import Missing
from model.conversation import Conversation, ConversationCreate


def get_conversation(id: int, db: Session) -> Conversation:
    conv = db.get(Conversation, id)
    if not conv:
        raise Missing("Conversation not found")
    return conv


def get_user_conversations(user_id: int, db: Session) -> list[Conversation]:
    return db.exec(select(Conversation).where(Conversation.user_id == user_id)).all()


def create_conversation(conversation: ConversationCreate, db: Session) -> Conversation:
    new = Conversation.model_validate(conversation)
    db.add(new)
    db.commit()
    db.refresh(new)
    return new


def close_conversation(id: int, db: Session) -> Conversation:
    conv = db.get(Conversation, id)
    if not conv:
        raise Missing("Conversation not found")
    conv.ended_at = datetime.utcnow()
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv