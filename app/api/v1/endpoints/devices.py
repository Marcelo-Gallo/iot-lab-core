from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.core.database import get_session
from app.models.device import Device
from app.schemas.device import DeviceCreate, DevicePublic
from app.schemas.device import DeviceCreate, DevicePublic, DeviceUpdate
from datetime import datetime

router = APIRouter()

@router.get("/", response_model=List[DevicePublic])
def read_devices(
    skip: int = 0, 
    limit: int = 100, 
    session: Session = Depends(get_session)
):
    """
    Lista todos os dispositivos cadastrados.
    """
    query = select(Device).offset(skip).limit(limit)
    devices = session.exec(query).all()
    return devices

@router.post("/", response_model=DevicePublic)
def create_device(device_in: DeviceCreate, session: Session = Depends(get_session)):
    """
    Cadastra um novo dispositivo.
    """
    # 1. Validação de Negócio: O slug já existe?
    # Query: SELECT * FROM devices WHERE slug = 'valor'
    query = select(Device).where(Device.slug == device_in.slug)
    existing_device = session.exec(query).first()
    
    if existing_device:
        raise HTTPException(status_code=400, detail="Já existe um dispositivo com este slug.")

    # 2. Transforma o Schema (Pydantic) em Model (Banco)
    # O .model_dump() pega os campos do JSON e joga na classe Device
    db_device = Device.model_validate(device_in)
    
    # 3. Grava no Banco
    session.add(db_device)
    session.commit()      # Efetiva a gravação
    session.refresh(db_device) # Atualiza o objeto com o ID gerado pelo banco
    
    return db_device

# --- 1. ALTERAR O GET EXISTENTE ---
@router.get("/", response_model=List[DevicePublic])
def read_devices(
    skip: int = 0, 
    limit: int = 100, 
    session: Session = Depends(get_session)
):
    # Só trazemos quem NÃO tem data de deleção
    query = select(Device).where(Device.deleted_at == None).offset(skip).limit(limit)
    devices = session.exec(query).all()
    return devices

# --- 2. NOVO ENDPOINT: UPDATE (PATCH) ---
@router.patch("/{device_id}", response_model=DevicePublic)
def update_device(
    device_id: int, 
    device_update: DeviceUpdate, 
    session: Session = Depends(get_session)
):
    # Busca o dispositivo (e garante que não está deletado)
    db_device = session.get(Device, device_id)
    if not db_device or db_device.deleted_at:
        raise HTTPException(status_code=404, detail="Dispositivo não encontrado")

    # Mágica do Pydantic: Pega só os dados que o usuário enviou (exclui os nulos)
    update_data = device_update.model_dump(exclude_unset=True)
    
    # Atualiza o objeto do banco
    for key, value in update_data.items():
        setattr(db_device, key, value)

    session.add(db_device)
    session.commit()
    session.refresh(db_device)
    return db_device

# --- 3. NOVO ENDPOINT: SOFT DELETE ---
@router.delete("/{device_id}")
def delete_device(device_id: int, session: Session = Depends(get_session)):
    db_device = session.get(Device, device_id)
    if not db_device or db_device.deleted_at:
        raise HTTPException(status_code=404, detail="Dispositivo não encontrado")

    db_device.deleted_at = datetime.utcnow()
    db_device.is_active = False # Boa prática desativar também
    
    session.add(db_device)
    session.commit()
    
    return {"ok": True, "message": "Dispositivo arquivado com sucesso"}