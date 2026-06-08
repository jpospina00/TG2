# test_conversation.py
# Propósito: Tests del servicio y router de conversaciones
# Dependencias: pytest
# Fecha: 2026-03-22

def test_create_conversation(client, test_user, test_challenge):
    response = client.post("/conversations", json={
        "user_id": test_user.id,
        "challenge_id": test_challenge.id
    })
    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == test_user.id
    assert data["challenge_id"] == test_challenge.id
    assert data["ended_at"] is None


def test_get_conversation_by_id(client, test_conversation):
    response = client.get(f"/conversations/{test_conversation.id}")
    assert response.status_code == 200
    assert response.json()["id"] == test_conversation.id


def test_get_user_conversations(client, test_conversation, test_user):
    response = client.get(f"/conversations/user/{test_user.id}")
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_close_conversation(client, test_conversation):
    response = client.patch(f"/conversations/{test_conversation.id}/close")
    assert response.status_code == 200
    assert response.json()["ended_at"] is not None


def test_get_nonexistent_conversation(client):
    response = client.get("/conversations/9999")
    assert response.status_code == 404