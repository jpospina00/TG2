# test_ai.py
# Propósito: Tests del router de IA con mocks de Groq
# Dependencias: pytest, unittest.mock
# Fecha: 2026-03-22

from unittest.mock import patch, MagicMock


def make_groq_response(text):
    """Helper para crear respuesta mock de Groq."""
    mock_response = MagicMock()
    mock_response.choices[0].message.content = text
    return mock_response


# ── Reto Simple ───────────────────────────────────────────────────────────────

def test_evaluate_simple_approved(client, test_conversation, test_challenge, test_modules, test_user, test_progress):
    """Evaluar reto simple — resultado aprobado."""
    feedback_text = (
        "La respuesta demuestra empatía y reconocimiento emocional. "
        "El lenguaje es cálido y no juzga al interlocutor. "
        "RESULTADO: APROBADO"
    )

    with patch("service.ai.get_groq_client") as mock_client:
        mock_instance = MagicMock()
        mock_instance.chat.completions.create.return_value = make_groq_response(feedback_text)
        mock_client.return_value = mock_instance

        response = client.post("/ai/simple/evaluate", json={
            "conversation_id": test_conversation.id,
            "student_response": "Entiendo que te sientes frustrado, y tiene sentido que te afecte."
        })

    assert response.status_code == 200
    data = response.json()
    assert "feedback" in data
    assert data["completed"] is True
    assert "RESULTADO: APROBADO" in data["feedback"]


def test_evaluate_simple_not_approved(client, test_conversation, test_challenge, test_modules, test_user, test_progress):
    """Evaluar reto simple — resultado no aprobado."""
    feedback_text = (
        "La respuesta no reconoce la emoción del interlocutor. "
        "Falta validación emocional y lenguaje empático. "
        "RESULTADO: NO APROBADO"
    )

    with patch("service.ai.get_groq_client") as mock_client:
        mock_instance = MagicMock()
        mock_instance.chat.completions.create.return_value = make_groq_response(feedback_text)
        mock_client.return_value = mock_instance

        response = client.post("/ai/simple/evaluate", json={
            "conversation_id": test_conversation.id,
            "student_response": "No te preocupes, ya se te pasará."
        })

    assert response.status_code == 200
    data = response.json()
    assert data["completed"] is False
    assert "RESULTADO: NO APROBADO" in data["feedback"]


def test_evaluate_simple_nonexistent_conversation(client):
    """Retornar 404 para conversación inexistente."""
    response = client.post("/ai/simple/evaluate", json={
        "conversation_id": 9999,
        "student_response": "Alguna respuesta"
    })
    assert response.status_code == 404


# ── Reto Conversacional ───────────────────────────────────────────────────────

def test_conversational_turn(client, test_conversation, test_challenge, test_modules, test_user, test_progress):
    """Generar respuesta del agente en reto conversacional."""
    agent_reply = "Gracias por escucharme. Me alegra que entiendas cómo me siento."

    with patch("service.ai.get_groq_client") as mock_client:
        mock_instance = MagicMock()
        mock_instance.chat.completions.create.return_value = make_groq_response(agent_reply)
        mock_client.return_value = mock_instance

        response = client.post("/ai/conversational/turn", json={
            "conversation_id": test_conversation.id,
            "student_message": "Entiendo que te sientes ignorado, tiene todo el sentido.",
            "history": [
                {"role": "agent", "content": "Me siento ignorado en el grupo."},
            ]
        })

    assert response.status_code == 200
    data = response.json()
    assert "agent_reply" in data
    assert data["agent_reply"] == agent_reply
    assert "turn_count" in data


def test_conversational_turn(client, test_conversation, test_challenge, test_modules, test_user, test_progress):
    agent_reply = "Gracias por escucharme. Me alegra que entiendas cómo me siento."

    with patch("web.ai.generate_agent_reply") as mock_reply:
        mock_reply.return_value = agent_reply

        response = client.post("/ai/conversational/turn", json={
            "conversation_id": test_conversation.id,
            "student_message": "Entiendo que te sientes ignorado, tiene todo el sentido.",
            "history": [
                {"role": "agent", "content": "Me siento ignorado en el grupo."},
            ]
        })

    assert response.status_code == 200
    data = response.json()
    assert "agent_reply" in data
    assert data["agent_reply"] == agent_reply
    assert "turn_count" in data


def test_conversational_turn_nonexistent_conversation(client):
    """Retornar 404 para conversación inexistente en turno conversacional."""
    response = client.post("/ai/conversational/turn", json={
        "conversation_id": 9999,
        "student_message": "Algún mensaje",
        "history": []
    })
    assert response.status_code == 404