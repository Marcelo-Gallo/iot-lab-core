from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from app.core.database import get_session
from app.models.device import Device
from app.schemas.device import DeviceCreate, DevicePublic, DeviceUpdate
from datetime import datetime

router = APIRouter()

# --- 1. LISTAR DISPOSITIVOS (CORRIGIDO) ---
@router.get("/", response_model=List[DevicePublic])
def read_devices(
    skip: int = 0, 
    limit: int = 100, 
    active_only: bool = False, # Novo parâmetro opcional
    session: Session = Depends(get_session)
):
    """
    Lista dispositivos.
    Se active_only=True, traz apenas os ativos.
    Se active_only=False (padrão), traz TODOS (inclusive arquivados).
    """
    query = select(Device)
    
    if active_only:
        query = query.where(Device.deleted_at == None)
        
    query = query.offset(skip).limit(limit)
    devices = session.exec(query).all()
    return devices

@router.post("/", response_model=DevicePublic)
def create_device(device_in: DeviceCreate, session: Session = Depends(get_session)):
    """
    Cadastra um novo dispositivo.
    """
    query = select(Device).where(Device.slug == device_in.slug)
    existing_device = session.exec(query).first()
    
    if existing_device:
        raise HTTPException(status_code=400, detail="Já existe um dispositivo com este slug.")

    db_device = Device.model_validate(device_in)
    session.add(db_device)
    session.commit()
    session.refresh(db_device)
    return db_device

# --- 2. UPDATE / RESTORE (CORRIGIDO) ---
@router.patch("/{device_id}", response_model=DevicePublic)
def update_device(
    device_id: int, 
    device_update: DeviceUpdate, 
    session: Session = Depends(get_session)
):
    # REMOVIDO O FILTRO "or db_device.deleted_at"
    # Agora podemos encontrar o dispositivo mesmo se ele estiver arquivado
    db_device = session.get(Device, device_id)
    
    if not db_device:
        raise HTTPException(status_code=404, detail="Dispositivo não encontrado")

    update_data = device_update.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(db_device, key, value)

    session.add(db_device)
    session.commit()
    session.refresh(db_device)
    return db_device

# --- 3. SOFT DELETE (MANTIDO IGUAL) ---
@router.delete("/{device_id}")
def delete_device(device_id: int, session: Session = Depends(get_session)):
    db_device = session.get(Device, device_id)
    
    # Aqui mantemos a verificação, pois não faz sentido deletar o que já está deletado
    if not db_device or db_device.deleted_at:
        raise HTTPException(status_code=404, detail="Dispositivo não encontrado ou já arquivado")

    db_device.deleted_at = datetime.utcnow()
    db_device.is_active = False
    
    session.add(db_device)
    session.commit()
    
    return {"ok": True, "message": "Dispositivo arquivado com sucesso"}