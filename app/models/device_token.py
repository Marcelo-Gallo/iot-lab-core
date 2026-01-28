from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
import secrets

class DeviceToken(SQLModel, table=True):
    __tablename__ = "device_tokens"

    id: Optional[int] = Field(default=None, primary_key=True)
    device_id: int = Field(foreign_key="devices.id", index=True)
    
    token: str = Field(index=True, unique=True)
    
    label: Optional[str] = None
    
    # Controle
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_used_at: Optional[datetime] = None
    
    # Flag para o futuro (LoRa/Rotação)
    is_rotating: bool = Field(default=False)

    @staticmethod
    def generate_token(prefix: str = "sk_iot_") -> str:
        """Gera um token seguro URL-safe (ex: sk_iot_Xy9...)"""
        return f"{prefix}{secrets.token_urlsafe(32)}"