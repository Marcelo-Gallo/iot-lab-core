from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime

from app.models.device_sensor import DeviceSensorLink

if TYPE_CHECKING:
    from app.models.device import Device

class SensorType(SQLModel, table=True):
    __tablename__ = "sensor_types"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    unit: str
    description: Optional[str] = None
    is_active: bool = Field(default=True)
    deleted_at: Optional[datetime] = Field(default=None)

    devices: List["Device"] = Relationship(
        back_populates="sensors", 
        link_model=DeviceSensorLink
    )