from pydantic import BaseModel, Field
from typing import Optional

class DeviceSensorLinkBase(BaseModel):
    sensor_type_id: int
    calibration_formula: Optional[str] = Field(
        default=None, 
        description="Fórmula matemática (ex: 'x * 0.5 + 10'). 'x' é o valor bruto."
    )

class DeviceSensorLinkCreate(DeviceSensorLinkBase):
    pass