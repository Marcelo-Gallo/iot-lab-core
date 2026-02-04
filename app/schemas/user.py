from typing import Optional
from sqlmodel import SQLModel

class UserBase(SQLModel):
    username: str
    email: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False
    full_name: Optional[str] = None

class UserRead(UserBase):
    id: int