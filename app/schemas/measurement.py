from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# O que o sensor envia (Payload)
class MeasurementCreate(BaseModel):
    device_id: int
    sensor_type_id: int
    value: float

# O que a API responde (inclui ID e Data)
class MeasurementPublic(MeasurementCreate):
    id: int
    created_at: datetime