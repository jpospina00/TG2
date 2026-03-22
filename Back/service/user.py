from sqlmodel import Session, select

from errors import Duplicate, Missing
from model.user import User, UserCreate, UserUpdate


def get_users(db: Session) -> list[User]:
    return db.exec(select(User)).all()


def get_user(id: int, db: Session) -> User:
    user = db.get(User, id)
    if not user:
        raise Missing("User not found")
    return user


def get_user_by_auth0(auth0_id: str, db: Session) -> User:
    user = db.exec(select(User).where(User.auth0_id == auth0_id)).first()
    if not user:
        raise Missing("User not found")
    return user


def create_user(user: UserCreate, db: Session) -> User:
    existing = db.exec(select(User).where(User.auth0_id == user.auth0_id)).first()
    if existing:
        raise Duplicate("A user with this auth0_id already exists")
    new_user = User.model_validate(user)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def update_user(id: int, user: UserUpdate, db: Session) -> User:
    db_user = db.get(User, id)
    if not db_user:
        raise Missing("User not found")
    data = user.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(db_user, key, value)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(id: int, db: Session):
    user = db.get(User, id)
    if not user:
        raise Missing("User not found")
    db.delete(user)
    db.commit()
    return {"ok": True}