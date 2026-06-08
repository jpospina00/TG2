# test_diagnostic.py
# Propósito: Tests del router de diagnóstico con mocks de Groq
# Dependencias: pytest, unittest.mock
# Fecha: 2026-03-22

import json
from unittest.mock import patch, MagicMock


def make_groq_response(text):
    mock_response = MagicMock()
    mock_response.choices[0].message.content = text
    return mock_response


MOCK_QUESTIONS = {
    "questions": [
        {
            "id": 1,
            "situation": "Un compañero llega tarde a una reunión importante.",
            "question": "¿Cuál sería la respuesta más empática?",
            "options": {
                "A": "Llegas tarde siempre.",
                "B": "¿Está todo bien? ¿Pasó algo?",
                "C": "Esto es una falta de respeto.",
                "D": "No importa, ya terminamos."
            },
            "correct": "B",
            "explanation": "Valida la situación antes de juzgar."
        }
    ]
}

MOCK_SCENARIO = {
    "agent_profile": "Compañero de grupo universitario estresado",
    "context": "Proyecto final de semestre con entregas próximas.",
    "opening_message": "No sé cómo voy a terminar todo esto a tiempo, estoy agotado."
}

MOCK_EVALUATION = {
    "level_result": "intermediate",
    "written_feedback": "La respuesta muestra comprensión del contexto emocional.",
    "strengths": "Buena identificación de emociones.",
    "weaknesses": "Podría profundizar más en la validación.",
    "justification": "Puntaje medio con respuesta escrita aceptable."
}

MOCK_CHALLENGES = {
    "challenges": [
        {
            "agent_profile": "Estudiante agobiado con múltiples entregas",
            "context": "Semana de parciales en la universidad.",
            "opening_message": "No puedo más, tengo cinco entregas esta semana.",
            "type": "simple"
        }
    ] * 5
}


def test_get_diagnostic_questions(client):
    """Generar preguntas de diagnóstico."""
    with patch("service.ai.get_groq_client") as mock_client:
        mock_instance = MagicMock()
        mock_instance.chat.completions.create.return_value = make_groq_response(
            json.dumps(MOCK_QUESTIONS)
        )
        mock_client.return_value = mock_instance

        with patch("web.diagnostic.ai_service.generate_diagnostic_scenario") as mock_scenario:
            mock_scenario.return_value = MOCK_SCENARIO

            response = client.get("/diagnostic/questions/empathy")

    assert response.status_code == 200
    data = response.json()
    assert "questions" in data
    assert "scenario" in data


def test_get_user_diagnostic_not_found(client, test_user, test_modules):
    """Retornar has_diagnostic=False cuando no hay diagnóstico."""
    response = client.get(
        f"/diagnostic/user/{test_user.id}/module/{test_modules['empathy'].id}"
    )
    assert response.status_code == 200
    assert response.json()["has_diagnostic"] is False


def test_submit_diagnostic(client, test_user, test_modules, test_progress):
    """Enviar diagnóstico y generar retos personalizados."""
    with patch("web.diagnostic.ai_service.evaluate_diagnostic_response") as mock_eval:
        mock_eval.return_value = MOCK_EVALUATION

        with patch("web.diagnostic.ai_service.generate_personalized_challenges") as mock_challenges:
            mock_challenges.return_value = MOCK_CHALLENGES["challenges"]

            response = client.post("/diagnostic/submit", json={
                "user_id": test_user.id,
                "module_id": test_modules["empathy"].id,
                "module_name": "empathy",
                "multiple_choice_score": 2,
                "scenario": MOCK_SCENARIO,
                "written_response": "Entiendo que estás agotado, es mucho lo que llevas encima."
            })

    assert response.status_code == 200
    data = response.json()
    assert data["level_result"] == "intermediate"
    assert "strengths" in data
    assert "weaknesses" in data
    assert data["challenges_ready"] is False


def test_get_user_diagnostic_after_submit(client, test_user, test_modules, test_progress):
    """Verificar que el diagnóstico queda guardado después de enviarlo."""
    with patch("web.diagnostic.ai_service.evaluate_diagnostic_response") as mock_eval:
        mock_eval.return_value = MOCK_EVALUATION

        with patch("web.diagnostic.ai_service.generate_personalized_challenges") as mock_challenges:
            mock_challenges.return_value = MOCK_CHALLENGES["challenges"]

            client.post("/diagnostic/submit", json={
                "user_id": test_user.id,
                "module_id": test_modules["empathy"].id,
                "module_name": "empathy",
                "multiple_choice_score": 2,
                "scenario": MOCK_SCENARIO,
                "written_response": "Buena respuesta empática de prueba."
            })

    response = client.get(
        f"/diagnostic/user/{test_user.id}/module/{test_modules['empathy'].id}"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["has_diagnostic"] is True
    assert data["level_result"] == "intermediate"


def test_reset_diagnostic(client, test_user, test_modules, test_progress):
    """Resetear diagnóstico del usuario."""
    response = client.delete(
        f"/diagnostic/user/{test_user.id}/module/{test_modules['empathy'].id}/reset"
    )
    assert response.status_code == 200
    assert "reiniciado" in response.json()["message"]