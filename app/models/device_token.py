from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime
import secrets

if TYPE_CHECKING:
    from app.models.device import Device

class DeviceToken(SQLModel, table=True):
    __tablename__ = "device_tokens"

    id: Optional[int] = Field(default=None, primary_key=True)
    
    # A FK aponta para "devices.id", que agora existe corretamente no modelo Device
    device_id: int = Field(foreign_key="devices.id", index=True)
    
    token: str = Field(index=True, unique=True)
    label: Optional[str] = None
    
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_used_at: Optional[datetime] = None
    is_rotating: bool = Field(default=False)

    # <--- CORREÇÃO CRÍTICA: O lado "filho" do relacionamento
    device: "Device" = Relationship(back_populates="tokens")

    @staticmethod
    def generate_token(prefix: str = "sk_iot_") -> str:
        """Gera um token seguro URL-safe (ex: sk_iot_Xy9...)"""
        return f"{prefix}{secrets.token_urlsafe(32)}"