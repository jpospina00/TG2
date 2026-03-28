from datetime import datetime
from sqlmodel import Session, select, func

from errors import Duplicate, Missing
from model.progress import Progress, ProgressCreate, ProgressUpdate
from model.feedback import Feedback
from model.conversation import Conversation
from model.challenge import Challenge


def get_progress(id: int, db: Session) -> Progress:
    progress = db.get(Progress, id)
    if not progress:
        raise Missing("Progress record not found")
    return progress


def get_user_progress(user_id: int, db: Session) -> list[Progress]:
    return db.exec(select(Progress).where(Progress.user_id == user_id)).all()


def create_progress(progress: ProgressCreate, db: Session) -> Progress:
    existing = db.exec(
        select(Progress).where(
            Progress.user_id == progress.user_id,
            Progress.module_id == progress.module_id
        )
    ).first()
    if existing:
        raise Duplicate("Progress already exists for this user and module")
    new = Progress.model_validate(progress)
    db.add(new)
    db.commit()
    db.refresh(new)
    return new


def update_progress(id: int, progress: ProgressUpdate, db: Session) -> Progress:
    db_progress = db.get(Progress, id)
    if not db_progress:
        raise Missing("Progress record not found")
    data = progress.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(db_progress, key, value)
    db_progress.last_activity = datetime.utcnow()
    db.add(db_progress)
    db.commit()
    db.refresh(db_progress)
    return db_progress


def count_completed_challenges(progress_id: int, db: Session) -> int:
    progress = db.get(Progress, progress_id)
    if not progress:
        raise Missing("Progress record not found")
    count = db.exec(
        select(func.count(Feedback.id))
        .join(Conversation, Conversation.id == Feedback.conversation_id)
        .join(Challenge, Challenge.id == Conversation.challenge_id)
        .where(
            Conversation.user_id == progress.user_id,
            Challenge.module_id == progress.module_id,
            Challenge.level == progress.current_level,
            Feedback.completed == True
        )
    ).one()
    return count