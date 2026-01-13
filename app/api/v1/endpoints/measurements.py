from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List

from app.core.database import get_session
from app.models.measurement import Measurement
from app.schemas.measurement import MeasurementCreate, MeasurementPublic

router = APIRouter()

@router.post("/", response_model=MeasurementPublic)
def create_measurement(
    measurement_in: MeasurementCreate, 
    session: Session = Depends(get_session)
):
    """
    Registra uma nova leitura de sensor.
    """
    # Cria o objeto do banco baseado no schema
    db_measurement = Measurement.model_validate(measurement_in)
    
    session.add(db_measurement)
    session.commit()
    session.refresh(db_measurement)
    
    return db_measurement

@router.get("/", response_model=List[MeasurementPublic])
def read_measurements(
    skip: int = 0, 
    limit: int = 100, 
    session: Session = Depends(get_session)
):
    """
    Lista as últimas medições registradas.
    Order by desc(id) para ver as mais recentes primeiro.
    """
    query = select(Measurement).order_by(Measurement.id.desc()).offset(skip).limit(limit)
    return session.exec(query).all()