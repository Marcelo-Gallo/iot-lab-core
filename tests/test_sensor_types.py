from fastapi.testclient import TestClient

def test_create_sensor_type(client: TestClient):
    payload = {
        "name": "CO2",
        "unit": "ppm",
        "description": "Dióxido de Carbono"
    }
    response = client.post("/api/v1/sensor-types/", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "CO2"
    assert data["unit"] == "ppm"
    assert "id" in data

def test_read_sensor_types(client: TestClient):
    # Cria um para ter certeza que lista não está vazia
    client.post("/api/v1/sensor-types/", json={"name": "Temp", "unit": "C"})
    
    response = client.get("/api/v1/sensor-types/")
    
    assert response.status_code == 200
    assert len(response.json()) >= 1