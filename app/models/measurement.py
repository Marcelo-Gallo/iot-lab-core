from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime

# Importação condicional para evitar ciclo (Circular Import)
if TYPE_CHECKING:
    from app.models.device import Device
    from app.models.sensor_type import SensorType

class Measurement(SQLModel, table=True):
    __tablename__ = "measurements"

    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Foreign Keys (Banco de Dados)
    device_id: int = Field(foreign_key="devices.id")
    sensor_type_id: int = Field(foreign_key="sensor_types.id")
    
    value: float 
    created_at: datetime = Field(default_factory=datetime.utcnow)

    device: "Device" = Relationship(back_populates="measurements")
    
    sensor_type: "SensorType" = Relationship()