from typing import Optional
from datetime import datetime, timezone, timedelta
from sqlmodel import Field, SQLModel, Relationship

class DeviceBase(SQLModel):
    name: str
    slug: str = Field(index=True, unique=True)
    location: Optional[str] = None
    is_active: bool = Field(default=True)

    heartbeat_interval: int = Field(default=300, description="Tempo máximo em segundos sem dados antes de considerar OFFLINE")

class Device(DeviceBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    deleted_at: Optional[datetime] = Field(default=None)
    
    last_seen: Optional[datetime] = Field(default=None)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relacionamentos
    tokens: list["DeviceToken"] = Relationship(back_populates="device")
    sensors: list["DeviceSensor"] = Relationship(back_populates="device")
    measurements: list["Measurement"] = Relationship(back_populates="device")

    @property
    def current_status(self) -> str:
        """
        Retorna o estado real do dispositivo baseado em regras de negócio.
        """

        if self.deleted_at is not None:
            return "ARCHIVED" # Na lixeira
            
        if not self.is_active:
            return "DISABLED" # Desligado pelo Admin
            
        if self.last_seen:
            now = datetime.now(timezone.utc)
            last_seen_aware = self.last_seen.replace(tzinfo=timezone.utc) if self.last_seen.tzinfo is None else self.last_seen
            
            delta = now - last_seen_aware
            
            if delta.total_seconds() > self.heartbeat_interval:
                return "OFFLINE"
            return "ONLINE"
            
        return "NEVER_SEEN"