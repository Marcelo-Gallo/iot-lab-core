from typing import Optional
from sqlmodel import SQLModel

# Base comum
class UserBase(SQLModel):
    username: str # Email ou Login
    email: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False
    full_name: Optional[str] = None
    organization_id: Optional[int] = None

# Para receber no POST (com senha)
class UserCreate(UserBase):
    password: str 

# Para receber no PUT/PATCH
class UserUpdate(SQLModel):
    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    organization_id: Optional[int] = None

# Para devolver na API (sem senha)
class UserRead(UserBase):
    id: int