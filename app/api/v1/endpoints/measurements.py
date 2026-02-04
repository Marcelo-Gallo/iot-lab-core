from typing import List, Optional, Literal
from datetime import datetime, timedelta

from fastapi import (
    APIRouter, 
    Depends, 
    HTTPException, 
    WebSocket, 
    WebSocketDisconnect, 
    Query, 
    status
)
from sqlalchemy import func, asc
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from jose import jwt, JWTError

# --- Core Imports ---
from app.core.socket import manager
from app.core.database import get_session
from app.core.calibration import safe_eval
from app.core.config import settings  # Necessário para decodificar o JWT

# --- Model Imports ---
from app.models.measurement import Measurement
from app.models.device import Device
from app.models.device_sensor import DeviceSensorLink
from app.models.user import User

# --- Schema Imports ---
from app.schemas.measurement import MeasurementPublic, MeasurementAnalytics, MeasurementPayload

# --- Dependencies ---
from app.api.v1 import deps

router = APIRouter()

# -----------------------------------------------------------------------------
# HELPERS (WebSocket Auth)
# -----------------------------------------------------------------------------
async def get_current_user_ws(token: str = Query(...)) -> int:
    """
    Dependência exclusiva para WebSocket.
    Valida o token JWT passado na URL e retorna o organization_id.
    Se inválido, rejeita a conexão com código de violação de política (1008).
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        organization_id: Optional[int] = payload.get("organization_id")
        
        if organization_id is None:
            print("❌ WS Auth Failed: No organization_id in token")
            raise WebSocketDisconnect(code=status.WS_1008_POLICY_VIOLATION)
            
        return int(organization_id)
        
    except (JWTError, ValueError) as e:
        print(f"❌ WS Auth Error: {e}")
        raise WebSocketDisconnect(code=status.WS_1008_POLICY_VIOLATION)

# -----------------------------------------------------------------------------
# INGESTÃO DE DADOS (Máquina -> Servidor)
# -----------------------------------------------------------------------------
@router.post("/", response_model=MeasurementPublic)
async def create_measurement(
    payload: MeasurementPayload,
    session: AsyncSession = Depends(get_session),
    device: Device = Depends(deps.get_current_device)  # Valida Token do Device
):
    """
    Registra uma nova medição e dispara evento Realtime isolado.
    Autenticação: Via X-Device-Token.
    """
    
    # 1. Validação de Vínculo Sensor-Dispositivo
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

    # 5. Realtime Broadcast com ISOLAMENTO VERTICAL
    # Envia apenas para sockets conectados na mesma organização do dispositivo
    await manager.broadcast(
        message={
            "id": db_measurement.id,
            "device_id": db_measurement.device_id,
            "sensor_type_id": db_measurement.sensor_type_id,
            "value": db_measurement.value,
            "created_at": db_measurement.created_at.isoformat(),
            "organization_id": device.organization_id 
        },
        organization_id=device.organization_id  # <--- CHAVE DA SEGURANÇA
    )
    
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
    current_user: User = Depends(deps.get_current_active_user)
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
    current_user: User = Depends(deps.get_current_active_user)
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
            .join(Device, Measurement.device_id == Device.id)
            .where(Device.organization_id == current_user.organization_id)
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
        print(f"❌ ERRO CRÍTICO NO ANALYTICS: {e}")
        raise HTTPException(status_code=500, detail="Erro interno no processamento de dados.")

# -----------------------------------------------------------------------------
# WEBSOCKET (Realtime Secure)
# -----------------------------------------------------------------------------
@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    organization_id: int = Depends(get_current_user_ws)
):
    """
    Endpoint WebSocket Autenticado e Isolado.
    Requer token JWT na query string: ws://host/api/v1/measurements/ws?token=<access_token>
    """
    await manager.connect(websocket, organization_id)
    try:
        while True:
            # Mantém a conexão ativa.
            # Como é push-notification (Server -> Client), não processamos input aqui.
            await websocket.receive_text()
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, organization_id)