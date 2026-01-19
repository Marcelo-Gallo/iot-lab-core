from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List
from datetime import datetime

from app.core.database import get_session
from app.models.sensor_type import SensorType
from app.schemas.sensor_type import SensorTypeCreate, SensorTypePublic, SensorTypeUpdate

router = APIRouter()

# LISTAR
@router.get("/", response_model=List[SensorTypePublic])
async def read_sensor_types(session: AsyncSession = Depends(get_session)):
    result = await session.exec(select(SensorType))
    return result.all()

# CRIAR
@router.post("/", response_model=SensorTypePublic)
async def create_sensor_type(
    sensor_type: SensorTypeCreate, 
    session: AsyncSession = Depends(get_session)
):
    # Verifica duplicidade de nome
    query = select(SensorType).where(SensorType.name == sensor_type.name)
    existing = await session.exec(query)
    if existing.first():
        raise HTTPException(status_code=400, detail="Já existe um sensor com este nome.")

    db_sensor = SensorType.model_validate(sensor_type)
    session.add(db_sensor)
    await session.commit()
    await session.refresh(db_sensor)
    return db_sensor

# DELETAR
@router.delete("/{sensor_id}")
async def delete_sensor_type(
    sensor_id: int, 
    session: AsyncSession = Depends(get_session)
):
    sensor = await session.get(SensorType, sensor_id)
    if not sensor:
        raise HTTPException(status_code=404, detail="Tipo de sensor não encontrado.")
    
    try:
        sensor.is_active = False
        sensor.deleted_at = datetime.utcnow()
        
        session.add(sensor)
        await session.commit()
        return {"ok": True, "status": "arquivado"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao arquivar: {e}")
    
@router.patch("/{sensor_id}", response_model=SensorTypePublic)
async def update_sensor_type(
    sensor_id: int,
    sensor_update: SensorTypeUpdate,
    session: AsyncSession = Depends(get_session)
):
    # Busca no banco
    db_sensor = await session.get(SensorType, sensor_id)
    if not db_sensor:
        raise HTTPException(status_code=404, detail="Sensor não encontrado.")

    # Atualiza apenas os campos enviados
    sensor_data = sensor_update.model_dump(exclude_unset=True)
    for key, value in sensor_data.items():
        setattr(db_sensor, key, value)

    # Salva
    session.add(db_sensor)
    await session.commit()
    await session.refresh(db_sensor)
    return db_sensor