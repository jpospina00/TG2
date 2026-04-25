# test_user.py
# Propósito: Tests del servicio y router de usuarios
# Dependencias: pytest, fastapi testclient
# Fecha: 2026-04-25

import pytest


def test_create_user(client):
    """Crear usuario nuevo."""
    response = client.post("/users", json={
        "auth0_id": "auth0|nuevo123",
        "name": "Juan Pablo",
        "email": "juan@test.com"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["auth0_id"] == "auth0|nuevo123"
    assert data["name"] == "Juan Pablo"
    assert data["email"] == "juan@test.com"
    assert "id" in data


def test_create_duplicate_user(client, test_user):
    """No debe permitir crear usuario con auth0_id duplicado."""
    response = client.post("/users", json={
        "auth0_id": "auth0|test123",
        "name": "Otro nombre",
        "email": "otro@test.com"
    })
    assert response.status_code == 409


def test_get_user_by_id(client, test_user):
    """Obtener usuario por ID."""
    response = client.get(f"/users/{test_user.id}")
    assert response.status_code == 200
    assert response.json()["id"] == test_user.id


def test_get_user_by_auth0(client, test_user):
    """Obtener usuario por auth0_id."""
    response = client.get(f"/users/auth0/{test_user.auth0_id}")
    assert response.status_code == 200
    assert response.json()["auth0_id"] == test_user.auth0_id


def test_get_nonexistent_user(client):
    """Retornar 404 para usuario inexistente."""
    response = client.get("/users/9999")
    assert response.status_code == 404


def test_list_users(client, test_user):
    """Listar todos los usuarios."""
    response = client.get("/users")
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_update_user(client, test_user):
    """Actualizar datos del usuario."""
    response = client.patch(f"/users/{test_user.id}", json={
        "name": "Nombre Actualizado"
    })
    assert response.status_code == 200
    assert response.json()["name"] == "Nombre Actualizado"


def test_delete_user(client, test_user):
    """Eliminar usuario."""
    response = client.delete(f"/users/{test_user.id}")
    assert response.status_code == 200
    # Verificar que ya no existe
    response = client.get(f"/users/{test_user.id}")
    assert response.status_code == 404