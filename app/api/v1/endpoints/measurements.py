from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from app.core.socket import manager
from sqlmodel import Session, select
from typing import List, Optional, Literal
from datetime import datetime, timedelta
from sqlalchemy import func, asc

from app.core.database import get_session
from app.models.measurement import Measurement
from app.schemas.measurement import MeasurementCreate, MeasurementPublic, MeasurementAnalytics

router = APIRouter()

@router.post("/", response_model=MeasurementPublic)
async def create_measurement(
    measurement_in: MeasurementCreate, 
    session: Session = Depends(get_session)
):
    """
    Registra uma nova leitura de sensor e notifica via WebSocket.
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
        "created_at": db_measurement.created_at.isoformat()
    }
    
    await manager.broadcast(payload)

    return db_measurement

@router.get("/", response_model=list[MeasurementPublic])
def read_measurements(
    session: Session = Depends(get_session),
    skip: int = 0,
    limit: int = 100,
    start_date: Optional[datetime] = None, 
    end_date: Optional[datetime] = None   
):
    """
    Lista medições com filtros opcionais de data.
    """
    query = select(Measurement)
    
    if start_date:
        query = query.where(Measurement.created_at >= start_date)
    
    if end_date:
        query = query.where(Measurement.created_at <= end_date)
        
    query = query.order_by(Measurement.created_at.desc()).offset(skip).limit(limit)
    
    measurements = session.exec(query).all()
    return measurements

@router.get("/analytics/", response_model=List[MeasurementAnalytics])
def get_analytics(
    session: Session = Depends(get_session),
    period: Literal['1h', '1d', '1w', '1m'] = '1d',
    bucket_size: Literal['minute', 'hour', 'day'] = 'hour'
):
    """
    Endpoint analítico com agregação temporal (Downsampling).
    Retorna Média/Min/Max agrupados por bucket de tempo.
    """
    try:
        # Janela de Tempo
        now = datetime.utcnow()
        if period == '1h':
            start_date = now - timedelta(hours=1)
        elif period == '1d':
            start_date = now - timedelta(days=1)
        elif period == '1w':
            start_date = now - timedelta(weeks=1)
        elif period == '1m':
            start_date = now - timedelta(days=30)
        else:
            start_date = now - timedelta(days=1)

        # Expressão de Agregação (Reutilizável)
        # Cria a expressão SQL: date_trunc('hour', created_at)
        bucket_expression = func.date_trunc(bucket_size, Measurement.created_at).label("bucket")

        # Query Otimizada
        query = (
            select(
                bucket_expression,
                Measurement.sensor_type_id,
                func.avg(Measurement.value).label("avg_value"),
                func.min(Measurement.value).label("min_value"),
                func.max(Measurement.value).label("max_value"),
                func.count(Measurement.id).label("count")
            )
            .where(Measurement.created_at >= start_date)
            .group_by(
                bucket_expression,          # Agrupa pelo objeto de expressão
                Measurement.sensor_type_id
            )
            .order_by(asc(bucket_expression)) # Ordena pelo objeto de expressão
        )

        results = session.exec(query).all()
        
        # Serialização manual (Row -> Pydantic)
        analytics_data = []
        for row in results:
            analytics_data.append(MeasurementAnalytics(
                bucket=row[0], 
                sensor_type_id=row[1],
                avg_value=round(float(row[2]), 2) if row[2] is not None else 0.0,
                min_value=float(row[3]) if row[3] is not None else 0.0,
                max_value=float(row[4]) if row[4] is not None else 0.0,
                count=int(row[5])
            ))
            
        return analytics_data

    except Exception as e:
        print(f"❌ ERRO CRÍTICO NO ANALYTICS: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao processar análise de dados.")

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"Erro Socket: {e}")
        manager.disconnect(websocket)