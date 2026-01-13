from sqlmodel import SQLModel, Field
from typing import Optional

class SensorType(SQLModel, table=True):
    __tablename__ = "sensor_types"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)  # Ex: "Temperatura", "Umidade"
    unit: str  # Ex: "°C", "%", "PPM"
    description: Optional[str] = None