import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_measurement_end_to_end(async_client: AsyncClient):
    # Cria Sensor Type
    s_resp = await async_client.post("/api/v1/sensor-types/", json={"name": "Temp", "unit": "C"})
    sensor_id = s_resp.json()["id"]

    # Cria Device
    d_resp = await async_client.post("/api/v1/devices/", json={"name": "Dev 1", "slug": "dev-1"})
    device_id = d_resp.json()["id"]

    # Vincula o sensor ao dispositivo
    link_resp = await async_client.post(
        f"/api/v1/devices/{device_id}/sensors",
        json={"sensor_ids": [sensor_id]}
    )
    assert link_resp.status_code == 200

    # Envia Medição
    payload = {
        "device_id": device_id,
        "sensor_type_id": sensor_id,
        "value": 25.5
    }
    response = await async_client.post("/api/v1/measurements/", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["value"] == 25.5

@pytest.mark.asyncio
async def test_security_reject_unlinked_sensor(async_client: AsyncClient):
    """Garante que o Porteiro barra sensores não vinculados"""
    # Cria Sensor e Device mas NÃO vincula
    s_id = (await async_client.post("/api/v1/sensor-types/", json={"name": "X", "unit": "X"})).json()["id"]
    d_id = (await async_client.post("/api/v1/devices/", json={"name": "Y", "slug": "y"})).json()["id"]

    payload = {"device_id": d_id, "sensor_type_id": s_id, "value": 10.0}
    response = await async_client.post("/api/v1/measurements/", json=payload)
    
    # Deve ser barrado
    assert response.status_code == 400
    assert "não possui o sensor" in response.json()["detail"]