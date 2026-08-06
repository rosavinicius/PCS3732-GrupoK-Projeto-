# Para rodar localmente: pytest tests/

import pytest
from backend.src.db.schemas import DeviceStatus

def test_create_device(client):
    """Testa a rota POST /devices/."""
    payload = {
        "mqtt_client_id": "esp32-teste-01",
        "name": "ESP32 de Teste",
        "ip": "192.168.1.50"
    }
    response = client.post("/devices/", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["mqtt_client_id"] == "esp32-teste-01"
    assert data["name"] == "ESP32 de Teste"
    assert "id" in data

def test_create_duplicate_device(client):
    """Garante que dispositivos duplicados retornem erro 409."""
    payload = {"mqtt_client_id": "esp32-duplicado", "name": "ESP1"}
    client.post("/devices/", json=payload)
    
    # Tenta criar o mesmo novamente
    response = client.post("/devices/", json=payload)
    assert response.status_code == 409
    assert response.json()["detail"] == "Device already registered"