from sqlmodel import Session, select

from errors import Missing
from model.module import Module


def get_modules(db: Session) -> list[Module]:
    return db.exec(select(Module)).all()


def get_module(id: int, db: Session) -> Module:
    module = db.get(Module, id)
    if not module:
        raise Missing("Module not found")
    return module