# conftest.py
# Propósito: Fixtures compartidos para todos los tests
# Dependencias: pytest, fastapi, sqlmodel, httpx
# Fecha: 2026-04-25

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from main import app
from database import get_session
from model import User, Module, Challenge, Progress, Conversation, Message, Feedback
from model.diagnostic import Diagnostic
from model.student_profile import StudentProfile 
from utils.auth import get_current_user, get_db_user


# ── BD de prueba en memoria ───────────────────────────────────────────────────

@pytest.fixture(name="engine")
def engine_fixture():
    from model import (
        User, Module, Challenge, Progress,
        Conversation, Message, Feedback,
        Diagnostic, StudentProfile
    )
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)

@pytest.fixture(name="session")
def session_fixture(engine):
    """Sesión de BD para cada test."""
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session, test_user):
    """
    Cliente HTTP con BD de prueba inyectada y auth mockeada.
    get_current_user devuelve un payload JWT falso con el auth0_id del test_user.
    get_db_user devuelve el test_user directamente.
    """
    def get_session_override():
        yield session

    def get_current_user_override():
        # Simula el payload decodificado de un JWT de Auth0
        return {"sub": test_user.auth0_id, "email": test_user.email}

    def get_db_user_override():
        # Devuelve el usuario de prueba directamente sin validar token
        return test_user

    app.dependency_overrides[get_session] = get_session_override
    app.dependency_overrides[get_current_user] = get_current_user_override
    app.dependency_overrides[get_db_user] = get_db_user_override

    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


# ── Datos base reutilizables ──────────────────────────────────────────────────

@pytest.fixture(name="test_user")
def test_user_fixture(session):
    """Usuario de prueba."""
    user = User(
        auth0_id="auth0|test123",
        name="Test User",
        email="test@test.com"
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture(name="test_modules")
def test_modules_fixture(session):
    """Módulos de prueba (empathy y networking)."""
    empathy = Module(name="empathy")
    networking = Module(name="networking")
    session.add(empathy)
    session.add(networking)
    session.commit()
    session.refresh(empathy)
    session.refresh(networking)
    return {"empathy": empathy, "networking": networking}


@pytest.fixture(name="test_challenge")
def test_challenge_fixture(session, test_modules):
    """Reto de prueba."""
    challenge = Challenge(
        module_id=test_modules["empathy"].id,
        user_id=None,
        level="beginner",
        type="simple",
        agent_profile="Compañero frustrado",
        context="Proyecto grupal universitario",
        opening_message="Me siento ignorado en el grupo."
    )
    session.add(challenge)
    session.commit()
    session.refresh(challenge)
    return challenge


@pytest.fixture(name="test_progress")
def test_progress_fixture(session, test_user, test_modules):
    """Progreso de prueba."""
    progress = Progress(
        user_id=test_user.id,
        module_id=test_modules["empathy"].id,
        current_level="beginner"
    )
    session.add(progress)
    session.commit()
    session.refresh(progress)
    return progress


@pytest.fixture(name="test_conversation")
def test_conversation_fixture(session, test_user, test_challenge):
    """Conversación de prueba."""
    conversation = Conversation(
        user_id=test_user.id,
        challenge_id=test_challenge.id
    )
    session.add(conversation)
    session.commit()
    session.refresh(conversation)
    return conversation