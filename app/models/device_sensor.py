from sqlmodel import SQLModel, Field
from typing import Optional

class DeviceSensorLink(SQLModel, table=True):
    __tablename__ = "device_sensor_links"

    device_id: Optional[int] = Field(
        default=None, foreign_key="devices.id", primary_key=True
    )
    sensor_type_id: Optional[int] = Field(
        default=None, foreign_key="sensor_types.id", primary_key=True
    )
    
    calibration_formula: Optional[str] = Field(default=None)