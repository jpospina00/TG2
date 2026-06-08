# test_student_profile.py
# Propósito: Tests del router de perfil del estudiante
# Dependencias: pytest
# Fecha: 2026-03-29

def test_create_profile(client, test_user):
    response = client.post("/students/profile", json={
        "semester": "6",
        "specialization": "backend",
        "self_assessed_level": "intermediate"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["semester"] == "6"
    assert data["specialization"] == "backend"
    assert data["self_assessed_level"] == "intermediate"


def test_get_profile_not_found(client, test_user):
    response = client.get(f"/students/profile/user/{test_user.id}")
    assert response.status_code == 200
    assert response.json()["has_profile"] is False


def test_get_profile_found(client, test_user):
    client.post("/students/profile", json={
        "semester": "8",
        "specialization": "ai",
        "self_assessed_level": "advanced"
    })
    response = client.get(f"/students/profile/user/{test_user.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["has_profile"] is True
    assert data["specialization"] == "ai"


def test_update_profile(client, test_user):
    client.post("/students/profile", json={
        "semester": "5",
        "specialization": "frontend",
        "self_assessed_level": "beginner"
    })
    # Llamar de nuevo actualiza
    response = client.post("/students/profile", json={
        "semester": "6",
        "specialization": "devops",
        "self_assessed_level": "intermediate"
    })
    assert response.status_code == 201
    assert response.json()["specialization"] == "devops"
    assert response.json()["semester"] == "6"