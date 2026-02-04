from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select, delete
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone

from app.core.database import get_session
from app.models.device import Device
from app.models.user import User
from app.models.device_token import DeviceToken
from app.models.device_sensor import DeviceSensorLink
from app.models.sensor_type import SensorType

from app.schemas.device import DeviceCreate, DevicePublic, DeviceUpdate, DeviceSensorCalibration
from app.schemas.device_token import DeviceTokenCreate, DeviceTokenPublic
from app.schemas.device_sensor import DeviceSensorLinkCreate

from app.api.v1 import deps

router = APIRouter()

# --- HELPER FUNCTION: TENANT SECURITY ---
def verify_device_ownership(device: Device, user: User):
    """
    Garante que o usuário só acesse dispositivos da sua organização.
    Levanta 404 se o dispositivo for de outra org (Security by Obscurity).
    """
    if device.organization_id != user.organization_id:
        raise HTTPException(status_code=404, detail="Dispositivo não encontrado")

# -----------------------------------------------------------------------------
# CRUD BÁSICO
# -----------------------------------------------------------------------------

@router.post("/", response_model=DevicePublic)
async def create_device(
    device: DeviceCreate, 
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(deps.get_current_active_user) # Alterado para User comum
):
    if not current_user.organization_id:
        raise HTTPException(status_code=400, detail="Usuário sem organização vinculada.")

    # Verifica duplicidade de Slug GLOBALMENTE ou por ORG?
    # Idealmente por ORG, mas mantemos global por enquanto para simplificar URLs
    query = select(Device).where(Device.slug == device.slug)
    result = await session.exec(query)
    if result.first():
        raise HTTPException(status_code=400, detail="Já existe um dispositivo com este slug.")

    # Criação do objeto com vinculo à Organização
    device_data = device.model_dump(exclude={"sensor_ids"})
    db_device = Device(**device_data)
    db_device.organization_id = current_user.organization_id # <--- TENANT BINDING
    
    session.add(db_device)
    await session.commit()
    await session.refresh(db_device)
    
    # Processa sensores iniciais
    if device.sensor_ids:
        for s_id in device.sensor_ids:
            link = DeviceSensorLink(device_id=db_device.id, sensor_type_id=s_id)
            session.add(link)
        await session.commit()

    # Recarrega com relacionamentos
    query_refresh = (
        select(Device)
        .where(Device.id == db_device.id)
        .options(selectinload(Device.sensors))
    )
    result = await session.exec(query_refresh)
    return result.one()

@router.get("/", response_model=List[Device])
async def read_devices(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(deps.get_current_active_user),
):
    # TENANT FILTER: Traz apenas devices da org do usuário
    query = (
        select(Device)
        .where(Device.organization_id == current_user.organization_id)
        .order_by(Device.id.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await session.exec(query)
    return result.all()

@router.get("/{device_id}", response_model=DevicePublic)
async def read_device(
    device_id: int, 
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(deps.get_current_active_user),
):
    query = (
        select(Device)
        .where(Device.id == device_id)
        .options(selectinload(Device.sensors)) 
    )
    result = await session.exec(query)
    db_device = result.first()

    if not db_device:
        raise HTTPException(status_code=404, detail="Dispositivo não encontrado")
    
    verify_device_ownership(db_device, current_user) # <--- SECURITY CHECK
    
    return db_device

@router.patch("/{device_id}", response_model=DevicePublic)
async def update_device(
    device_id: int, 
    device_in: DeviceUpdate, 
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(deps.get_current_active_user)
):
    db_device = await session.get(Device, device_id)
    if not db_device:
        raise HTTPException(status_code=404, detail="Dispositivo não encontrado")
    
    verify_device_ownership(db_device, current_user) # <--- SECURITY CHECK
    
    device_data = device_in.model_dump(exclude_unset=True)
    
    # Impede mudança de dono
    if "organization_id" in device_data:
        del device_data["organization_id"]

    for key, value in device_data.items():
        setattr(db_device, key, value)
        
    session.add(db_device)
    await session.commit()
    await session.refresh(db_device)
    return db_device

@router.delete("/{device_id}")
async def delete_device(
    device_id: int, 
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(deps.get_current_active_user)
):
    db_device = await session.get(Device, device_id)
    if not db_device:
        raise HTTPException(status_code=404, detail="Dispositivo não encontrado")
    
    verify_device_ownership(db_device, current_user) # <--- SECURITY CHECK
    
    db_device.deleted_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db_device.is_active = False
    
    session.add(db_device)
    await session.commit()
    return {"ok": True}

@router.post("/{device_id}/restore")
async def restore_device(
    device_id: int, 
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(deps.get_current_active_user)
):
    db_device = await session.get(Device, device_id)
    if not db_device:
        raise HTTPException(status_code=404, detail="Dispositivo não encontrado")
    
    verify_device_ownership(db_device, current_user) # <--- SECURITY CHECK
    
    db_device.deleted_at = None
    db_device.is_active = True
    
    session.add(db_device)
    await session.commit()
    return {"ok": True}

# -----------------------------------------------------------------------------
# GESTÃO DE SENSORES E TOKENS (Mantidos e Protegidos)
# -----------------------------------------------------------------------------

@router.get("/{device_id}/sensors", response_model=List[int])
async def get_device_sensors(
    device_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(deps.get_current_active_user) # Adicionado Auth
):
    # Precisamos validar o device antes de buscar sensores
    device = await session.get(Device, device_id)
    if not device:
         raise HTTPException(status_code=404, detail="Dispositivo não encontrado")
    verify_device_ownership(device, current_user)

    query = select(DeviceSensorLink.sensor_type_id).where(DeviceSensorLink.device_id == device_id)
    result = await session.exec(query)
    return result.all()

@router.post("/{device_id}/tokens", response_model=DeviceTokenPublic)
async def create_device_token(
    device_id: int,
    token_in: DeviceTokenCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(deps.get_current_active_user)
):
    device = await session.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Dispositivo não encontrado")
    verify_device_ownership(device, current_user) # <--- SECURITY CHECK

    raw_token = DeviceToken.generate_token()

    db_token = DeviceToken(
        device_id=device_id,
        token=raw_token,
        label=token_in.label
    )

    session.add(db_token)
    await session.commit()
    await session.refresh(db_token)

    return db_token

@router.get("/{device_id}/tokens", response_model=List[DeviceTokenPublic])
async def list_device_tokens(
    device_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(deps.get_current_active_user)
):
    device = await session.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Dispositivo não encontrado")
    verify_device_ownership(device, current_user) # <--- SECURITY CHECK

    query = select(DeviceToken).where(DeviceToken.device_id == device_id)
    result = await session.exec(query)
    return result.all()

@router.put("/{device_id}/sensors/{sensor_id}/calibration", response_model=dict)
async def update_sensor_calibration(
    device_id: int,
    sensor_id: int,
    payload: DeviceSensorCalibration,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(deps.get_current_active_user)
):
    # Valida Device Primeiro
    device = await session.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Dispositivo não encontrado")
    verify_device_ownership(device, current_user) # <--- SECURITY CHECK

    link = await session.get(DeviceSensorLink, (device_id, sensor_id))
    if not link:
        raise HTTPException(status_code=404, detail="Sensor não vinculado.")

    link.calibration_formula = payload.calibration_formula
    session.add(link)
    await session.commit()
    
    return {"status": "ok", "formula": link.calibration_formula}

@router.get("/{device_id}/sensors/{sensor_id}/calibration", response_model=dict)
async def get_sensor_calibration(
    device_id: int,
    sensor_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(deps.get_current_active_user) # Adicionado Auth
):
    device = await session.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Dispositivo não encontrado")
    verify_device_ownership(device, current_user)

    link = await session.get(DeviceSensorLink, (device_id, sensor_id))
    if not link:
        raise HTTPException(status_code=404, detail="Link não encontrado")
    return {"formula": link.calibration_formula}

@router.post("/{device_id}/sensors")
async def update_device_sensors(
    device_id: int,
    sensor_links: List[DeviceSensorLinkCreate], 
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(deps.get_current_active_user),
):
    device = await session.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Dispositivo não encontrado")
    verify_device_ownership(device, current_user) # <--- SECURITY CHECK

    # Limpeza e Recriação (Mantida lógica original)
    stmt = delete(DeviceSensorLink).where(DeviceSensorLink.device_id == device_id)
    await session.exec(stmt)
    
    for link_in in sensor_links:
        db_link = DeviceSensorLink(
            device_id=device_id,
            sensor_type_id=link_in.sensor_type_id,
            calibration_formula=link_in.calibration_formula
        )
        session.add(db_link)
    
    await session.commit()
    return {"ok": True}