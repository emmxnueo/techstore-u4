from fastapi.testclient import TestClient
from app.api import app

client = TestClient(app)


def test_pedido_inexistente_404():
    response = client.post("/orders/O999/confirm")
    assert response.status_code == 404
    assert response.json()["detail"] == "No existe"