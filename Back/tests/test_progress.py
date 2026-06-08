# test_progress.py
# Propósito: Tests del servicio y router de progreso
# Dependencias: pytest
# Fecha: 2026-03-22

def test_create_progress(client, test_user, test_modules):
    response = client.post("/progress", json={
        "user_id": test_user.id,
        "module_id": test_modules["empathy"].id,
        "current_level": "beginner"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["current_level"] == "beginner"
    assert data["user_id"] == test_user.id


def test_create_duplicate_progress(client, test_progress):
    response = client.post("/progress", json={
        "user_id": test_progress.user_id,
        "module_id": test_progress.module_id,
        "current_level": "beginner"
    })
    assert response.status_code == 409


def test_get_user_progress(client, test_progress, test_user):
    response = client.get(f"/progress/user/{test_user.id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["user_id"] == test_user.id


def test_update_progress_level(client, test_progress):
    response = client.patch(f"/progress/{test_progress.id}", json={
        "current_level": "intermediate"
    })
    assert response.status_code == 200
    assert response.json()["current_level"] == "intermediate"


def test_get_nonexistent_progress(client):
    response = client.get("/progress/9999")
    assert response.status_code == 404