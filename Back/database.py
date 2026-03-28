from sqlmodel import Session, SQLModel, create_engine
from config import settings

# Seleccionar argumentos según el motor
is_sqlite = settings.active_database_uri.startswith("sqlite")
connect_args = {"check_same_thread": False} if is_sqlite else {}

engine = create_engine(
    settings.active_database_uri,
    echo=True,
    connect_args=connect_args
)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session