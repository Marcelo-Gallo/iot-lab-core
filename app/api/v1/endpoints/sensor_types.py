from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from app.core.database import get_session
from app.models.sensor_type import SensorType
from app.schemas.sensor_type import SensorTypeCreate, SensorTypePublic

router = APIRouter()

@router.post("/", response_model=SensorTypePublic)
def create_sensor_type(
    sensor_type_in: SensorTypeCreate, 
    session: Session = Depends(get_session)
):
    # Verifica se já existe (pelo nome)
    query = select(SensorType).where(SensorType.name == sensor_type_in.name)
    existing = session.exec(query).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Este tipo de sensor já existe.")

    db_sensor_type = SensorType.model_validate(sensor_type_in)
    session.add(db_sensor_type)
    session.commit()
    session.refresh(db_sensor_type)
    return db_sensor_type

@router.get("/", response_model=List[SensorTypePublic])
def read_sensor_types(
    skip: int = 0, 
    limit: int = 100, 
    session: Session = Depends(get_session)
):
    query = select(SensorType).offset(skip).limit(limit)
    return session.exec(query).all()