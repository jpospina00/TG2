# seed.py
# Propósito: Poblar solo los módulos base en la BD
# Fecha: 2026-03-20

from sqlmodel import Session, select
from database import engine, create_db_and_tables
from model.module import Module

def seed():
    create_db_and_tables()
    with Session(engine) as db:
        existing = db.exec(select(Module)).all()
        if existing:
            print("Módulos ya existen. Omitiendo.")
            return

        empathy = Module(name="empathy")
        networking = Module(name="networking")
        db.add(empathy)
        db.add(networking)
        db.commit()
        print("Módulos creados: empathy, networking")

if __name__ == "__main__":
    seed()