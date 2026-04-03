from sqlmodel import Session, SQLModel, create_engine
from config import settings

is_sqlite = settings.active_database_uri.startswith("sqlite")

connect_args = {}
if is_sqlite:
    connect_args = {"check_same_thread": False}
elif "neon.tech" in settings.active_database_uri:
    connect_args = {"sslmode": "require"}

engine = create_engine(
    settings.active_database_uri,
    echo=False,
    connect_args=connect_args
)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session