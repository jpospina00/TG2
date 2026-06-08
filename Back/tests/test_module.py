# test_module.py
# Propósito: Tests del servicio y router de módulos
# Dependencias: pytest
# Fecha: 2026-03-22

def test_list_modules(client, test_modules):
    response = client.get("/modules")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    names = [m["name"] for m in data]
    assert "empathy" in names
    assert "networking" in names


def test_get_module_by_id(client, test_modules):
    empathy_id = test_modules["empathy"].id
    response = client.get(f"/modules/{empathy_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "empathy"


def test_get_nonexistent_module(client):
    response = client.get("/modules/9999")
    assert response.status_code == 404