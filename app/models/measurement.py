from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class Measurement(SQLModel, table=True):
    __tablename__ = "measurements"

    id: Optional[int] = Field(default=None, primary_key=True)
    
    # RELACIONAMENTOS (Foreign Keys)
    device_id: int = Field(foreign_key="devices.id")
    sensor_type_id: int = Field(foreign_key="sensor_types.id")
    
    value: float # Dados
    created_at: datetime = Field(default_factory=datetime.utcnow)