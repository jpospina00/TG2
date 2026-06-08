# test_message.py
# Propósito: Tests del servicio y router de mensajes
# Dependencias: pytest
# Fecha: 2026-03-22

def test_create_message(client, test_conversation):
    response = client.post("/messages", json={
        "conversation_id": test_conversation.id,
        "role": "agent",
        "content": "Hola, ¿cómo estás?",
        "order": 1
    })
    assert response.status_code == 201
    data = response.json()
    assert data["role"] == "agent"
    assert data["content"] == "Hola, ¿cómo estás?"
    assert data["order"] == 1


def test_create_user_message(client, test_conversation):
    response = client.post("/messages", json={
        "conversation_id": test_conversation.id,
        "role": "user",
        "content": "Me siento frustrado con el grupo.",
        "order": 2
    })
    assert response.status_code == 201
    assert response.json()["role"] == "user"


def test_get_conversation_messages(client, test_conversation):
    # Crear dos mensajes
    client.post("/messages", json={
        "conversation_id": test_conversation.id,
        "role": "agent",
        "content": "Mensaje del agente",
        "order": 1
    })
    client.post("/messages", json={
        "conversation_id": test_conversation.id,
        "role": "user",
        "content": "Respuesta del usuario",
        "order": 2
    })

    response = client.get(f"/messages/conversation/{test_conversation.id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["order"] == 1
    assert data[1]["order"] == 2