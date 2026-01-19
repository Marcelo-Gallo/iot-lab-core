import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_crud_sensor_type(async_client: AsyncClient):
    # Create
    resp = await async_client.post("/api/v1/sensor-types/", json={"name": "CO2", "unit": "ppm"})
    assert resp.status_code == 200
    
    # Read
    resp = await async_client.get("/api/v1/sensor-types/")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1