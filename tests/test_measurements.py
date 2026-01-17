from fastapi.testclient import TestClient

def test_create_measurement_end_to_end(client: TestClient):
    # 1. PREPARAÇÃO (Setup)
    # Precisamos de um Device e um SensorType antes de medir
    
    # Cria Device
    dev_resp = client.post("/api/v1/devices/", json={"name": "D1", "slug": "d1"})
    device_id = dev_resp.json()["id"]
    
    # Cria Sensor Type
    sens_resp = client.post("/api/v1/sensor-types/", json={"name": "Hum", "unit": "%"})
    sensor_id = sens_resp.json()["id"]
    
    # 2. AÇÃO (Act)
    # Envia a medição vinculada aos IDs acima
    payload = {
        "device_id": device_id,
        "sensor_type_id": sensor_id,
        "value": 55.5
    }
    response = client.post("/api/v1/measurements/", json=payload)
    
    # 3. VERIFICAÇÃO (Assert)
    assert response.status_code == 200
    data = response.json()
    assert data["value"] == 55.5
    assert data["device_id"] == device_id
    assert data["sensor_type_id"] == sensor_id
    assert "id" in data
    assert "created_at" in data

def test_read_measurements_filter(client: TestClient):
    # Vamos verificar se o filtro de limite funciona
    # Cria dependências
    dev_id = client.post("/api/v1/devices/", json={"name": "D2", "slug": "d2"}).json()["id"]
    type_id = client.post("/api/v1/sensor-types/", json={"name": "T2", "unit": "K"}).json()["id"]
    
    # Cria 5 medições
    for i in range(5):
        client.post("/api/v1/measurements/", json={"device_id": dev_id, "sensor_type_id": type_id, "value": i})
        
    # Pede apenas as últimas 2
    response = client.get("/api/v1/measurements/?limit=2")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2