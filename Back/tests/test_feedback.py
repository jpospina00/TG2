# test_feedback.py
# Propósito: Tests del servicio y router de retroalimentación
# Dependencias: pytest
# Fecha: 2026-03-22

def test_create_feedback(client, test_conversation):
    response = client.post("/feedback", json={
        "conversation_id": test_conversation.id,
        "content": "Buena respuesta empática.",
        "completed": True
    })
    assert response.status_code == 201
    data = response.json()
    assert data["completed"] is True
    assert data["conversation_id"] == test_conversation.id


def test_get_feedback_by_conversation(client, test_conversation):
    client.post("/feedback", json={
        "conversation_id": test_conversation.id,
        "content": "Retroalimentación de prueba.",
        "completed": False
    })
    response = client.get(f"/feedback/conversation/{test_conversation.id}")
    assert response.status_code == 200
    assert response.json()["conversation_id"] == test_conversation.id


def test_get_feedback_nonexistent_conversation(client):
    response = client.get("/feedback/conversation/9999")
    assert response.status_code == 404


def test_feedback_completed_false(client, test_conversation):
    response = client.post("/feedback", json={
        "conversation_id": test_conversation.id,
        "content": "Necesita mejorar.",
        "completed": False
    })
    assert response.status_code == 201
    assert response.json()["completed"] is False