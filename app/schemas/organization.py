from typing import Optional
from pydantic import BaseModel
from datetime import datetime

# Propriedades compartilhadas
class OrganizationBase(BaseModel):
    name: str
    description: Optional[str] = None
    slug: str # Obrigatório para URL única

# Propriedades para criação
class OrganizationCreate(OrganizationBase):
    pass

# Propriedades para atualização
class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    slug: Optional[str] = None

# Propriedades para leitura (API Response)
class OrganizationRead(OrganizationBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True