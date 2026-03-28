from sqlmodel import Session, select

from errors import Missing
from model.challenge import Challenge, ChallengeCreate, ChallengeUpdate


def get_challenges(db: Session) -> list[Challenge]:
    return db.exec(select(Challenge)).all()


def get_challenge(id: int, db: Session) -> Challenge:
    challenge = db.get(Challenge, id)
    if not challenge:
        raise Missing("Challenge not found")
    return challenge


def get_challenges_by_module_level(module_id: int, level: str, db: Session) -> list[Challenge]:
    return db.exec(
        select(Challenge).where(
            Challenge.module_id == module_id,
            Challenge.level == level
        )
    ).all()


def create_challenge(challenge: ChallengeCreate, db: Session) -> Challenge:
    new = Challenge.model_validate(challenge)
    db.add(new)
    db.commit()
    db.refresh(new)
    return new


def update_challenge(id: int, challenge: ChallengeUpdate, db: Session) -> Challenge:
    db_challenge = db.get(Challenge, id)
    if not db_challenge:
        raise Missing("Challenge not found")
    data = challenge.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(db_challenge, key, value)
    db.add(db_challenge)
    db.commit()
    db.refresh(db_challenge)
    return db_challenge


def delete_challenge(id: int, db: Session):
    challenge = db.get(Challenge, id)
    if not challenge:
        raise Missing("Challenge not found")
    db.delete(challenge)
    db.commit()
    return {"ok": True}