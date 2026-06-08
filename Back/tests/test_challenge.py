# test_challenge.py
# Propósito: Tests del servicio y router de retos
# Dependencias: pytest
# Fecha: 2026-03-22

def test_create_challenge(client, test_modules):
    response = client.post("/challenges", json={
        "module_id": test_modules["empathy"].id,
        "user_id": None,
        "level": "beginner",
        "type": "simple",
        "agent_profile": "Compañero frustrado",
        "context": "Proyecto grupal",
        "opening_message": "Me siento ignorado."
    })
    assert response.status_code == 201
    data = response.json()
    assert data["level"] == "beginner"
    assert data["type"] == "simple"


def test_get_challenge_by_id(client, test_challenge):
    response = client.get(f"/challenges/{test_challenge.id}")
    assert response.status_code == 200
    assert response.json()["id"] == test_challenge.id


def test_get_nonexistent_challenge(client):
    response = client.get("/challenges/9999")
    assert response.status_code == 404


def test_list_challenges(client, test_challenge):
    response = client.get("/challenges")
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_get_challenges_by_module_and_level(client, test_challenge, test_modules):
    response = client.get(
        f"/challenges/module/{test_modules['empathy'].id}/level/beginner"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert all(c["level"] == "beginner" for c in data)


def test_get_challenges_by_module_and_level_with_user(client, test_challenge, test_modules, test_user):
    response = client.get(
        f"/challenges/module/{test_modules['empathy'].id}/level/beginner",
        params={"user_id": test_user.id}
    )
    assert response.status_code == 200


def test_update_challenge(client, test_challenge):
    response = client.patch(f"/challenges/{test_challenge.id}", json={
        "agent_profile": "Perfil actualizado"
    })
    assert response.status_code == 200
    assert response.json()["agent_profile"] == "Perfil actualizado"


def test_delete_challenge(client, test_challenge):
    response = client.delete(f"/challenges/{test_challenge.id}")
    assert response.status_code == 200
    response = client.get(f"/challenges/{test_challenge.id}")
    assert response.status_code == 404