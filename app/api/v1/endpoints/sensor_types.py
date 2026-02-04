from typing import Any, List
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1 import deps
from app.core.database import get_session
from app.models.user import User
from app.models.sensor_type import SensorType
from app.schemas.sensor_type import SensorTypeCreate, SensorTypePublic, SensorTypeUpdate

router = APIRouter()

# CORREÇÃO AQUI: response_model usa SensorTypePublic
@router.get("/", response_model=List[SensorTypePublic])
async def read_sensor_types(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Retrieve sensor types.
    """
    query = select(SensorType).order_by(SensorType.id.asc()).offset(skip).limit(limit)
    result = await session.exec(query)
    return result.all()

@router.post("/", response_model=SensorTypePublic)
async def create_sensor_type(
    *,
    session: AsyncSession = Depends(get_session),
    sensor_type_in: SensorTypeCreate,
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """
    Create new sensor type.
    """
    sensor_type = SensorType.from_orm(sensor_type_in)
    session.add(sensor_type)
    await session.commit()
    await session.refresh(sensor_type)
    return sensor_type

@router.put("/{sensor_type_id}", response_model=SensorTypePublic)
async def update_sensor_type(
    *,
    session: AsyncSession = Depends(get_session),
    sensor_type_id: int,
    sensor_type_in: SensorTypeUpdate,
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """
    Update a sensor type.
    """
    sensor_type = await session.get(SensorType, sensor_type_id)
    if not sensor_type:
        raise HTTPException(status_code=404, detail="Sensor type not found")
    
    update_data = sensor_type_in.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(sensor_type, key, value)
        
    session.add(sensor_type)
    await session.commit()
    await session.refresh(sensor_type)
    return sensor_type

@router.delete("/{sensor_type_id}")
async def delete_sensor_type(
    *,
    session: AsyncSession = Depends(get_session),
    sensor_type_id: int,
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """
    Arquiva um tipo de sensor (Soft Delete).
    """
    sensor_type = await session.get(SensorType, sensor_type_id)
    if not sensor_type:
        raise HTTPException(status_code=404, detail="Sensor type not found")
    
    sensor_type.deleted_at = datetime.now(timezone.utc).replace(tzinfo=None)
    sensor_type.is_active = False
    
    session.add(sensor_type)
    await session.commit()
    return {"ok": True}

@router.post("/{sensor_type_id}/restore")
async def restore_sensor_type(
    *,
    session: AsyncSession = Depends(get_session),
    sensor_type_id: int,
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """
    Restaura um tipo de sensor arquivado.
    """
    sensor_type = await session.get(SensorType, sensor_type_id)
    if not sensor_type:
        raise HTTPException(status_code=404, detail="Sensor type not found")
    
    sensor_type.deleted_at = None
    sensor_type.is_active = True
    
    session.add(sensor_type)
    await session.commit()
    return {"ok": True}