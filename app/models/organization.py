from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.device import Device

class OrganizationBase(SQLModel):
    name: str = Field(index=True, unique=True)
    description: Optional[str] = None

class Organization(OrganizationBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    slug: str = Field(index=True, unique=True) # Ex: 'escola-infantil-01' para URLs amigáveis
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    users: List["User"] = Relationship(back_populates="organization")
    devices: List["Device"] = Relationship(back_populates="organization")