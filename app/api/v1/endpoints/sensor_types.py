from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List

from app.core.database import get_session
from app.models.sensor_type import SensorType
from app.schemas.sensor_type import SensorTypeCreate, SensorTypePublic

router = APIRouter()

@router.post("/", response_model=SensorTypePublic)
async def create_sensor_type(
    sensor_type: SensorTypeCreate, 
    session: AsyncSession = Depends(get_session)
):
    db_sensor_type = SensorType.model_validate(sensor_type)
    session.add(db_sensor_type)
    await session.commit()
    await session.refresh(db_sensor_type)
    return db_sensor_type

@router.get("/", response_model=List[SensorTypePublic])
async def read_sensor_types(
    session: AsyncSession = Depends(get_session),
    skip: int = 0,
    limit: int = 100,
):
    query = select(SensorType).offset(skip).limit(limit)
    result = await session.exec(query)
    return result.all()