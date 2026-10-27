import pytest
from fastapi.testclient import TestClient
from app.api import app, orders
from cargar_csv import load_fixture

client = TestClient(app)


@pytest.fixture(autouse=True)
def recargar_pedidos():
    orders.clear()
    orders.update(load_fixture())


def test_get_pedido_existente_200():
    assert client.get("/orders/O001").status_code == 200


def test_pedido_inexistente_404():
    response = client.post("/orders/O999/confirm")
    assert response.status_code == 404
    assert response.json()["detail"] == "No existe"


def test_confirmar_200():
    response = client.post("/orders/O001/confirm")
    assert response.status_code == 200
    assert response.json()["status"] == "CONFIRMED"


def test_confirmar_dos_veces_409():
    client.post("/orders/O013/confirm")
    assert client.post("/orders/O013/confirm").status_code == 409


def test_confirmar_pedido_vacio_422():
    assert client.post("/orders/O007/confirm").status_code == 422


def test_enviar_sin_guia_422():
    client.post("/orders/O012/confirm")
    response = client.post("/orders/O012/ship", json={"tracking_number": ""})
    assert response.status_code == 422


def test_cancelar_desde_shipped_409():
    client.post("/orders/O014/confirm")
    client.post("/orders/O014/ship", json={"tracking_number": "GUIA123"})
    response = client.post("/orders/O014/cancel", json={"reason": "Cliente lo solicitó"})
    assert response.status_code == 409