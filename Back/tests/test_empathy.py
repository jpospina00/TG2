# test_empathy.py
# Propósito: Tests de los endpoints del Laboratorio de Empatía
# Dependencias: pytest, unittest.mock
# Fecha: 2026-04-16

import json
from unittest.mock import patch, MagicMock
from model.challenge import Challenge
from model.conversation import Conversation


def make_groq_response(text):
    mock = MagicMock()
    mock.choices[0].message.content = text
    return mock


MOCK_OPTIONS = {
    "options": [
        {"id": "A", "text": "Parece que estás cargando con mucho solo. ¿Te puedo ayudar?", "is_correct": True, "explanation": "Valida la emoción y ofrece ayuda sin imponer."},
        {"id": "B", "text": "Tranquilo, todos tenemos semanas difíciles.", "is_correct": False, "explanation": "Minimiza la emoción sin validarla."},
        {"id": "C", "text": "Deberías haber pedido ayuda antes.", "is_correct": False, "explanation": "Juzga al interlocutor en lugar de validarlo."},
        {"id": "D", "text": "Lo importante es terminar el sprint.", "is_correct": False, "explanation": "Ignora el estado emocional y desvía el foco."},
    ]
}

MOCK_EVAL_RESULT = {
    "precision_emocional": 8.5,
    "calidad_mensaje": 7.0,
    "tono_empatico": 9.0,
    "coherencia_contextual": 7.5,
    "feedback": "Identificaste correctamente el agotamiento. Tu mensaje fue cálido y validador.",
    "completed": True,
    "average": 8.0,
}


# ── Fixtures de empatía ───────────────────────────────────────────────────────

def create_empathy_challenge(session, test_modules):
    """Crea un reto de tipo analysis para empatía."""
    challenge = Challenge(
        module_id=test_modules["empathy"].id,
        user_id=None,
        level="beginner",
        type="analysis",
        agent_profile="Compañero de equipo agotado",
        context="Proyecto de software con entrega próxima",
        opening_message="Llevo tres días sin dormir bien y siento que no voy a lograrlo."
    )
    session.add(challenge)
    session.commit()
    session.refresh(challenge)
    return challenge


def create_empathy_multiple_choice_challenge(session, test_modules):
    """Crea un reto de tipo multiple_choice para empatía."""
    challenge = Challenge(
        module_id=test_modules["empathy"].id,
        user_id=None,
        level="beginner",
        type="multiple_choice",
        agent_profile="Compañero frustrado",
        context="Reunión de equipo cancelada sin aviso",
        opening_message="Nadie me avisó que cancelaron la reunión y perdí el tiempo."
    )
    session.add(challenge)
    session.commit()
    session.refresh(challenge)
    return challenge


def create_conversation(session, test_user, challenge):
    """Crea una conversación para los tests."""
    conv = Conversation(
        user_id=test_user.id,
        challenge_id=challenge.id
    )
    session.add(conv)
    session.commit()
    session.refresh(conv)
    return conv


# ── Tests de opciones ─────────────────────────────────────────────────────────

def test_get_empathy_options(client, test_modules, session):
    """Genera las 4 opciones para un reto de selección múltiple."""
    challenge = create_empathy_multiple_choice_challenge(session, test_modules)

    with patch("service.ai.get_groq_client") as mock_client:
        mock_instance = MagicMock()
        mock_instance.chat.completions.create.return_value = make_groq_response(
            json.dumps(MOCK_OPTIONS)
        )
        mock_client.return_value = mock_instance

        response = client.get(f"/ai/empathy/options/{challenge.id}")

    assert response.status_code == 200
    data = response.json()
    assert "options" in data
    assert len(data["options"]) == 4
    correct = [o for o in data["options"] if o["is_correct"]]
    assert len(correct) == 1


def test_get_empathy_options_nonexistent_challenge(client):
    """Retorna 404 para reto inexistente."""
    response = client.get("/ai/empathy/options/9999")
    assert response.status_code == 404


# ── Tests de evaluación análisis ──────────────────────────────────────────────

def test_evaluate_empathy_lab_approved(client, test_modules, test_user, test_progress, session):
    """Evalúa análisis de empatía — resultado aprobado."""
    challenge = create_empathy_challenge(session, test_modules)
    conv = create_conversation(session, test_user, challenge)

    with patch("service.ai.get_groq_client") as mock_client:
        mock_instance = MagicMock()
        mock_instance.chat.completions.create.return_value = make_groq_response(
            json.dumps(MOCK_EVAL_RESULT)
        )
        mock_client.return_value = mock_instance

        response = client.post("/ai/empathy/evaluate", json={
            "conversation_id": conv.id,
            "emotion_identification": "Creo que está sintiendo agotamiento y soledad porque nadie del equipo le preguntó cómo estaba.",
            "student_message": "Oye, me di cuenta de que llevas días cargando con mucho. ¿Cómo estás? Estoy aquí si necesitas ayuda."
        })

    assert response.status_code == 200
    data = response.json()
    assert "scores" in data
    assert "feedback" in data
    assert data["completed"] is True
    assert "average" in data
    assert data["scores"]["precision_emocional"] == 8.5
    assert data["scores"]["tono_empatico"] == 9.0


def test_evaluate_empathy_lab_not_approved(client, test_modules, test_user, test_progress, session):
    """Evalúa análisis de empatía — resultado no aprobado."""
    challenge = create_empathy_challenge(session, test_modules)
    conv = create_conversation(session, test_user, challenge)

    low_result = {**MOCK_EVAL_RESULT,
        "precision_emocional": 4.0,
        "calidad_mensaje": 3.5,
        "tono_empatico": 4.0,
        "coherencia_contextual": 3.0,
        "completed": False,
        "average": 3.6,
    }

    with patch("service.ai.get_groq_client") as mock_client:
        mock_instance = MagicMock()
        mock_instance.chat.completions.create.return_value = make_groq_response(
            json.dumps(low_result)
        )
        mock_client.return_value = mock_instance

        response = client.post("/ai/empathy/evaluate", json={
            "conversation_id": conv.id,
            "emotion_identification": "Está cansado.",
            "student_message": "Deberías organizarte mejor."
        })

    assert response.status_code == 200
    assert response.json()["completed"] is False


def test_evaluate_empathy_lab_nonexistent_conversation(client):
    """Retorna 404 para conversación inexistente."""
    response = client.post("/ai/empathy/evaluate", json={
        "conversation_id": 9999,
        "emotion_identification": "Algo",
        "student_message": "Algo"
    })
    assert response.status_code == 404


# ── Tests de selección múltiple ───────────────────────────────────────────────

def test_submit_empathy_multiple_choice_correct(client, test_modules, test_user, test_progress, session):
    """Registra respuesta correcta en selección múltiple."""
    challenge = create_empathy_multiple_choice_challenge(session, test_modules)
    conv = create_conversation(session, test_user, challenge)

    response = client.post("/ai/empathy/multiple-choice", json={
        "conversation_id": conv.id,
        "selected_option_id": "A",
        "is_correct": True,
        "options": MOCK_OPTIONS["options"]
    })

    assert response.status_code == 200
    data = response.json()
    assert data["completed"] is True
    assert "options" in data


def test_submit_empathy_multiple_choice_incorrect(client, test_modules, test_user, test_progress, session):
    """Registra respuesta incorrecta en selección múltiple."""
    challenge = create_empathy_multiple_choice_challenge(session, test_modules)
    conv = create_conversation(session, test_user, challenge)

    response = client.post("/ai/empathy/multiple-choice", json={
        "conversation_id": conv.id,
        "selected_option_id": "C",
        "is_correct": False,
        "options": MOCK_OPTIONS["options"]
    })

    assert response.status_code == 200
    assert response.json()["completed"] is False


def test_submit_empathy_multiple_choice_nonexistent_conversation(client):
    """Retorna 404 para conversación inexistente."""
    response = client.post("/ai/empathy/multiple-choice", json={
        "conversation_id": 9999,
        "selected_option_id": "A",
        "is_correct": True,
        "options": []
    })
    assert response.status_code == 404