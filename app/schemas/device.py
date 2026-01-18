from pydantic import BaseModel
from typing import Optional
from datetime import datetime  # <--- IMPORT NOVO

# O que o usuário PRECISAR enviar para criar
class DeviceCreate(BaseModel):
    name: str
    slug: str
    location: Optional[str] = None
    description: Optional[str] = None

# O que a API devolve para o usuário
class DevicePublic(DeviceCreate):
    id: int
    is_active: bool
    created_at: Optional[datetime] = None # É bom ter para ordenar gráficos
    deleted_at: Optional[datetime] = None # <--- CRUCIAL: O Frontend precisa ver isso!

class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    deleted_at: Optional[datetime] = None # <--- CRUCIAL: Para permitir restaurar (enviar null)