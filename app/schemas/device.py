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
    is_battery_powered: bool = False

# O que a API devolve para o usuário (Sem segredos internos, se houvesse)
class DevicePublic(DeviceCreate):
    id: int
    is_active: bool
    sensors: List[SensorTypePublic] = []
    organization_id: Optional[int] = None

class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    is_battery_powered: Optional[bool] = None

class DeviceSensorsUpdate(BaseModel):
    sensor_ids: List[int]

class DeviceSensorCalibration(BaseModel):
    calibration_formula: Optional[str] = None