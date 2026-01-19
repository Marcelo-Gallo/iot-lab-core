from pydantic import BaseModel
from typing import Optional, List
from app.schemas.sensor_type import SensorTypePublic

# O que o usuário PRECISAR enviar para criar
class DeviceCreate(BaseModel):
    name: str
    slug: str
    location: Optional[str] = None
    description: Optional[str] = None
    sensor_ids: Optional[List[int]] = []

# O que a API devolve para o usuário (Sem segredos internos, se houvesse)
class DevicePublic(DeviceCreate):
    id: int
    is_active: bool
    sensors: List[SensorTypePublic] = []

class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class DeviceSensorsUpdate(BaseModel):
    sensor_ids: List[int]