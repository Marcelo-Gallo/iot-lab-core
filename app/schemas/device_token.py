from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Base: Atributos comuns
class DeviceTokenBase(BaseModel):
    label: Optional[str] = "Token Padrão"

# Input: O que o usuário envia para criar (pode ser vazio, usamos o default)
class DeviceTokenCreate(DeviceTokenBase):
    pass

# Output: O que a API responde (Aqui mostramos o token!)
class DeviceTokenPublic(DeviceTokenBase):
    id: int
    device_id: int
    token: str         
    created_at: datetime
    last_used_at: Optional[datetime] = None
    is_active: bool