from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class MeasurementPayload(BaseModel):
    sensor_type_id: int
    value: float
    timestamp: Optional[datetime] = None 

class MeasurementCreate(MeasurementPayload):
    device_id: int

class MeasurementPublic(MeasurementCreate):
    id: int
    created_at: datetime

class MeasurementAnalytics(BaseModel):
    bucket: datetime
    sensor_type_id: int
    avg_value: float
    min_value: float
    max_value: float
    count: int