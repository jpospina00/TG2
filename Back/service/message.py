from sqlmodel import Session, select

from model.message import Message, MessageCreate


def get_conversation_messages(conversation_id: int, db: Session) -> list[Message]:
    return db.exec(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.order)
    ).all()


def create_message(message: MessageCreate, db: Session) -> Message:
    new = Message.model_validate(message)
    db.add(new)
    db.commit()
    db.refresh(new)
    return new