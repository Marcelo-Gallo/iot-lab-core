from fastapi.testclient import TestClient

def test_create_device(client: TestClient):
    # Tenta criar um dispositivo válido
    payload = {
        "name": "Arduino Lab 1",
        "slug": "arduino-lab-1",
        "location": "Bancada A"
    }
    response = client.post("/api/v1/devices/", json=payload)
    
    # Validações
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Arduino Lab 1"
    assert data["slug"] == "arduino-lab-1"
    assert data["is_active"] is True  # Default deve ser True
    assert "id" in data

def test_create_duplicate_slug_should_fail(client: TestClient):
    # Cria o primeiro
    payload = {"name": "Device A", "slug": "unique-slug"}
    client.post("/api/v1/devices/", json=payload)
    
    # Tenta criar o segundo com MESMO slug
    payload_dup = {"name": "Device B", "slug": "unique-slug"}
    response = client.post("/api/v1/devices/", json=payload_dup)
    
    # Validação: Deve retornar erro 400 (Bad Request)
    assert response.status_code == 400
    assert "Já existe um dispositivo" in response.json()["detail"]

def test_read_devices(client: TestClient):
    # Cria dois dispositivos
    client.post("/api/v1/devices/", json={"name": "D1", "slug": "d1"})
    client.post("/api/v1/devices/", json={"name": "D2", "slug": "d2"})
    
    # Busca a lista
    response = client.get("/api/v1/devices/")
    
    # Validações
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    assert data[0]["slug"] == "d1"