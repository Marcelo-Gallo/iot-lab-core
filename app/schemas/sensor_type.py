from pydantic import BaseModel
from typing import Optional

# O que o usuário manda para criar
class SensorTypeCreate(BaseModel):
    name: str   # Ex: "Temperatura"
    unit: str   # Ex: "°C"
    description: Optional[str] = None

# O que a API devolve
class SensorTypePublic(SensorTypeCreate):
    id: int
    is_active: bool

class SensorTypeUpdate(BaseModel):
    name: Optional[str] = None
    unit: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None