from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

from app.models.device_sensor import DeviceSensorLink

if TYPE_CHECKING:
    from app.models.sensor_type import SensorType

class Device(SQLModel, table=True):
    __tablename__ = "devices"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    slug: str = Field(unique=True, index=True)
    location: Optional[str] = None
    description: Optional[str] = None
    is_active: bool = Field(default=True)
    deleted_at: Optional[datetime] = Field(default=None)
    is_battery_powered: bool = Field(default = False)

    sensors: List["SensorType"] = Relationship(
        back_populates="devices", 
        link_model=DeviceSensorLink 
    )