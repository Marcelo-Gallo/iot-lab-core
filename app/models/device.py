from typing import Optional, List, TYPE_CHECKING
from datetime import datetime, timezone
from sqlmodel import Field, SQLModel, Relationship

# Imports condicionais
if TYPE_CHECKING:
    from app.models.device_token import DeviceToken
    from app.models.measurement import Measurement
    from app.models.sensor_type import SensorType

from app.models.device_sensor import DeviceSensorLink

class DeviceBase(SQLModel):
    name: str
    slug: str = Field(index=True, unique=True)
    location: Optional[str] = None
    description: Optional[str] = None  # <--- Mantido
    
    is_active: bool = Field(default=True)
    is_battery_powered: bool = Field(default=False) # <--- Mantido (útil para lógica de sleep)
    
    heartbeat_interval: int = Field(default=300, description="Tempo máximo em segundos sem dados antes de considerar OFFLINE")

class Device(DeviceBase, table=True):
    __tablename__ = "devices" 

    id: Optional[int] = Field(default=None, primary_key=True)
    
    deleted_at: Optional[datetime] = Field(default=None)
    last_seen: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relacionamentos
    tokens: List["DeviceToken"] = Relationship(back_populates="device")
    
    sensors: List["SensorType"] = Relationship(
        back_populates="devices", 
        link_model=DeviceSensorLink
    )
    
    measurements: List["Measurement"] = Relationship(back_populates="device")

    @property
    def current_status(self) -> str:
        """Retorna o estado real do dispositivo baseado em regras de negócio."""
        if self.deleted_at is not None:
            return "ARCHIVED"
            
        if not self.is_active:
            return "DISABLED"
            
        if self.last_seen:
            now = datetime.now(timezone.utc)
            last_seen_aware = self.last_seen
            if self.last_seen.tzinfo is None:
                last_seen_aware = self.last_seen.replace(tzinfo=timezone.utc)
            
            # Lógica Especial: Se for bateria, tolerância maior? (Exemplo futuro)
            # tolerance = self.heartbeat_interval * (2 if self.is_battery_powered else 1)
            
            delta = now - last_seen_aware
            if delta.total_seconds() > self.heartbeat_interval:
                return "OFFLINE"
            return "ONLINE"
            
        return "NEVER_SEEN"