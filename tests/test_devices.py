import pytest
from httpx import AsyncClient

# O Decorator avisa ao pytest que este teste deve rodar num Event Loop
@pytest.mark.asyncio
async def test_create_device(async_client: AsyncClient):
    payload = {
        "name": "Arduino Lab 1",
        "slug": "arduino-lab-1",
        "location": "Bancada A"
    }
    # Note o 'await' aqui
    response = await async_client.post("/api/v1/devices/", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Arduino Lab 1"
    assert "id" in data

@pytest.mark.asyncio
async def test_create_duplicate_slug_should_fail(async_client: AsyncClient):
    payload = {"name": "Device A", "slug": "unique-slug"}
    
    # Cria o primeiro
    await async_client.post("/api/v1/devices/", json=payload)
    
    # Tenta criar o segundo igual
    response = await async_client.post("/api/v1/devices/", json=payload)
    
    assert response.status_code == 400
    assert "Já existe um dispositivo" in response.json()["detail"]

@pytest.mark.asyncio
async def test_read_devices(async_client: AsyncClient):
    await async_client.post("/api/v1/devices/", json={"name": "D1", "slug": "d1"})
    
    response = await async_client.get("/api/v1/devices/")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1