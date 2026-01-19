from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List
from sqlalchemy import desc

from app.core.database import get_session
from app.models.device import Device
from app.schemas.device import DeviceCreate, DevicePublic, DeviceUpdate

from app.models.device_sensor import DeviceSensorLink
from app.models.sensor_type import SensorType         
from app.schemas.device import DeviceSensorsUpdate    

router = APIRouter()

@router.post("/", response_model=DevicePublic)
async def create_device(
    device: DeviceCreate, 
    session: AsyncSession = Depends(get_session)
):
    # Verifica unicidade do slug
    query = select(Device).where(Device.slug == device.slug)
    result = await session.exec(query)
    existing_device = result.first()
    
    if existing_device:
        raise HTTPException(status_code=400, detail="Já existe um dispositivo com este slug.")

    db_device = Device.model_validate(device)
    session.add(db_device)
    await session.commit()
    await session.refresh(db_device)
    return db_device

@router.get("/", response_model=List[DevicePublic])
async def read_devices(
    session: AsyncSession = Depends(get_session),
    skip: int = 0,
    limit: int = 100,
):
    # Ordenação LIFO (Last In, First Out)
    query = select(Device).order_by(Device.id.desc()).offset(skip).limit(limit)
    result = await session.exec(query)
    return result.all()

@router.get("/{device_id}", response_model=DevicePublic)
async def read_device(
    device_id: int, 
    session: AsyncSession = Depends(get_session)
):
    db_device = await session.get(Device, device_id)
    if not db_device:
        raise HTTPException(status_code=404, detail="Dispositivo não encontrado")
    return db_device

@router.patch("/{device_id}", response_model=DevicePublic)
async def update_device(
    device_id: int, 
    device_in: DeviceUpdate, 
    session: AsyncSession = Depends(get_session)
):
    db_device = await session.get(Device, device_id)
    if not db_device:
        raise HTTPException(status_code=404, detail="Dispositivo não encontrado")
    
    device_data = device_in.model_dump(exclude_unset=True)
    for key, value in device_data.items():
        setattr(db_device, key, value)
        
    session.add(db_device)
    await session.commit()
    await session.refresh(db_device)
    return db_device

@router.delete("/{device_id}")
async def delete_device(
    device_id: int, 
    session: AsyncSession = Depends(get_session)
):
    db_device = await session.get(Device, device_id)
    if not db_device:
        raise HTTPException(status_code=404, detail="Dispositivo não encontrado")
    
    await session.delete(db_device)
    await session.commit()
    return {"ok": True}

@router.post("/{device_id}/sensors", response_model=dict)
async def update_device_sensors(
    device_id: int,
    payload: DeviceSensorsUpdate,
    session: AsyncSession = Depends(get_session)
):
    """
    Atualiza a lista de sensores vinculados a um dispositivo.
    (Substitui a lista atual pela nova).
    """
    device = await session.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Dispositivo não encontrado")

    current_links_query = select(DeviceSensorLink.sensor_type_id).where(
        DeviceSensorLink.device_id == device_id
    )
    result = await session.exec(current_links_query)
    current_ids = set(result.all())
    
    new_ids = set(payload.sensor_ids)

    to_add = new_ids - current_ids
    to_remove = current_ids - new_ids

    for sensor_id in to_add:
        link = DeviceSensorLink(device_id=device_id, sensor_type_id=sensor_id)
        session.add(link)

    if to_remove:
        stmt = select(DeviceSensorLink).where(
            DeviceSensorLink.device_id == device_id,
            DeviceSensorLink.sensor_type_id.in_(to_remove)
        )
        results = await session.exec(stmt)
        for link in results:
            await session.delete(link)

    await session.commit()
    
    return {"status": "ok", "added": len(to_add), "removed": len(to_remove)}

@router.get("/{device_id}/sensors", response_model=List[int])
async def get_device_sensors(
    device_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Retorna apenas os IDs dos sensores vinculados"""
    query = select(DeviceSensorLink.sensor_type_id).where(DeviceSensorLink.device_id == device_id)
    result = await session.exec(query)
    return result.all()