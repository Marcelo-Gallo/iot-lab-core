from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from app.core.socket import manager
from sqlmodel import Session, select
from typing import List, Optional
from datetime import datetime

from app.core.database import get_session
from app.models.measurement import Measurement
from app.schemas.measurement import MeasurementCreate, MeasurementPublic

router = APIRouter()

@router.post("/", response_model=MeasurementPublic)
async def create_measurement(
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

    payload = {
        "id": db_measurement.id,
        "device_id": db_measurement.device_id,
        "sensor_type_id": db_measurement.sensor_type_id,
        "value": db_measurement.value,
        "created_at": db_measurement.created_at.isoformat() # ISO 8601 String
    }
    
    await manager.broadcast(payload)

    return db_measurement

@router.get("/", response_model=List[MeasurementPublic])
def read_measurements(
    session: Session = Depends(get_session),
    skip: int = 0,
    limit: int = 100,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    device_ids: Optional[List[int]] = Query(default=None) # <--- PARÂMETRO NOVO
):
    """
    Lista medições com filtros opcionais de data e dispositivos.
    """
    query = select(Measurement)
    
    if start_date:
        query = query.where(Measurement.created_at >= start_date)
    
    if end_date:
        query = query.where(Measurement.created_at <= end_date)
    
    #  FILTRO DE DISPOSITIVOS
    if device_ids:
        query = query.where(Measurement.device_id.in_(device_ids))
        
    query = query.order_by(Measurement.created_at.desc()).offset(skip).limit(limit)
    
    measurements = session.exec(query).all()
    return measurements

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Canal de comunicação em tempo real.
    O cliente conecta e fica 'preso' neste loop aguardando mensagens.
    """
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"Erro inesperado no Socket: {e}")
        manager.disconnect(websocket)