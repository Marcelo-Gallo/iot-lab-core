from pydantic import BaseModel
from typing import Optional, List

# O que o usuário PRECISAR enviar para criar
class DeviceCreate(BaseModel):
    name: str
    slug: str
    location: Optional[str] = None
    description: Optional[str] = None

# O que a API devolve para o usuário (Sem segredos internos, se houvesse)
class DevicePublic(DeviceCreate):
    id: int
    is_active: bool

class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class DeviceSensorsUpdate(BaseModel):
    sensor_ids: List[int]