from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List, Optional, Literal
from datetime import datetime, timedelta
from sqlalchemy import func, asc

from app.core.socket import manager
from app.core.database import get_session
from app.core.calibration import safe_eval

from app.models.measurement import Measurement
from app.models.device import Device
from app.models.device_sensor import DeviceSensorLink
from app.models.user import User  # <--- Necessário para Auth

from app.schemas.measurement import MeasurementPublic, MeasurementAnalytics, MeasurementPayload
from app.api.v1 import deps

router = APIRouter()

# -----------------------------------------------------------------------------
# INGESTÃO DE DADOS (Máquina -> Servidor)
# -----------------------------------------------------------------------------
@router.post("/", response_model=MeasurementPublic)
async def create_measurement(
    payload: MeasurementPayload,
    session: AsyncSession = Depends(get_session),
    device: Device = Depends(deps.get_current_device) # Valida Token do Device
):
    """
    Registra uma nova medição.
    Autenticação: Via X-Device-Token (Machine-to-Machine).
    """
    
    # 1. Correção do Bug: Extrair IDs válidos dos sensores do dispositivo
    # Assumindo que get_current_device já faz o 'selectinload(Device.sensors)'
    valid_sensor_ids = [sensor.id for sensor in device.sensors]

    if payload.sensor_type_id not in valid_sensor_ids:
         raise HTTPException(
             status_code=400, 
             detail=f"Sensor {payload.sensor_type_id} não está vinculado a este dispositivo."
         )
    
    # 2. Busca Link para Calibração
    query_link = select(DeviceSensorLink).where(
        DeviceSensorLink.device_id == device.id,
        DeviceSensorLink.sensor_type_id == payload.sensor_type_id
    )
    link_result = await session.exec(query_link)
    link = link_result.first()

    # 3. Aplica Fórmula (Edge Computing no Server)
    final_value = payload.value
    if link and link.calibration_formula:
        final_value = safe_eval(link.calibration_formula, payload.value)
    
    # 4. Persistência
    db_measurement = Measurement(
        device_id=device.id, 
        sensor_type_id=payload.sensor_type_id,
        value=final_value,
        created_at=payload.timestamp if payload.timestamp else datetime.utcnow()
    )
    
    session.add(db_measurement)
    await session.commit()
    await session.refresh(db_measurement)

    # 5. Realtime Broadcast
    # TODO Futuro: O WebSocket também precisará ser segmentado por Salas/Organização
    await manager.broadcast({
        "id": db_measurement.id,
        "device_id": db_measurement.device_id,
        "sensor_type_id": db_measurement.sensor_type_id,
        "value": db_measurement.value,
        "created_at": db_measurement.created_at.isoformat(),
        # Enviamos o OrgID para o frontend filtrar (Solução temporária)
        "organization_id": device.organization_id 
    })
    
    return db_measurement

# -----------------------------------------------------------------------------
# LEITURA DE DADOS (Humano -> Servidor)
# -----------------------------------------------------------------------------

@router.get("/", response_model=List[MeasurementPublic])
async def read_measurements(
    session: AsyncSession = Depends(get_session),
    skip: int = 0,
    limit: int = 100,
    start_date: Optional[datetime] = None, 
    end_date: Optional[datetime] = None,
    device_id: Optional[int] = None,
    current_user: User = Depends(deps.get_current_active_user) # <--- BLINDAGEM
):
    """
    Lista medições históricas.
    SECURITY: Filtra rigorosamente pela Organização do usuário.
    """
    # TENANT ISOLATION: Join com Device para filtrar por Organization
    query = select(Measurement).join(Device)
    query = query.where(Device.organization_id == current_user.organization_id)
    
    # Filtros opcionais
    if device_id:
        query = query.where(Measurement.device_id == device_id)
        
    if start_date: 
        query = query.where(Measurement.created_at >= start_date)
    if end_date: 
        query = query.where(Measurement.created_at <= end_date)
        
    query = query.order_by(Measurement.created_at.desc()).offset(skip).limit(limit)
    
    result = await session.exec(query)
    return result.all()

@router.get("/analytics/", response_model=List[MeasurementAnalytics])
async def get_analytics(
    session: AsyncSession = Depends(get_session),
    period: Literal['1h', '1d', '1w', '1m'] = '1d',
    bucket_size: Literal['minute', 'hour', 'day'] = 'hour',
    current_user: User = Depends(deps.get_current_active_user) # <--- BLINDAGEM
):
    """
    Retorna dados agregados (Média, Min, Max).
    SECURITY: Agrega apenas dados da Organização do usuário.
    """
    try:
        now = datetime.utcnow()
        if period == '1h': start_date = now - timedelta(hours=1)
        elif period == '1d': start_date = now - timedelta(days=1)
        elif period == '1w': start_date = now - timedelta(weeks=1)
        elif period == '1m': start_date = now - timedelta(days=30)
        else: start_date = now - timedelta(days=1)

        bucket_expression = func.date_trunc(bucket_size, Measurement.created_at).label("bucket")

        # Query Complexa com Join de Segurança
        query = (
            select(
                bucket_expression,
                Measurement.sensor_type_id,
                func.avg(Measurement.value).label("avg_value"),
                func.min(Measurement.value).label("min_value"),
                func.max(Measurement.value).label("max_value"),
                func.count(Measurement.id).label("count")
            )
            .join(Device, Measurement.device_id == Device.id) # <--- Join Explicito
            .where(Device.organization_id == current_user.organization_id) # <--- Filtro Tenant
            .where(Measurement.created_at >= start_date)
            .group_by(bucket_expression, Measurement.sensor_type_id)
            .order_by(asc(bucket_expression))
        )

        result = await session.exec(query)
        results = result.all()
        
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
        print(f"ERRO CRÍTICO NO ANALYTICS: {e}")
        raise HTTPException(status_code=500, detail="Erro interno no processamento de dados.")

# -----------------------------------------------------------------------------
# WEBSOCKET (Realtime)
# -----------------------------------------------------------------------------
# ALERTA DE ARQUITETO:
# O WebSocket atual não tem autenticação. Qualquer um pode conectar.
# Em produção, devemos passar o token na query string da conexão WS (ws://...?token=xyz)
# e validar a organização antes de aceitar a conexão.
# Por enquanto, mantemos funcional, mas ciente do risco.

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)