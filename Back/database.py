from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import NullPool, QueuePool
from config import settings

is_sqlite = settings.active_database_uri.startswith("sqlite")

connect_args = {}
if is_sqlite:
    connect_args = {"check_same_thread": False}
elif "neon.tech" in settings.active_database_uri:
    connect_args = {"sslmode": "require"}

# Neon.tech cierra conexiones inactivas después de ~5 min.
# pool_pre_ping=True verifica la conexión antes de cada uso y reconecta si fue cerrada.
# pool_recycle evita usar conexiones más antiguas que 5 minutos.
if is_sqlite:
    engine = create_engine(
        settings.active_database_uri,
        echo=False,
        connect_args=connect_args,
    )
else:
    engine = create_engine(
        settings.active_database_uri,
        echo=False,
        connect_args=connect_args,
        pool_pre_ping=True,
        pool_recycle=240,      # recicla conexiones cada 4 min (antes del cierre de Neon)
        pool_size=5,
        max_overflow=2,
    )

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session